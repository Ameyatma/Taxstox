from src.models.ais import (
    AISAnnexureIISalary,
    AISData,
    AISEquityMFSale,
    AISOtherUnitSale,
    AISRefund,
    AISSavingsInterest,
    AISSecuritiesPurchase,
    AISTDSEntry,
)
from src.models.api import (
    AnswersSubmitRequest,
    ExportResponse,
    Question,
    QuestionsResponse,
    TaxSummaryResponse,
    UploadRequest,
    UploadResponse,
    ValidationReport,
    ValidationResult,
)
from src.models.form16 import (
    ChapterVIADeductions,
    Form12BA,
    Form16Annexure,
    Form16Data,
    Form16PartA,
    Form16PartB,
    OtherExemption,
    PerquisitesDetail,
    QuarterlyTDS,
    Regime,
    SalaryComponent,
    Section10Exemptions,
    TaxComputation,
)
from src.models.tax import (
    CGDateRanges,
    CGSaleEntry,
    ClassifiedCGData,
    RegimeResult,
    UnifiedTaxData,
    UserAnswers,
)

__all__ = [
    # Form 16
    "Form16Data", "Form16PartA", "Form16PartB", "Form16Annexure",
    "Form12BA", "SalaryComponent", "QuarterlyTDS", "Section10Exemptions",
    "OtherExemption", "ChapterVIADeductions", "TaxComputation",
    "PerquisitesDetail", "Regime",
    # AIS
    "AISData", "AISTDSEntry", "AISSavingsInterest", "AISEquityMFSale",
    "AISOtherUnitSale", "AISSecuritiesPurchase", "AISRefund",
    "AISAnnexureIISalary",
    # Tax
    "UnifiedTaxData", "CGSaleEntry", "CGDateRanges", "UserAnswers",
    "ClassifiedCGData", "RegimeResult",
    # API
    "UploadRequest", "UploadResponse", "QuestionsResponse", "Question",
    "TaxSummaryResponse", "ExportResponse", "ValidationResult",
    "ValidationReport", "AnswersSubmitRequest",
]
