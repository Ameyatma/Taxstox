"""Reporting Engine — Custom report builder and generation.

Engine layer. Imports from domain. No framework imports.
"""

from src.engine.reporting.custom_report_builder import (
    CustomReportEngine,
    ReportGenerationResult,
)

__all__ = [
    "CustomReportEngine",
    "ReportGenerationResult",
]
