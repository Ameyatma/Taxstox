"""Session management for TaxStox.

Design principle: Store only what's needed for the current filing session.
No financial data persisted to disk. Sessions expire after 30 minutes of inactivity.

Persistence is backend-pluggable (PR5.2):
- InMemorySessionBackend  — development / single-worker (default, unchanged behaviour)
- RedisSessionBackend      — production, horizontal scaling, survives restart

The legacy global `session_manager` singleton keeps the same public API
(create / get / delete), so callers in routes.py / simulation.py are unaffected.
"""

import logging
import pickle
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Protocol

from src.models.ais import AISData
from src.models.financial_year import FinancialYear
from src.models.form16 import Form16Data
from src.models.tax import ClassifiedCGData, RegimeResult, UnifiedTaxData, UserAnswers

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """A filing session — holds all data during the ITR preparation flow."""

    session_id: str
    pan: str = ""
    dob: str = ""

    # PDF data
    form16: Form16Data | None = None
    ais: AISData | None = None

    # Computed
    classified_cg: ClassifiedCGData | None = None
    regime_result: RegimeResult | None = None
    user_answers: UserAnswers = field(default_factory=UserAnswers)
    itr_form: str = "ITR-2"  # Auto-detected ITR form type
    taxpayer_data: dict | None = None  # Auto-extracted data from PDFs
    financial_year: FinancialYear | None = None  # Authoritative filing year (from Form 16 assessment year)

    # Audit (PR2) — attached dynamically by the processing pipeline
    audit_trail: list | None = None
    audit_event_count: int = 0

    # Final
    itr_json: dict | None = None
    status: str = "created"  # created → parsed → classified → questions_answered → built → validated

    # Document uploads
    documents: list = field(default_factory=list)

    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(UTC))

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
            final_total_income=Decimal(0),
            final_tax_liability=Decimal(0),
            final_balance_payable=Decimal(0),
        )


class SessionBackend(Protocol):
    """Persistence backend for filing sessions.

    Implementations: InMemorySessionBackend (dev), RedisSessionBackend (prod).
    """

    def put(self, session: Session, ttl: timedelta) -> None:
        """Store or refresh a session."""
        ...

    def get(self, session_id: str) -> Session | None:
        """Retrieve a session, or None if missing/expired."""
        ...

    def delete(self, session_id: str) -> None:
        """Remove a session."""
        ...


class InMemorySessionBackend:
    """Process-local session store. Default for development / single-worker.

    Preserves the original in-memory semantics exactly.
    """

    def __init__(self, ttl_minutes: int = 30) -> None:
        self._sessions: dict[str, Session] = {}
        self._ttl = timedelta(minutes=ttl_minutes)

    def put(self, session: Session, ttl: timedelta) -> None:
        self._sessions[session.session_id] = session

    def get(self, session_id: str) -> Session | None:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if datetime.now(UTC) - session.last_accessed > self._ttl:
            del self._sessions[session_id]
            return None
        session.last_accessed = datetime.now(UTC)
        return session

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def _cleanup_expired(self) -> None:
        now = datetime.now(UTC)
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.last_accessed > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]


