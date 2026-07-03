"""In-memory session management for TaxStox.

Design principle: Store only what's needed for the current filing session.
No financial data persisted to disk. Sessions expire after 30 minutes of inactivity.
"""

import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from src.models.form16 import Form16Data
from src.models.ais import AISData
from src.models.tax import UnifiedTaxData, UserAnswers, ClassifiedCGData, RegimeResult


@dataclass
class Session:
    """A filing session — holds all data during the ITR preparation flow."""

    session_id: str
    pan: str = ""
    dob: str = ""

    # PDF data
    form16: Optional[Form16Data] = None
    ais: Optional[AISData] = None

    # Computed
    classified_cg: Optional[ClassifiedCGData] = None
    regime_result: Optional[RegimeResult] = None
    user_answers: UserAnswers = field(default_factory=UserAnswers)
    itr_form: str = "ITR-2"  # Auto-detected ITR form type

    # Final
    itr_json: Optional[dict] = None
    status: str = "created"  # created → parsed → classified → questions_answered → built → validated

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)

    @property
    def unified_data(self) -> UnifiedTaxData:
        """Build UnifiedTaxData from session state."""
        return UnifiedTaxData(
            pan=self.pan,
            dob=None,  # Parse as date if needed
            form16=self.form16,
            ais=self.ais,
            user_answers=self.user_answers,
            capital_gains=self.classified_cg or ClassifiedCGData(),
            regime_result=self.regime_result or RegimeResult(),
            final_total_income=Decimal("0"),
            final_tax_liability=Decimal("0"),
            final_balance_payable=Decimal("0"),
        )


class SessionManager:
    """Manages filing sessions in memory."""

    def __init__(self, ttl_minutes: int = 30):
        self._sessions: dict[str, Session] = {}
        self._ttl = timedelta(minutes=ttl_minutes)

    def create(self, pan: str, dob: str) -> Session:
        """Create a new filing session."""
        session_id = str(uuid.uuid4())[:8]
        session = Session(
            session_id=session_id,
            pan=pan.strip().upper(),
            dob=dob.strip(),
        )
        self._sessions[session_id] = session
        self._cleanup_expired()
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """Get a session by ID, updating last_accessed."""
        session = self._sessions.get(session_id)
        if session is None:
            return None

        # Check expiry
        if datetime.now() - session.last_accessed > self._ttl:
            del self._sessions[session_id]
            return None

        session.last_accessed = datetime.now()
        return session

    def delete(self, session_id: str) -> None:
        """Delete a session."""
        self._sessions.pop(session_id, None)

    def _cleanup_expired(self) -> None:
        """Remove expired sessions."""
        now = datetime.now()
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.last_accessed > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]


# Global session manager instance
session_manager = SessionManager()
