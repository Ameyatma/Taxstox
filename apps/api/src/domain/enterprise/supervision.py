"""Supervision Workflow — Senior reviews junior work, activity logging.

Enforces CA firm hierarchy: Senior CA reviews Junior CA filings,
Admin oversees everyone. Activity log captures who did what and when.

Traceability: C21.2 (CA Firm Hierarchy — 50%→80%, P5)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class ActivityType(str, Enum):
    CLIENT_ASSIGNED = "client_assigned"
    CLIENT_REMOVED = "client_removed"
    FILING_STARTED = "filing_started"
    FILING_SUBMITTED = "filing_submitted"
    FILING_REVIEWED = "filing_reviewed"
    DOCUMENT_UPLOADED = "document_uploaded"
    ROLE_CHANGED = "role_changed"
    SETTINGS_CHANGED = "settings_changed"
    SSO_CONFIGURED = "sso_configured"
    BILLING_UPDATED = "billing_updated"


@dataclass(frozen=True)
class ActivityLogEntry:
    """A single activity log entry. Immutable audit record."""

    entry_id: UUID
    tenant_id: UUID
    user_id: UUID                        # Who performed the action
    activity_type: ActivityType
    description: str
    target_user_id: UUID | None = None   # Who was affected
    target_resource: str = ""            # What resource was affected
    metadata: dict = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(self, "timestamp",
                              datetime.now(timezone.utc).isoformat())

    @staticmethod
    def create(
        tenant_id: UUID, user_id: UUID, activity_type: ActivityType,
        description: str, target_user_id: UUID | None = None,
        target_resource: str = "", metadata: dict | None = None,
    ) -> ActivityLogEntry:
        return ActivityLogEntry(
            entry_id=uuid4(), tenant_id=tenant_id, user_id=user_id,
            activity_type=activity_type, description=description,
            target_user_id=target_user_id, target_resource=target_resource,
            metadata=metadata or {},
        )


@dataclass
class ReviewRequest:
    """A request for a senior to review a junior's work."""

    request_id: UUID
    tenant_id: UUID
    submitted_by: UUID                   # Junior CA
    submitted_for: UUID                  # Client whose filing is being reviewed
    reviewer_id: UUID | None = None      # Senior CA (assigned)
    financial_year: str = ""
    status: ReviewStatus = ReviewStatus.PENDING
    comments: str = ""
    reviewer_comments: str = ""
    created_at: str = ""
    reviewed_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def approve(self, reviewer_id: UUID, comments: str = "") -> None:
        self.status = ReviewStatus.APPROVED
        self.reviewer_id = reviewer_id
        self.reviewer_comments = comments
        self.reviewed_at = datetime.now(timezone.utc).isoformat()

    def reject(self, reviewer_id: UUID, comments: str) -> None:
        self.status = ReviewStatus.REJECTED
        self.reviewer_id = reviewer_id
        self.reviewer_comments = comments
        self.reviewed_at = datetime.now(timezone.utc).isoformat()

    def request_changes(self, reviewer_id: UUID, comments: str) -> None:
        self.status = ReviewStatus.CHANGES_REQUESTED
        self.reviewer_id = reviewer_id
        self.reviewer_comments = comments
        self.reviewed_at = datetime.now(timezone.utc).isoformat()

    @property
    def is_resolved(self) -> bool:
        return self.status in (ReviewStatus.APPROVED, ReviewStatus.REJECTED)

    @staticmethod
    def create(
        tenant_id: UUID, submitted_by: UUID, submitted_for: UUID,
        financial_year: str = "",
    ) -> ReviewRequest:
        return ReviewRequest(
            request_id=uuid4(), tenant_id=tenant_id,
            submitted_by=submitted_by, submitted_for=submitted_for,
            financial_year=financial_year,
        )


@dataclass
class SupervisionWorkflow:
    """Manages the review workflow between hierarchy levels.

    Domain service. Enforces that:
    - A user can only review work submitted by lower-hierarchy users
    - Activity log captures every action
    """

    tenant_id: UUID
    review_requests: list[ReviewRequest] = field(default_factory=list)
    activity_log: list[ActivityLogEntry] = field(default_factory=list)

    def submit_for_review(
        self, submitted_by: UUID, submitted_for: UUID,
        reviewer_hierarchy_level: int, submitter_hierarchy_level: int,
        financial_year: str = "",
    ) -> Optional[ReviewRequest]:
        """Submit work for review. Validates hierarchy.

        Returns None if submitter is higher or equal to reviewer.
        """
        if submitter_hierarchy_level <= reviewer_hierarchy_level:
            return None  # Cannot review equal or higher authority

        request = ReviewRequest.create(
            tenant_id=self.tenant_id, submitted_by=submitted_by,
            submitted_for=submitted_for, financial_year=financial_year,
        )
        self.review_requests.append(request)
        return request

    def approve_review(self, request_id: UUID, reviewer_id: UUID, comments: str = "") -> bool:
        for req in self.review_requests:
            if req.request_id == request_id and req.status == ReviewStatus.PENDING:
                req.approve(reviewer_id, comments)
                self._log(reviewer_id, ActivityType.FILING_REVIEWED,
                         f"Approved filing for client", target_resource=str(request_id))
                return True
        return False

    def reject_review(self, request_id: UUID, reviewer_id: UUID, comments: str) -> bool:
        for req in self.review_requests:
            if req.request_id == request_id and req.status == ReviewStatus.PENDING:
                req.reject(reviewer_id, comments)
                self._log(reviewer_id, ActivityType.FILING_REVIEWED,
                         f"Rejected filing: {comments}", target_resource=str(request_id))
                return True
        return False

    def get_pending_reviews(self, reviewer_id: UUID | None = None) -> list[ReviewRequest]:
        pending = [r for r in self.review_requests if r.status == ReviewStatus.PENDING]
        if reviewer_id:
            pending = [r for r in pending if r.reviewer_id is None or r.reviewer_id == reviewer_id]
        return pending

    def get_user_activity(
        self, user_id: UUID, limit: int = 50,
    ) -> list[ActivityLogEntry]:
        entries = [e for e in self.activity_log if e.user_id == user_id]
        return sorted(entries, key=lambda e: e.timestamp, reverse=True)[:limit]

    @property
    def pending_review_count(self) -> int:
        return len(self.get_pending_reviews())

    @property
    def approved_count(self) -> int:
        return sum(1 for r in self.review_requests if r.status == ReviewStatus.APPROVED)

    @property
    def recent_activity(self) -> list[ActivityLogEntry]:
        return sorted(self.activity_log, key=lambda e: e.timestamp, reverse=True)[:20]

    def _log(
        self, user_id: UUID, activity_type: ActivityType,
        description: str, target_user_id: UUID | None = None,
        target_resource: str = "",
    ) -> None:
        self.activity_log.append(ActivityLogEntry.create(
            tenant_id=self.tenant_id, user_id=user_id,
            activity_type=activity_type, description=description,
            target_user_id=target_user_id, target_resource=target_resource,
        ))
