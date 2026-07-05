"""API request/response models."""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from src.models.form16 import Regime


class UploadRequest(BaseModel):
    pan: str
    dob: str  # DDMMYYYY format


class UploadResponse(BaseModel):
    session_id: str
    status: str  # "parsed", "password_required", "error"
    data_summary: Optional[dict] = None
    password_required: bool = False
    password_hint: Optional[str] = None


class Question(BaseModel):
    id: str
    text: str
    type: str  # yes_no, number, dropdown, text
    sub_questions: Optional[list["Question"]] = None
    impact: str = ""
    suppressible: bool = True

    # For conditional display
    depends_on: Optional[str] = None
    depends_on_answer: Optional[str] = None


class QuestionsResponse(BaseModel):
    itr_type: str = "ITR-2"
    regime_recommended: Regime = Regime.NEW
    regime_savings: Decimal = Decimal("0")
    income_summary: dict = Field(default_factory=dict)
    questions: list[Question] = Field(default_factory=list)
    # Auto-detected data from PDFs (salary, TDS, interest, CG, deductions)
    auto_detected: dict = Field(default_factory=dict)
    itr_form: str = "ITR-2"


class AnswersSubmitRequest(BaseModel):
    session_id: str
    answers: dict  # question_id → answer


class TaxSummaryResponse(BaseModel):
    income: dict = Field(default_factory=dict)            # Nested detail: {Salary: {Gross, HRA, ...}}
    deductions: dict = Field(default_factory=dict)         # {80C, 80CCD2, 80D, ...}
    taxable_income: Decimal = Decimal("0")
    tax_breakdown: dict = Field(default_factory=dict)      # Line-item tax: {Slab, 112A, 111A, rebate, cess}
    payments: dict = Field(default_factory=dict)           # {TDS Employer, TDS Other, ...}
    balance_payable: Decimal = Decimal("0")
    regime: Regime = Regime.NEW
    regime_savings: Decimal = Decimal("0")
    filing_deadline: Optional[date] = None
    # V2: Both regime breakdowns for side-by-side comparison
    old_regime_breakdown: dict = Field(default_factory=dict)
    new_regime_breakdown: dict = Field(default_factory=dict)


class ExportResponse(BaseModel):
    filename: str = ""
    json_data: dict = Field(default_factory=dict)
    validation_passed: bool = False
    validation_warnings: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    check_name: str
    passed: bool
    severity: str = "info"  # error, warning, info
    message: str = ""
    fix_suggestion: Optional[str] = None


class ValidationReport(BaseModel):
    results: list[ValidationResult] = Field(default_factory=list)
    passed: int = 0
    failed: int = 0
    warnings: int = 0

    @property
    def can_file(self) -> bool:
        return all(
            r.passed or r.severity != "error" for r in self.results
        )
