"""Employer/Enterprise Integration — Bulk employee tax filing integration.

Traceability: C16.4 (Employer/Enterprise Integration — 0%→30%, P7)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class EmployerIntegration:
    """Employer integration for bulk employee tax filing. Entity."""

    integration_id: UUID
    tenant_id: UUID
    employer_name: str
    employer_tan: str = ""
    employees_count: int = 0
    bulk_form16_enabled: bool = False
    auto_ais_fetch: bool = False
    status: str = "pending"            # pending, active, suspended
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def activate(self) -> None:
        self.status = "active"
        self.updated_at = datetime.now(timezone.utc).isoformat()

    @staticmethod
    def create(
        tenant_id: UUID, employer_name: str, employer_tan: str = "",
    ) -> EmployerIntegration:
        return EmployerIntegration(
            integration_id=uuid4(), tenant_id=tenant_id,
            employer_name=employer_name, employer_tan=employer_tan,
        )
