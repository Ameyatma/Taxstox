from src.models.form16 import (
    Form16Data,
    Form16PartA,
    Form16PartB,
    Form16Annexure,
    Form12BA,
    SalaryComponent,
    QuarterlyTDS,
    Section10Exemptions,
    OtherExemption,
    ChapterVIADeductions,
    TaxComputation,
    PerquisitesDetail,
    Regime,
)
from src.models.ais import (
    AISData,
    AISTDSEntry,
    AISSavingsInterest,
    AISEquityMFSale,
    AISOtherUnitSale,
    AISSecuritiesPurchase,
    AISRefund,
    AISAnnexureIISalary,
)
from src.models.tax import (
    UnifiedTaxData,
    CGSaleEntry,
    CGDateRanges,
    UserAnswers,
    ClassifiedCGData,
    RegimeResult,
)
from src.models.api import (
    UploadRequest,
    UploadResponse,
    QuestionsResponse,
    Question,
    TaxSummaryResponse,
    ExportResponse,
    ValidationResult,
    ValidationReport,
    AnswersSubmitRequest,
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
