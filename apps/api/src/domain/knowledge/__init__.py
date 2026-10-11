"""Knowledge bounded context — Tax provision knowledge, glossary, circulars, education.

Domain layer. Zero framework imports. Pure Python.
Provides the semantic foundation for the AI Intelligence platform.

Traceability: C11.1 (Tax Knowledge Graph), C11.2 (Tax Provision KB),
             C11.4 (Tax Concept Glossary), C11.5 (CBDT Circular DB),
             C11.6 (Taxpayer Education Content)
"""

from src.domain.knowledge.circular_db import (
    CBDTCircularDatabase,
    Circular,
    circular_db,
)
from src.domain.knowledge.education_content import (
    EducationArticle,
    EducationContent,
    ExpertiseLevel,
    education_content,
)
from src.domain.knowledge.provision_kb import (
    ProvisionEntry,
    ProvisionKnowledgeBase,
    provision_kb,
)
from src.domain.knowledge.tax_glossary import (
    GlossaryEntry,
    TaxGlossary,
    tax_glossary,
)

__all__ = [
    "CBDTCircularDatabase",
    "Circular",
    "EducationArticle",
    "EducationContent",
    "ExpertiseLevel",
    "GlossaryEntry",
    "ProvisionEntry",
    "ProvisionKnowledgeBase",
    "TaxGlossary",
    "circular_db",
    "education_content",
    "provision_kb",
    "tax_glossary",
]
