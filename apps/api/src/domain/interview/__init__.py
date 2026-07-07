"""Interview bounded context — Adaptive, personalized, offline-capable tax interview.

Domain layer. Zero framework imports. Pure Python.

Traceability: C13.2 (Adaptive Question Engine), C13.5 (Real-Time Validation),
             C13.6 (Interview Personalization), C13.8 (Offline Interview)
"""

from src.domain.interview.personalization import (
    InterviewPersonalizationEngine,
    QuestionRelevanceScore,
    TaxpayerProfile,
    personalization_engine,
)
from src.domain.interview.offline import (
    OfflineInterviewPack,
    OfflineQuestion,
    OfflineResponse,
    pack_interview,
)

__all__ = [
    "InterviewPersonalizationEngine",
    "QuestionRelevanceScore",
    "TaxpayerProfile",
    "personalization_engine",
    "OfflineInterviewPack",
    "OfflineQuestion",
    "OfflineResponse",
    "pack_interview",
]
