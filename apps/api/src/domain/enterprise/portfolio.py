"""Client Portfolio — Client categorization, status tracking, and document vault.

Enables CA firms to categorize clients (HNI, NRI, salaried, business),
track filing status per client, and maintain a document vault.

Traceability: C21.3 (Client Portfolio — 50%→80%, P5)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class FilingStatus(str, Enum):
    NOT_STARTED = "not_started"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    IN_PROGRESS = "in_progress"
    READY_FOR_REVIEW = "ready_for_review"
    REVIEWED = "reviewed"
    FILED = "filed"
    REJECTED = "rejected"
    REVISED = "revised"


class ClientPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ClientFilingStatus:
    """Per-client filing status within a tenant's portfolio.

    Tracks where each client is in the filing pipeline.
    """

    client_user_id: UUID
    financial_year: str
    itr_type: str = ""                       # ITR-1 through ITR-7
    status: FilingStatus = FilingStatus.NOT_STARTED
    priority: ClientPriority = ClientPriority.NORMAL
    assigned_to: UUID | None = None          # Staff user_id
    due_date: str = ""                       # "2026-07-31"
    last_updated: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.last_updated:
            self.last_updated = datetime.now(timezone.utc).isoformat()

    def advance(self, new_status: FilingStatus) -> None:
        self.status = new_status
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def assign_to(self, staff_user_id: UUID) -> None:
        self.assigned_to = staff_user_id
        self.last_updated = datetime.now(timezone.utc).isoformat()

    @property
    def is_complete(self) -> bool:
        return self.status in (FilingStatus.FILED, FilingStatus.REVISED)

    @property
    def is_overdue(self) -> bool:
        if not self.due_date or self.is_complete:
            return False
        return datetime.now(timezone.utc).isoformat()[:10] > self.due_date


@dataclass(frozen=True)
class DocumentVaultEntry:
    """A document stored in the client's document vault. Value object."""

    document_id: UUID
    client_user_id: UUID
    tenant_id: UUID
    document_type: str                      # "form16", "ais", "pan_card", "investment_proof"
    filename: str
    financial_year: str = ""
    uploaded_at: str = ""
    uploaded_by: UUID | None = None
    expiry_date: str = ""                   # For time-sensitive docs
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.uploaded_at:
            object.__setattr__(self, "uploaded_at",
                              datetime.now(timezone.utc).isoformat())

    @staticmethod
    def create(
        client_user_id: UUID, tenant_id: UUID,
        document_type: str, filename: str,
        financial_year: str = "", uploaded_by: UUID | None = None,
    ) -> DocumentVaultEntry:
        return DocumentVaultEntry(
            document_id=uuid4(), client_user_id=client_user_id,
            tenant_id=tenant_id, document_type=document_type,
            filename=filename, financial_year=financial_year,
            uploaded_by=uploaded_by,
        )


@dataclass
class ClientPortfolio:
    """A tenant's client portfolio — filing statuses, document vault.

    Entity within Tenant aggregate. Provides the operational view
    of all clients for a CA firm.
    """

    tenant_id: UUID
    filing_statuses: list[ClientFilingStatus] = field(default_factory=list)
    document_vault: list[DocumentVaultEntry] = field(default_factory=list)

    # ── Filing Status Methods ───────────────────────────────────────

    def get_client_status(
        self, client_user_id: UUID, financial_year: str,
    ) -> Optional[ClientFilingStatus]:
        for fs in self.filing_statuses:
            if fs.client_user_id == client_user_id and fs.financial_year == financial_year:
                return fs
        return None

    def set_client_status(
        self, client_user_id: UUID, financial_year: str,
        status: FilingStatus, itr_type: str = "",
    ) -> ClientFilingStatus:
        existing = self.get_client_status(client_user_id, financial_year)
        if existing:
            existing.advance(status)
            if itr_type:
                existing.itr_type = itr_type
            return existing
        fs = ClientFilingStatus(
            client_user_id=client_user_id, financial_year=financial_year,
            status=status, itr_type=itr_type,
        )
        self.filing_statuses.append(fs)
        return fs

    @property
    def clients_by_status(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for fs in self.filing_statuses:
            key = fs.status.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    @property
    def overdue_clients(self) -> list[ClientFilingStatus]:
        return [fs for fs in self.filing_statuses if fs.is_overdue]

    @property
    def completion_rate(self) -> float:
        total = len(self.filing_statuses)
        if total == 0:
            return 0.0
        completed = sum(1 for fs in self.filing_statuses if fs.is_complete)
        return completed / total

    # ── Document Vault Methods ──────────────────────────────────────

    def add_document(
        self, client_user_id: UUID, document_type: str, filename: str,
        financial_year: str = "", uploaded_by: UUID | None = None,
    ) -> DocumentVaultEntry:
        entry = DocumentVaultEntry.create(
            client_user_id=client_user_id, tenant_id=self.tenant_id,
            document_type=document_type, filename=filename,
            financial_year=financial_year, uploaded_by=uploaded_by,
        )
        self.document_vault.append(entry)
        return entry

    def get_client_documents(
        self, client_user_id: UUID, financial_year: str = "",
    ) -> list[DocumentVaultEntry]:
        results = [d for d in self.document_vault if d.client_user_id == client_user_id]
        if financial_year:
            results = [d for d in results if d.financial_year == financial_year]
        return results

    def get_documents_by_type(self, document_type: str) -> list[DocumentVaultEntry]:
        return [d for d in self.document_vault if d.document_type == document_type]

    @property
    def total_documents(self) -> int:
        return len(self.document_vault)
