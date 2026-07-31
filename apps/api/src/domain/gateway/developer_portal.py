"""Developer Portal — API product catalog, developer registration.

Traceability: C16.8 (Developer Portal — 0%→30%, P7)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ApiProduct:
    """An API product available to developers. Value object."""

    product_id: str                    # "itr-filing", "tax-computation", "pan-verification"
    name: str                          # "ITR Filing API"
    description: str
    base_path: str                     # "/api/v1"
    rate_limit_per_minute: int = 100
    requires_approval: bool = False


@dataclass
class DeveloperRegistration:
    """A registered developer/organization using the API. Entity."""

    registration_id: UUID
    organization_name: str
    contact_email: str
    website: str = ""
    api_keys: list[UUID] = field(default_factory=list)  # key_ids
    subscribed_products: list[str] = field(default_factory=list)
    status: str = "pending"            # pending, approved, suspended
    registered_at: str = ""

    def __post_init__(self) -> None:
        if not self.registered_at:
            self.registered_at = datetime.now(timezone.utc).isoformat()

    def approve(self) -> None:
        self.status = "approved"

    def suspend(self) -> None:
        self.status = "suspended"

    def add_key(self, key_id: UUID) -> None:
        self.api_keys.append(key_id)

    def subscribe(self, product_id: str) -> None:
        if product_id not in self.subscribed_products:
            self.subscribed_products.append(product_id)

    @staticmethod
    def create(organization_name: str, contact_email: str, website: str = "") -> DeveloperRegistration:
        return DeveloperRegistration(
            registration_id=uuid4(), organization_name=organization_name,
            contact_email=contact_email, website=website,
        )


# ── Standard API Products ────────────────────────────────────────────

API_PRODUCTS = [
    ApiProduct("itr-filing", "ITR Filing API",
               "Submit and manage ITR filings programmatically", "/api/v1/filing", 100),
    ApiProduct("tax-computation", "Tax Computation API",
               "Compute tax liability for any income scenario", "/api/v1/compute", 200, True),
    ApiProduct("pan-verification", "PAN Verification API",
               "Verify PAN against NSDL database", "/api/v1/verify/pan", 50, True),
    ApiProduct("document-parsing", "Document Parsing API",
               "Parse Form 16, AIS, and 26AS PDF documents", "/api/v1/parse", 50),
    ApiProduct("ais-data", "AIS Data API",
               "Access parsed AIS financial transaction data", "/api/v1/ais", 100),
]
