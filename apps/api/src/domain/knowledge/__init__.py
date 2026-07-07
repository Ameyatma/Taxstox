"""Knowledge bounded context — Tax provision knowledge, glossary, circulars, education.

Domain layer. Zero framework imports. Pure Python.
Provides the semantic foundation for the AI Intelligence platform.

Traceability: C11.1 (Tax Knowledge Graph), C11.2 (Tax Provision KB),
             C11.4 (Tax Concept Glossary), C11.5 (CBDT Circular DB),
             C11.6 (Taxpayer Education Content)
"""

from src.domain.knowledge.provision_kb import (
    ProvisionKnowledgeBase,
    ProvisionEntry,
    provision_kb,
)
from src.domain.knowledge.tax_glossary import (
    TaxGlossary,
    GlossaryEntry,
    tax_glossary,
)
from src.domain.knowledge.circular_db import (
    CBDTCircularDatabase,
    Circular,
    circular_db,
)
from src.domain.knowledge.education_content import (
    EducationContent,
    EducationArticle,
    ExpertiseLevel,
    education_content,
)

__all__ = [
    "ProvisionKnowledgeBase",
    "ProvisionEntry",
    "provision_kb",
    "TaxGlossary",
    "GlossaryEntry",
    "tax_glossary",
    "CBDTCircularDatabase",
    "Circular",
    "circular_db",
    "EducationContent",
    "EducationArticle",
    "ExpertiseLevel",
    "education_content",
]
