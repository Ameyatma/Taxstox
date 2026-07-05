# AI-DOS Engineering Standards v1.0.0

> **Status:** GOVERNANCE DOCUMENT — Level 5 Authority
> **Supersedes:** Nothing
> **Ratified:** 2026-07-05
> **Last Amended:** 2026-07-05
> **Next Review:** 2026-10-05
> **Applies To:** All code, all modules, all contributors
> **Parent Document:** [00-Constitution.md](00-Constitution.md)

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Language-Specific Standards](#2-language-specific-standards)
3. [Naming Conventions](#3-naming-conventions)
4. [Code Organization](#4-code-organization)
5. [Error Handling](#5-error-handling)
6. [Logging Standards](#6-logging-standards)
7. [Type Safety](#7-type-safety)
8. [Configuration Management](#8-configuration-management)
9. [Dependency Management](#9-dependency-management)
10. [Security Engineering Standards](#10-security-engineering-standards)
11. [Code Review Checklist](#11-code-review-checklist)
12. [Failure Cases](#12-failure-cases)

---

## 1. Purpose and Scope

### 1.1 Purpose

This document operationalizes Constitutional Principles P1 (Consistency), P3 (Explicit Over Implicit), P5 (Testability Is Design), and P7 (Security by Design) into concrete, enforceable engineering standards.

### 1.2 Scope

Every line of code committed to this repository must conform to these standards. Violations are flagged in code review and blocked from merge. Legacy code that pre-dates these standards carries `CODE_DEBT` markers.

### 1.3 Enforcement

| Standard Type | Enforcement Mechanism | Blocking? |
|---------------|----------------------|-----------|
| Formatting | Ruff (Python) — auto-formatted on commit | ✅ Yes (CI fails) |
| Linting | Ruff (Python) — all rules enabled | ✅ Yes (CI fails) |
| Type Checking | MyPy (strict mode) | ✅ Yes (CI fails) |
| Naming | Code review | ✅ Yes |
| Security | Bandit + custom rules | ✅ Yes (CI fails) |
| Complexity | Radon (CC ≤ 10 per function) | ❌ Warning only |

---

## 2. Language-Specific Standards

### 2.1 Python (Primary Backend Language)

**Version:** Python 3.12+

#### 2.1.1 Style

Follow PEP 8 with these project-specific additions:

```python
# ✅ CORRECT: Module header
"""
Module: tax_engine.computation.orchestrator

Orchestrates the tax computation pipeline:
1. Income aggregation across all heads
2. Deduction application (Chapter VI-A)
3. Tax slab application
4. Surcharge and cess computation
5. TDS/advance tax set-off

See ADR-XXXX for the computation pipeline design.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Protocol

# Constants at module level, after imports
MAX_ITR_AGE_DAYS: Final[int] = 120
DEFAULT_CESS_RATE: Final[Decimal] = Decimal("0.04")

logger = logging.getLogger(__name__)
```

#### 2.1.2 Imports

```python
# ✅ CORRECT: Import order
# 1. Standard library
# 2. Third-party
# 3. Internal modules
# Each group separated by blank line, sorted alphabetically

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, field_validator

from tax_engine.domain.entities import Taxpayer, TaxLiability
from tax_engine.rules.registry import RuleRegistry
```

```python
# ❌ WRONG: Never import *
from tax_engine.domain.entities import *  # FORBIDDEN

# ❌ WRONG: Never import from internal modules of other modules
from tax_rules.fy2025_26._internal import _SlabHelper  # FORBIDDEN
```

#### 2.1.3 Function Design

```python
# ✅ CORRECT: Well-typed, documented function
def compute_tax_on_total_income(
    total_income: Decimal,
    financial_year: FinancialYear,
    regime: TaxRegime,
    *,
    override_slabs: SlabCollection | None = None,
) -> TaxOnTotalIncome:
    """
    Compute tax on total income by applying the appropriate tax slabs.

    Args:
        total_income: Total income after all deductions (rounded to nearest ₹10 per §288B).
        financial_year: The financial year for which tax is computed.
        regime: OLD_REGIME or NEW_REGIME.
        override_slabs: Optional slab override for testing/simulation. Not for production use.

    Returns:
        TaxOnTotalIncome with per-slab breakdown.

    Raises:
        InvalidFinancialYearError: If no slabs are defined for the given financial year.
        RegimeNotApplicableError: If the regime is not valid for the given financial year.
        NegativeIncomeError: If total_income is negative (should be caught earlier).

    Example:
        >>> compute_tax_on_total_income(
        ...     total_income=Decimal("850000"),
        ...     financial_year=FinancialYear.FY2025_26,
        ...     regime=TaxRegime.NEW_REGIME,
        ... )
        TaxOnTotalIncome(tax=Decimal("42500"), breakdown=[...])
    """
    _validate_inputs(total_income, financial_year, regime)

    slabs = override_slabs or SlabRepository.get_active_slabs(financial_year, regime)
    calculator = SlabBasedCalculator(slabs)
    result = calculator.compute(total_income)

    logger.info(
        "Tax computed",
        extra={
            "total_income": str(total_income),
            "financial_year": str(financial_year),
            "regime": str(regime),
            "tax": str(result.tax),
        },
    )
    return result


# ❌ WRONG: Vague name, no types, no docs
def calc(x, y):
    return x * y / 100
```

#### 2.1.4 Classes and Dataclasses

```python
# ✅ CORRECT: Dataclass for data, class for behavior
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import date
from uuid import UUID, uuid4

@dataclass(frozen=True)  # Immutable by default
class TaxSlab:
    """A single tax bracket with its rate."""

    slab_id: UUID = field(default_factory=uuid4)
    income_from: Decimal  # Inclusive lower bound
    income_to: Decimal | None  # None = no upper bound
    rate: Decimal  # e.g., 0.05 for 5%

    def __post_init__(self) -> None:
        """Validate slab integrity after initialization."""
        if self.income_from < 0:
            raise InvalidSlabError(f"income_from must be non-negative: {self.income_from}")
        if self.income_to is not None and self.income_from >= self.income_to:
            raise InvalidSlabError(
                f"income_from ({self.income_from}) must be less than income_to ({self.income_to})"
            )
        if not (0 <= self.rate <= 1):
            raise InvalidSlabError(f"rate must be between 0 and 1: {self.rate}")

    def contains(self, income: Decimal) -> bool:
        """Check if this slab applies to the given income."""
        if self.income_to is None:
            return income > self.income_from
        return self.income_from < income <= self.income_to

    def tax_for_amount(self, amount: Decimal) -> Decimal:
        """Compute tax for an amount falling within this slab."""
        return (amount * self.rate).quantize(Decimal("0.01"))
```

### 2.2 Future Languages

When additional languages are introduced (TypeScript for frontend, SQL for migrations), language-specific standards will be appended to this section. Until then, all standards refer to Python.

---

## 3. Naming Conventions

### 3.1 General Principles

1. **Descriptive over clever.** `compute_tax_liability` not `do_it`
2. **Consistent vocabulary.** Same concept = same word everywhere
3. **Pronounceable.** `taxpayer_repository` not `txpyrRepo`
4. **Searchable.** Full words, no abbreviations unless universally understood in the domain

### 3.2 Domain-Specific Vocabulary

These terms have specific meanings. Use them consistently:

| Term | Meaning | Don't Use |
|------|---------|-----------|
| `taxpayer` | The person/entity whose tax is being computed | `user`, `client`, `customer` |
| `financial_year` | FY2025-26, etc. | `fy`, `year`, `tax_year` |
| `assessment_year` | AY2026-27, etc. | `ay`, `return_year` |
| `regime` | OLD_REGIME or NEW_REGIME | `scheme`, `plan`, `option` |
| `tax_liability` | The total tax owed | `tax`, `amount_due`, `payable` |
| `deduction` | Chapter VI-A deduction | `exemption` (different concept) |
| `exemption` | Income not included in total income | `deduction` (different concept) |
| `rebate` | 87A rebate from tax | `discount`, `reduction` |
| `surcharge` | Additional tax on high income | `extra_tax`, `super_tax` |
| `cess` | Health & Education Cess | `levy`, `additional_charge` |
| `total_income` | Income after deductions | `taxable_income` |
| `gross_total_income` | Income before deductions | `gross_income` |
| `tds` | Tax Deducted at Source | `withholding_tax` |

### 3.3 Naming Rules by Construct

| Construct | Convention | Example |
|-----------|-----------|---------|
| Module | `snake_case` | `tax_engine/` |
| Package | `snake_case` | `rule_engine/` |
| Class | `PascalCase` | `TaxSlab`, `RuleRegistry` |
| Exception | `PascalCase` + `Error` | `InvalidTaxSlabError` |
| Function/Method | `snake_case` + verb | `compute_tax`, `get_active_slabs()` |
| Variable | `snake_case` | `total_income`, `slab_collection` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_DEDUCTION_80C` |
| Boolean variable | `is_` / `has_` / `can_` prefix | `is_senior_citizen`, `has_business_income` |
| Private member | `_` prefix | `_validate_slabs()`, `_tax_cache` |
| Type alias | `PascalCase` | `TaxRate = Decimal` |
| Protocol/Interface | `PascalCase` | `class TaxRuleProtocol(Protocol)` |
| Enum | `PascalCase` | `class TaxRegime(StrEnum)` |
| Enum member | `UPPER_SNAKE_CASE` | `TaxRegime.OLD_REGIME` |
| Test file | `test_` + module name | `test_tax_slab.py` |
| Test function | `test_` + behavior | `test_computes_tax_for_mid_slab_income` |
| Fixture | `snake_case` | `fy2025_26_slabs` |

---

## 4. Code Organization

### 4.1 Module Structure

Every module follows this structure:

```
module_name/
├── __init__.py              # Public API re-exports only
├── _internal/               # Private implementation (not importable by other modules)
│   ├── __init__.py
│   └── ...
├── api/                     # Public API (if the module exposes an API)
│   ├── __init__.py
│   ├── routes.py
│   ├── schemas.py           # Request/response Pydantic models
│   └── dependencies.py
├── domain/                  # Domain logic (if the module has domain entities)
│   ├── __init__.py
│   ├── entities.py
│   ├── value_objects.py
│   ├── aggregates.py
│   └── services.py
├── infrastructure/          # External dependencies (database, HTTP clients, etc.)
│   ├── __init__.py
│   ├── repository.py
│   ├── db_models.py         # ORM models (SQLAlchemy)
│   └── clients.py
├── config.py                # Module configuration
├── exceptions.py            # Module-specific exceptions
├── py.typed                 # PEP 561 marker (empty file)
└── README.md                # Module documentation
```

### 4.2 File Size Limits

| File Type | Max Lines | Rationale |
|-----------|-----------|-----------|
| Module (`.py`) | 500 | Above 500, split into sub-modules |
| Test file | 1000 | Tests can be longer but should still be focused |
| `__init__.py` | 50 | Re-exports only; no logic |
| Config file | 100 | If longer, split by environment |

### 4.3 Function and Method Size Limits

| Metric | Limit | Rationale |
|--------|-------|-----------|
| Lines per function | ≤ 50 | If longer, extract helper functions |
| Parameters | ≤ 5 | If more, use a dataclass/config object |
| Cyclomatic complexity | ≤ 10 | If higher, simplify or split |
| Nesting depth | ≤ 3 | If deeper, extract or use guard clauses |
| Return statements | ≤ 3 | If more, the function does too much |

### 4.4 Public API Design

```python
# ✅ CORRECT: __init__.py exports ONLY the public API
# module_name/__init__.py
from module_name.domain.entities import TaxSlab, SlabCollection
from module_name.domain.services import SlabBasedCalculator
from module_name.exceptions import InvalidSlabError, SlabNotFoundError

__all__ = [
    "TaxSlab",
    "SlabCollection",
    "SlabBasedCalculator",
    "InvalidSlabError",
    "SlabNotFoundError",
]
```

---

## 5. Error Handling

### 5.1 Exception Hierarchy

```python
# All project exceptions inherit from a base exception
class TaxPlatformError(Exception):
    """Base exception for all project errors."""
    def __init__(self, message: str, *, code: str | None = None, details: dict | None = None):
        self.message = message
        self.code = code or "INTERNAL_ERROR"
        self.details = details or {}
        super().__init__(message)

# Domain exceptions
class DomainError(TaxPlatformError):
    """Base for domain rule violations."""

class InvalidTaxSlabError(DomainError):
    """Tax slab configuration is invalid."""

class IncomeHeadNotApplicableError(DomainError):
    """The specified income head does not apply to this taxpayer."""

class RegimeNotApplicableError(DomainError):
    """The specified regime is not valid."""

class DeductionLimitExceededError(DomainError):
    """The claimed deduction exceeds the statutory limit."""

# Infrastructure exceptions
class InfrastructureError(TaxPlatformError):
    """Base for infrastructure failures."""

class RepositoryError(InfrastructureError):
    """Database operation failed."""

class ExternalServiceError(InfrastructureError):
    """External API call failed."""

# Validation exceptions
class ValidationError(TaxPlatformError):
    """Input validation failed."""

class PANFormatError(ValidationError):
    """PAN format is invalid."""

class AadhaarFormatError(ValidationError):
    """Aadhaar format is invalid."""

# Computation exceptions
class ComputationError(TaxPlatformError):
    """Tax computation failed."""

class IncompleteDataError(ComputationError):
    """Required data is missing for computation."""

class RuleConflictError(ComputationError):
    """Two applicable rules produce conflicting results."""
```

### 5.2 Exception Handling Rules

```python
# RULE 1: Never catch and silence. Always log or propagate.
# ❌ WRONG:
try:
    compute_tax(data)
except Exception:
    pass  # FORBIDDEN

# RULE 2: Catch specific exceptions, not generic ones.
# ❌ WRONG:
try:
    compute_tax(data)
except Exception:  # Too broad
    logger.error("Tax computation failed")

# ✅ CORRECT:
try:
    compute_tax(data)
except IncompleteDataError as e:
    logger.warning("Cannot compute tax: missing data", extra=e.details)
    raise  # Re-raise domain exceptions so the caller can handle them
except InfrastructureError as e:
    logger.error("Infrastructure failure during tax computation", exc_info=True)
    raise ComputationError("Tax computation failed due to system error") from e

# RULE 3: Domain exceptions carry context.
# ✅ CORRECT:
raise DeductionLimitExceededError(
    f"80C deduction of ₹{claimed:,.2f} exceeds the limit of ₹{limit:,.2f}",
    code="DEDUCTION_LIMIT_EXCEEDED",
    details={
        "section": "80C",
        "claimed": str(claimed),
        "limit": str(limit),
        "excess": str(claimed - limit),
        "taxpayer_id": str(taxpayer_id),
    },
)

# RULE 4: Infrastructure exceptions get error codes for API responses.
# ✅ CORRECT:
raise RepositoryError(
    "Failed to retrieve tax slabs for FY2025-26",
    code="DB_QUERY_FAILED",
    details={"financial_year": "FY2025-26", "query": "get_active_slabs"},
)

# RULE 5: Never expose stack traces to users. API layer catches and transforms.
# In the API layer:
@app.exception_handler(TaxPlatformError)
async def tax_platform_error_handler(request, exc: TaxPlatformError):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request.state.request_id,
            }
        },
    )

@app.exception_handler(Exception)
async def unhandled_error_handler(request, exc: Exception):
    logger.error("Unhandled error", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Reference: " + request.state.request_id,
                "request_id": request.state.request_id,
            }
        },
    )
```

### 5.3 Error Handling Decision Tree

```
ERROR OCCURS:
│
├── Is it an expected domain condition (e.g., deduction limit exceeded)?
│   └── Yes → Raise specific domain exception with context → Caller handles
│
├── Is it a validation failure (e.g., invalid PAN)?
│   └── Yes → Raise ValidationError with field-level details → API returns 422
│
├── Is it an infrastructure failure (e.g., database down)?
│   └── Yes → Raise InfrastructureError → API returns 503 → Alert on-call
│
├── Is it a bug (e.g., unexpected None, index error)?
│   └── Yes → Log with full traceback → Raise ComputationError → API returns 500 → Create issue
│
└── Is it a truly unknown error?
    └── Yes → Log with full traceback → Never silence → API returns 500 → P1 incident
```

---

## 6. Logging Standards

### 6.1 Log Levels

| Level | When to Use | Example |
|-------|------------|---------|
| `CRITICAL` | System unusable, data loss imminent | Database connection pool exhausted |
| `ERROR` | Operation failed, needs attention | External API call failed after retries |
| `WARNING` | Something unexpected but recoverable | AIS data not available, proceeding without cross-check |
| `INFO` | Significant business events | Tax computation completed, ITR submitted |
| `DEBUG` | Diagnostic information | Intermediate computation values, rule evaluation trace |
| `TRACE` | Extremely detailed (off in production) | Every function entry/exit with arguments |

### 6.2 Log Format

All logs must be structured JSON for machine parsing:

```python
# ✅ CORRECT: Structured logging
logger.info(
    "Tax computation completed",
    extra={
        "taxpayer_id": str(taxpayer_id),
        "financial_year": "FY2025-26",
        "regime": "NEW_REGIME",
        "total_income": str(total_income),
        "tax_liability": str(tax_liability),
        "computation_id": str(computation_id),
        "duration_ms": duration_ms,
        "rule_count": rule_count,
    },
)
```

### 6.3 What MUST Be Logged

| Event | Level | Required Fields |
|-------|-------|----------------|
| Tax computation started | INFO | `taxpayer_id`, `financial_year`, `regime`, `computation_id` |
| Tax computation completed | INFO | `taxpayer_id`, `financial_year`, `tax_liability`, `duration_ms` |
| Rule evaluation | DEBUG | `rule_id`, `section`, `input`, `output` |
| Deduction applied | DEBUG | `section`, `claimed`, `allowed`, `excess` |
| Validation failure | WARNING | `field`, `value`, `rule`, `message` |
| External API call | INFO | `service`, `endpoint`, `duration_ms`, `status_code` |
| External API failure | ERROR | `service`, `endpoint`, `error`, `retry_count` |
| Database query slow (> 100ms) | WARNING | `query`, `duration_ms`, `params` |
| Security event (auth, access) | INFO | `user_id`, `action`, `resource`, `ip`, `result` |
| Configuration loaded | INFO | `config_source`, `config_version` |

### 6.4 What MUST NEVER Be Logged

| Forbidden Data | Examples | Reason |
|----------------|---------|--------|
| PAN | `ABCDE1234F` | PII — Restricted |
| Aadhaar | `123456789012` | PII — Restricted |
| Full bank account number | `12345678901` | PII — Restricted |
| Passwords/tokens | Any form | Security |
| Full credit card number | Any form | PCI |
| Full tax computation details | Income, deductions (in a single log) | Could reconstruct tax return |
| Email addresses (full) | `user@example.com` | PII — can log `u***r@example.com` |

### 6.5 Correlation ID

Every request must carry a `request_id` (UUID) that flows through all logs for that request.

```python
# Middleware sets request_id
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id

    # Inject into logging context
    with logging_context(request_id=request_id):
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

---

## 7. Type Safety

### 7.1 Type Annotation Rules

```python
# RULE 1: Every function signature must be fully annotated.
# ✅ CORRECT:
def compute_rebate(
    total_income: Decimal,
    tax_before_rebate: Decimal,
    financial_year: FinancialYear,
    regime: TaxRegime,
) -> Decimal:
    ...

# ❌ WRONG: Missing annotations
def compute_rebate(total_income, tax_before_rebate, financial_year, regime):
    ...

# RULE 2: Use Decimal for all monetary values. Never float.
# ✅ CORRECT:
from decimal import Decimal
deduction_limit: Decimal = Decimal("150000")

# ❌ WRONG:
deduction_limit: float = 150000.00  # FORBIDDEN — floating point errors

# RULE 3: Use NewType for domain-specific primitives.
from typing import NewType

PAN = NewType("PAN", str)
AadhaarNumber = NewType("AadhaarNumber", str)
AssessmentYear = NewType("AssessmentYear", str)
Section = NewType("Section", str)

# RULE 4: Use Literal for constrained string values.
from typing import Literal

IncomeHead = Literal["SALARY", "HOUSE_PROPERTY", "BUSINESS", "CAPITAL_GAINS", "OTHER_SOURCES"]
ITRType = Literal["ITR-1", "ITR-2", "ITR-3", "ITR-4", "ITR-5", "ITR-6", "ITR-7"]

# RULE 5: Use Final for constants.
from typing import Final
MAX_80C_DEDUCTION: Final[Decimal] = Decimal("150000")

# RULE 6: Use Protocol for interfaces (not ABC unless you need concrete behavior).
from typing import Protocol

class RuleEvaluator(Protocol):
    def evaluate(self, context: RuleContext) -> RuleResult: ...

class TaxSlabRepository(Protocol):
    def get_active_slabs(
        self, financial_year: FinancialYear, regime: TaxRegime
    ) -> SlabCollection: ...

# RULE 7: Use | for optional types, not Optional[].
# ✅ CORRECT:
def get_taxpayer(pan: PAN) -> Taxpayer | None: ...

# ❌ WRONG:
from typing import Optional
def get_taxpayer(pan: PAN) -> Optional[Taxpayer]: ...
```

### 7.2 Pydantic Models for Data Transfer

```python
# ✅ CORRECT: Use Pydantic for all input/output at API boundaries
from pydantic import BaseModel, Field, field_validator
from datetime import date
from decimal import Decimal
import re

PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")

class TaxpayerCreateRequest(BaseModel):
    """Request model for creating a taxpayer record."""

    model_config = {"extra": "forbid"}  # Reject unknown fields

    pan: str = Field(
        ...,
        pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$",
        description="Permanent Account Number (10 characters)",
        examples=["ABCDE1234F"],
    )
    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Full name as per PAN",
    )
    date_of_birth: date = Field(
        ...,
        description="Date of birth as per PAN",
    )
    mobile: str = Field(
        ...,
        pattern=r"^[6-9][0-9]{9}$",
        description="10-digit mobile number",
    )

    @field_validator("date_of_birth")
    @classmethod
    def must_be_adult(cls, v: date) -> date:
        """Validate the taxpayer is at least 18 years old."""
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError("Taxpayer must be at least 18 years old")
        if age > 150:
            raise ValueError("Invalid date of birth")
        return v

    @field_validator("pan")
    @classmethod
    def validate_pan_format(cls, v: str) -> str:
        """Validate PAN format: 5 letters, 4 digits, 1 letter."""
        if not PAN_PATTERN.match(v.upper()):
            raise ValueError(f"Invalid PAN format: {v}")
        return v.upper()


class TaxpayerResponse(BaseModel):
    """Response model for taxpayer data."""

    model_config = {"from_attributes": True}

    taxpayer_id: str
    pan: str
    name: str
    date_of_birth: date
    mobile: str
    created_at: str
```

---

## 8. Configuration Management

### 8.1 Configuration Principles

1. **Configuration is code.** Config files are versioned, reviewed, and tested.
2. **Schema-validated.** Every config has a Pydantic schema that validates at startup.
3. **Environment-agnostic.** Config file does not contain environment-specific values.
4. **Secrets are external.** Never in config files. Always from secrets manager.
5. **Defaults are explicit.** Every setting has an explicit default or explicitly has none.

### 8.2 Configuration Structure

```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from decimal import Decimal
from typing import Literal

class DatabaseSettings(BaseSettings):
    """Database connection settings."""
    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = Field("localhost", description="Database host")
    port: int = Field(5432, ge=1, le=65535, description="Database port")
    name: str = Field("tax_platform", description="Database name")
    user: str = Field("tax_app", description="Database user")
    password: str = Field(..., description="Database password — from secrets manager")
    pool_size: int = Field(10, ge=1, le=100, description="Connection pool size")
    pool_timeout: int = Field(30, ge=1, le=300, description="Pool timeout in seconds")

class TaxSettings(BaseSettings):
    """Tax computation settings."""
    model_config = SettingsConfigDict(env_prefix="TAX_")

    rounding_precision: int = Field(
        2, ge=0, le=4,
        description="Decimal places for monetary rounding"
    )
    default_regime: Literal["NEW_REGIME", "OLD_REGIME"] = Field(
        "NEW_REGIME",
        description="Default tax regime per Finance Act 2023"
    )
    max_itr_age_days: int = Field(
        120,
        ge=1, le=365,
        description="Maximum age of an ITR that can be revised"
    )

class AppSettings(BaseSettings):
    """Application settings."""
    model_config = SettingsConfigDict(env_prefix="APP_")

    log_level: Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    environment: Literal["development", "staging", "production"] = "development"
    request_timeout_seconds: int = Field(30, ge=1, le=300)

# Combined settings
class Settings(BaseSettings):
    """Root settings aggregating all subsystems."""
    model_config = SettingsConfigDict(env_prefix="TAX_PLATFORM_")

    db: DatabaseSettings = DatabaseSettings()
    tax: TaxSettings = TaxSettings()
    app: AppSettings = AppSettings()

# Singleton
settings = Settings()
```

### 8.3 What MUST Be Configurable

Per Constitutional Invariant I8, these must be configurable without code deployment:

- Tax slab rates and thresholds
- Surcharge rates and thresholds
- Cess rates
- Deduction limits (80C, 80D, etc.)
- Rebate thresholds
- TDS rates
- Interest rates for late payment/refund
- ITR form schema versions
- API rate limits

---

## 9. Dependency Management

### 9.1 Adding Dependencies

```
NEW DEPENDENCY PROCESS:
1. Justify: Why can't we do this with existing dependencies?
2. Evaluate:
   - License compatibility (Apache 2.0, MIT, BSD — require approval for GPL/AGPL)
   - Maintenance status (active in last 6 months)
   - Security history (CVEs in last year)
   - Community size and responsiveness
   - Python version support
3. ADR: Write a brief ADR or note in Decisions.md
4. Pin: Exact version in requirements.txt or pyproject.toml
5. Lock: Update lock file
6. Scan: Run security scan on new dependency tree
```

### 9.2 Dependency Categories

```python
# pyproject.toml
[project]
dependencies = [
    # Core frameworks — versions pinned
    "fastapi>=0.115,<1.0",
    "pydantic>=2.10,<3.0",
    "pydantic-settings>=2.6,<3.0",
    "sqlalchemy>=2.0,<3.0",
    "alembic>=1.14,<2.0",

    # Utilities
    "httpx>=0.28,<1.0",
    "python-json-logger>=2.0,<3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9.0",
    "pytest-cov>=6.0,<7.0",
    "ruff>=0.8,<1.0",
    "mypy>=1.13,<2.0",
    "pre-commit>=4.0,<5.0",
]

test = [
    "pytest>=8.0,<9.0",
    "httpx>=0.28,<1.0",  # For TestClient
]
```

---

## 10. Security Engineering Standards

### 10.1 Input Validation

```python
# RULE: Validate at every trust boundary.
# Trust boundaries: API endpoints, file uploads, message queue consumers, CLI inputs

# ✅ CORRECT: Validate on entry, trust internally
@app.post("/api/v1/tax/compute")
async def compute_tax(request: TaxComputationRequest) -> TaxComputationResponse:
    # Pydantic has already validated the request
    # But cross-field validation happens here:
    try:
        validated = TaxInputValidator.validate(request)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.details)

    result = tax_service.compute(validated)  # Now trusted
    return result


# PAN validation (comprehensive)
def validate_pan(pan: str) -> str:
    """Validate PAN format and checksum."""
    pan = pan.upper().strip()

    if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan):
        raise PANFormatError(f"Invalid PAN format: {pan}")

    # Fourth character indicates taxpayer category
    category = pan[3]
    valid_categories = {"P", "C", "H", "F", "A", "T", "B", "L", "J", "G", "E"}
    if category not in valid_categories:
        raise PANFormatError(f"Invalid PAN category: {category}")

    return pan
```

### 10.2 SQL Injection Prevention

```python
# ✅ CORRECT: Use parameterized queries (SQLAlchemy does this automatically)
stmt = select(Taxpayer).where(Taxpayer.pan == pan)

# ❌ WRONG: String concatenation — FORBIDDEN
stmt = f"SELECT * FROM taxpayers WHERE pan = '{pan}'"  # SQL INJECTION RISK

# ✅ CORRECT: When raw SQL is unavoidable, use parameterized execution
result = await session.execute(
    text("SELECT * FROM taxpayers WHERE pan = :pan"),
    {"pan": pan},
)

# ❌ WRONG: Even with raw SQL, never format strings
result = await session.execute(
    text(f"SELECT * FROM taxpayers WHERE pan = '{pan}'"),  # STILL SQL INJECTION
)
```

### 10.3 Secrets Management

```python
# ✅ CORRECT: Secrets from environment or secrets manager, never in code
import os
from functools import lru_cache

@lru_cache
def get_secret(secret_name: str) -> str:
    """
    Retrieve a secret from the configured secrets backend.
    Falls back to environment variable in development.
    """
    if settings.app.environment == "development":
        secret = os.environ.get(secret_name)
        if not secret:
            raise SecretNotFoundError(f"Secret {secret_name} not found in environment")
        return secret

    # Production: AWS Secrets Manager / Azure Key Vault / HashiCorp Vault
    return secrets_manager.get_secret(secret_name)

# ❌ WRONG: Secrets in code — FORBIDDEN
DB_PASSWORD = "mysecretpassword123"  # NEVER DO THIS
API_KEY = "sk-1234567890abcdef"       # NEVER DO THIS
```

### 10.4 Data Masking

```python
# ✅ CORRECT: Mask sensitive data in logs and error messages
def mask_pan(pan: str) -> str:
    """Mask PAN for logging: ABCDE1234F → ABC**1234F"""
    return f"{pan[:3]}**{pan[5:]}"

def mask_aadhaar(aadhaar: str) -> str:
    """Mask Aadhaar for logging: 123456789012 → ******789012"""
    return f"******{aadhaar[6:]}"

def mask_mobile(mobile: str) -> str:
    """Mask mobile for logging: 9876543210 → 98****3210"""
    return f"{mobile[:2]}****{mobile[6:]}"

# Usage in logging:
logger.info(
    "Taxpayer record accessed",
    extra={
        "pan": mask_pan(pan),
        "accessed_by": user_id,
    },
)
```

---

## 11. Code Review Checklist

The full review process is in [05-Review-Standards.md](05-Review-Standards.md). This is the engineering-specific checklist that every reviewer uses:

```
ENGINEERING REVIEW CHECKLIST:

Formatting & Style:
□ Code is formatted (Ruff formatter would produce no changes)
□ Imports are organized (stdlib → third-party → internal)
□ No `import *` anywhere
□ No unused imports or variables

Naming:
□ Names follow project conventions (snake_case, PascalCase)
□ Names are descriptive and use the domain vocabulary correctly
□ No abbreviations except the approved domain ones
□ Boolean variables use is_/has_/can_ prefixes

Types:
□ All function signatures are fully annotated
□ No `Any` unless exceptional and documented
□ Monetary values use Decimal, never float
□ NewType used for domain-specific primitives where appropriate

Error Handling:
□ Errors are domain exceptions, not generic Exception
□ Exceptions carry context (code, details)
□ No bare `except:` or `except Exception: pass`
□ Error handling follows the decision tree (§5.3)

Logging:
□ Significant events are logged at appropriate levels
□ Log messages are structured (extra=, not f-strings)
□ No PII in logs (PAN, Aadhaar masked)
□ Correlation ID flows through all logs

Security:
□ Input validated at every trust boundary
□ SQL queries are parameterized (no string formatting)
□ No secrets in code, config, or environment
□ Output escaping for its context (HTML, JSON, SQL)

Configuration:
□ New configuration is schema-validated
□ Defaults are reasonable and documented
□ Secrets come from secrets manager/ environment, not config files

Performance:
□ No N+1 queries (check ORM lazy loading)
□ Appropriate indexing considered for new queries
□ No large data loaded into memory unnecessarily

Testing:
□ Tests exist for all new functionality
□ Tests cover happy path, edge cases, and error cases
□ See 04-Testing-Standards.md for detailed test requirements

Documentation:
□ Module README updated if module boundaries changed
□ All public functions have docstrings with Args, Returns, Raises
□ Complex logic has explanatory inline comments
□ ADR written if architecture was changed
```

---

## 12. Failure Cases

### 12.1 Common Engineering Anti-Patterns

| Anti-Pattern | Example | Detection | Remedy |
|-------------|---------|-----------|--------|
| **Float for Money** | `tax = income * 0.3` | Linting rule | Replace with `Decimal` |
| **Magic Numbers** | `if income > 500000:` | Code review | Named constant with source |
| **Swallowed Exception** | `except: pass` | Linting rule | Handle or propagate |
| **Import Star** | `from module import *` | Linting rule | Explicit imports |
| **Mega Function** | 200-line function | Radon complexity | Extract helpers |
| **God Class** | 50-method class | Code review | Split by responsibility |
| **String SQL** | `f"SELECT * FROM {table}"` | Bandit | Parameterized query |
| **Leaked Secret** | `password = "..."` | Secret scanning | Move to secrets manager |
| **Zombie Code** | Commented-out code | Code review | Delete it |
| **False Logging** | `logger.info(f"tax is {tax}")` (unstructured) | Code review | Use `extra={}` |
| **PII in Logs** | PAN unmasked in log | Code review | Use mask functions |

### 12.2 Correctness Verification

Before claiming code is "done," verify:

1. **Run the linter:** `ruff check .` — zero errors
2. **Run the formatter:** `ruff format --check .` — would make no changes
3. **Run type checker:** `mypy . --strict` — zero errors
4. **Run security scanner:** `bandit -c pyproject.toml .` — zero HIGH/MEDIUM
5. **Run tests:** `pytest --cov` — all pass, coverage meets threshold
6. **Manual review:** Walk through the code review checklist (§11)

---

*End of AI-DOS Engineering Standards v1.0.0*

*These standards exist to make every engineer's code look like one engineer wrote it.*
