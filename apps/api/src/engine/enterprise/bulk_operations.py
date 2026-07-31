"""Bulk Operations Engine — CSV/Excel client import, bulk filing, bulk documents.

Enables CA firms to onboard clients in bulk, initiate batch filings,
and request documents from multiple clients simultaneously.

Traceability: C21.5 (Bulk Operations — 0%→60%, P5)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import UUID


class ImportRowStatus(str, Enum):
    SUCCESS = "success"
    SKIPPED = "skipped"            # Duplicate or already exists
    ERROR = "error"                 # Validation failure


@dataclass
class ClientImportRow:
    """A single row from a bulk client import."""

    row_number: int
    pan: str = ""
    name: str = ""
    email: str = ""
    mobile: str = ""
    client_type: str = ""            # "individual", "huf", "business"
    tags: str = ""                   # Comma-separated: "HNI,salaried"
    status: ImportRowStatus = ImportRowStatus.SUCCESS
    error_message: str = ""
    imported_client_id: UUID | None = None

    def validate(self) -> list[str]:
        """Validate row data. Returns list of errors."""
        import re
        errors: list[str] = []
        if not self.name.strip():
            errors.append("Name is required")
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", self.pan.upper()):
            errors.append(f"Invalid PAN format: {self.pan}")
        if self.email and "@" not in self.email:
            errors.append(f"Invalid email: {self.email}")
        if self.mobile and not re.match(r"^[6-9][0-9]{9}$", self.mobile):
            errors.append(f"Invalid mobile: {self.mobile}")
        return errors


@dataclass
class BulkImportResult:
    """Result of a bulk client import operation."""

    tenant_id: UUID
    total_rows: int = 0
    success_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    rows: list[ClientImportRow] = field(default_factory=list)
    imported_client_ids: list[UUID] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return self.success_count / self.total_rows

    @property
    def summary(self) -> str:
        return (
            f"Imported {self.success_count} of {self.total_rows} clients "
            f"({self.skipped_count} skipped, {self.error_count} errors)"
        )


class BulkClientImportEngine:
    """Processes bulk client imports from CSV/Excel.

    Engine layer. Validates, deduplicates, and imports client data
    into a tenant's portfolio.
    """

    # PAN validation regex
    PAN_PATTERN = r"^[A-Z]{5}[0-9]{4}[A-Z]$"

    def parse_csv(self, csv_content: str) -> list[ClientImportRow]:
        """Parse CSV content into import rows."""
        import csv
        import io

        reader = csv.DictReader(io.StringIO(csv_content))
        rows: list[ClientImportRow] = []
        for i, row_dict in enumerate(reader, 1):
            rows.append(ClientImportRow(
                row_number=i,
                pan=row_dict.get("PAN", row_dict.get("pan", "")).strip(),
                name=row_dict.get("Name", row_dict.get("name", "")).strip(),
                email=row_dict.get("Email", row_dict.get("email", "")).strip(),
                mobile=row_dict.get("Mobile", row_dict.get("mobile", "")).strip(),
                client_type=row_dict.get("Type", row_dict.get("type", "individual")).strip(),
                tags=row_dict.get("Tags", row_dict.get("tags", "")).strip(),
            ))
        return rows

    def validate_rows(self, rows: list[ClientImportRow]) -> list[ClientImportRow]:
        """Validate all rows. Sets status and error_message on each row."""
        seen_pans: set[str] = set()
        for row in rows:
            # Check duplicate PAN within the batch
            pan_upper = row.pan.upper()
            if pan_upper in seen_pans:
                row.status = ImportRowStatus.ERROR
                row.error_message = f"Duplicate PAN in import: {row.pan}"
                continue
            seen_pans.add(pan_upper)

            # Validate row
            errors = row.validate()
            if errors:
                row.status = ImportRowStatus.ERROR
                row.error_message = "; ".join(errors)
        return rows

    def process_import(
        self,
        tenant_id: UUID,
        rows: list[ClientImportRow],
        existing_pans: set[str] | None = None,
    ) -> BulkImportResult:
        """Process a validated import against a tenant.

        Args:
            tenant_id: The tenant importing clients
            rows: Pre-validated import rows
            existing_pans: Set of PANs already in the tenant (for dedup)

        Returns:
            BulkImportResult with import statistics
        """
        existing = existing_pans or set()
        result = BulkImportResult(
            tenant_id=tenant_id, total_rows=len(rows),
            rows=rows,
        )

        for row in rows:
            if row.status == ImportRowStatus.ERROR:
                result.error_count += 1
                continue

            # Dedup against existing clients
            if row.pan.upper() in existing:
                row.status = ImportRowStatus.SKIPPED
                row.error_message = f"PAN {row.pan} already exists in portfolio"
                result.skipped_count += 1
                continue

            # Success
            row.status = ImportRowStatus.SUCCESS
            row.imported_client_id = UUID("00000000-0000-0000-0000-000000000000")  # Placeholder
            result.success_count += 1
            result.imported_client_ids.append(row.imported_client_id)

        return result

    @staticmethod
    def extract_tags(tag_string: str) -> list[str]:
        """Parse comma-separated tags into a list."""
        if not tag_string:
            return []
        return [t.strip() for t in tag_string.split(",") if t.strip()]

    @staticmethod
    def generate_csv_template() -> str:
        """Generate a CSV template for client import."""
        return "PAN,Name,Email,Mobile,Type,Tags\nABCDE1234F,John Doe,john@email.com,9876543210,individual,HNI,salaried\n"
