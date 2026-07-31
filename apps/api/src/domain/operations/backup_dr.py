"""Backup & Disaster Recovery — Configuration, plans, and recovery points.

Traceability: C17.6 (Backup & DR — 0%→60%, P7)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class BackupFrequency(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class DRTestResult(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    NOT_RUN = "not_run"


@dataclass(frozen=True)
class RecoveryPoint:
    """A single recovery point (backup snapshot). Value object."""

    point_id: UUID
    created_at: str
    backup_type: str                # "full", "incremental"
    size_bytes: int = 0
    status: str = "completed"
    location: str = ""              # S3 bucket / backup storage path


@dataclass
class BackupConfig:
    """Backup configuration for the platform. Entity."""

    config_id: UUID
    database_backup: bool = True
    file_storage_backup: bool = True
    frequency: BackupFrequency = BackupFrequency.DAILY
    retention_days: int = 90
    encryption_enabled: bool = True
    last_backup: str = ""
    last_verified: str = ""
    backup_location: str = "s3://taxstox-backups/production"

    @staticmethod
    def create() -> BackupConfig:
        return BackupConfig(config_id=uuid4())


@dataclass
class DRPlan:
    """Disaster Recovery plan. Entity."""

    plan_id: UUID
    rpo_minutes: int = 5              # Recovery Point Objective
    rto_minutes: int = 30             # Recovery Time Objective
    last_dr_test: str = ""
    dr_test_result: DRTestResult = DRTestResult.NOT_RUN
    failover_procedure: str = ""
    rollback_procedure: str = ""
    contact_list: list[str] = field(default_factory=list)
    documented_at: str = ""

    def __post_init__(self) -> None:
        if not self.documented_at:
            self.documented_at = datetime.now(timezone.utc).isoformat()

    @staticmethod
    def create() -> DRPlan:
        plan = DRPlan(plan_id=uuid4())
        plan.failover_procedure = (
            "1. Detect outage via health check alerts\n"
            "2. Verify database state in primary region\n"
            "3. Promote read replica in DR region\n"
            "4. Update DNS to point to DR region\n"
            "5. Verify application health in DR region\n"
            "6. Notify users via status page"
        )
        plan.rollback_procedure = (
            "1. Verify primary region is healthy\n"
            "2. Sync DR region data back to primary\n"
            "3. Update DNS back to primary region\n"
            "4. Verify no data loss\n"
            "5. Resume normal operations"
        )
        return plan

    def record_dr_test(self, result: DRTestResult) -> None:
        self.last_dr_test = datetime.now(timezone.utc).isoformat()
        self.dr_test_result = result

    @property
    def is_compliant(self) -> bool:
        return (self.rpo_minutes <= 5 and self.rto_minutes <= 30
                and self.dr_test_result == DRTestResult.PASSED)