class RedisSessionBackend:
    """Redis-backed session store. Global, survives restart, horizontally scalable.

    Sessions are pickled (binary) and stored with a TTL equal to the session
    idle timeout. On every GET the TTL is refreshed (sliding idle window) and
    last_accessed updated. On Redis failure the store degrades to an in-memory
    fallback so the API keeps serving (no data loss guarantee under outage, but
    no crash).
    """

    def __init__(
        self,
        ttl_minutes: int = 30,
        redis_client=None,
        *,
        key_prefix: str = "session:",
        fallback: SessionBackend | None = None,
    ) -> None:
        self._ttl = timedelta(minutes=ttl_minutes)
        self._key_prefix = key_prefix
        self._redis = redis_client
        self._redis_available = False
        self._fallback = fallback or InMemorySessionBackend(ttl_minutes)

        if redis_client is not None:
            self._redis = redis_client
            self._test_connection()
        else:
            self._init_from_env()

    def _init_from_env(self) -> None:
        import os
        redis_url = os.environ.get("REDIS_URL")
        if not redis_url:
            logger.info("REDIS_URL not set — sessions use in-memory fallback")
            return
        try:
            import redis
            self._redis = redis.Redis.from_url(
                redis_url,
                socket_connect_timeout=2,
                socket_timeout=2,
                decode_responses=False,  # we store pickled bytes
            )
            self._test_connection()
        except (redis.ConnectionError, redis.ValidationError) as e:
            logger.warning("Redis session backend unavailable: %s", e)
            self._redis = None

    def _test_connection(self) -> None:
        if self._redis is None:
            return
        try:
            self._redis.ping()
            self._redis_available = True
            logger.info("Redis session backend connected")
        except (ConnectionError, TimeoutError) as e:
            logger.warning("Redis ping failed — in-memory fallback: %s", e)
            self._redis_available = False
            self._redis = None

    def _key(self, session_id: str) -> str:
        return f"{self._key_prefix}{session_id}"

    def put(self, session: Session, ttl: timedelta) -> None:
        if self._redis_available and self._redis is not None:
            try:
                session.last_accessed = datetime.now(UTC)
                self._redis.set(
                    self._key(session.session_id),
                    pickle.dumps(session),
                    ex=int(ttl.total_seconds()),
                )
                return
            except (ConnectionError, TimeoutError) as e:
                logger.warning("Redis session put failed, fallback: %s", e)
                self._redis_available = False
        self._fallback.put(session, ttl)

    def get(self, session_id: str) -> Session | None:
        if self._redis_available and self._redis is not None:
            try:
                raw = self._redis.get(self._key(session_id))
                if raw is None:
                    return None
                session: Session = pickle.loads(raw)
                # Sliding idle window: refresh TTL and last_accessed
                session.last_accessed = datetime.now(UTC)
                self._redis.set(
                    self._key(session_id),
                    pickle.dumps(session),
                    ex=int(self._ttl.total_seconds()),
                )
                return session
            except (ConnectionError, TimeoutError) as e:
                logger.warning("Redis session get failed, fallback: %s", e)
                self._redis_available = False
        return self._fallback.get(session_id)

    def delete(self, session_id: str) -> None:
        if self._redis_available and self._redis is not None:
            try:
                self._redis.delete(self._key(session_id))
                return
            except (ConnectionError, TimeoutError) as e:
                logger.warning("Redis session delete failed, fallback: %s", e)
                self._redis_available = False
        self._fallback.delete(session_id)


class SessionManager:
    """Manages filing sessions through a pluggable backend.

    Public API (create / get / delete) is unchanged from the in-memory version,
    so existing callers (routes.py, simulation.py) require no modifications.
    """

    def __init__(self, ttl_minutes: int = 30, backend: SessionBackend | None = None) -> None:
        self._ttl = timedelta(minutes=ttl_minutes)
        self._backend = backend or self._default_backend(ttl_minutes)

    @staticmethod
    def _default_backend(ttl_minutes: int) -> SessionBackend:
        """Choose backend: Redis if REDIS_URL configured, else in-memory."""
        import os
        if os.environ.get("REDIS_URL"):
            try:
                return RedisSessionBackend(ttl_minutes=ttl_minutes)
            except (ConnectionError, TimeoutError) as e:  # pragma: no cover — defensive
                logger.warning("Redis backend init failed, in-memory: %s", e)
        return InMemorySessionBackend(ttl_minutes=ttl_minutes)

    def create(self, pan: str, dob: str) -> Session:
        """Create a new filing session."""
        session_id = uuid.uuid4().hex
        session = Session(
            session_id=session_id,
            pan=pan.strip().upper(),
            dob=dob.strip(),
        )
        self._backend.put(session, self._ttl)
        return session

    def get(self, session_id: str) -> Session | None:
        """Get a session by ID, updating last_accessed/sliding TTL."""
        return self._backend.get(session_id)

    def delete(self, session_id: str) -> None:
        """Delete a session."""
        self._backend.delete(session_id)


# Global session manager instance — public API unchanged.
session_manager = SessionManager()
