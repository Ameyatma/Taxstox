"""Provider framework for fetching official Government of India tax updates.

Each provider is responsible for one official source (PIB, CBDT, Income Tax Dept, MoF).
All providers implement the BaseProvider interface and register themselves in the
provider registry for discovery.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Type

logger = logging.getLogger(__name__)


# ── Data Models ───────────────────────────────────────────────────────

@dataclass
class RawUpdate:
    """A raw, unprocessed update from an official government source."""

    title: str
    raw_content: str  # Raw HTML / text content for AI summarization
    url: str  # Canonical source URL (used for dedup)
    published_date: str  # ISO date string (YYYY-MM-DD)
    source: str  # e.g. "pib", "incometax", "cbdt", "mof"


# ── Base Provider ─────────────────────────────────────────────────────

class BaseProvider(ABC):
    """Abstract base for official government data providers."""

    # Override in subclasses
    name: str = "base"
    label: str = "Base Provider"
    base_url: str = ""

    @abstractmethod
    async def fetch(self) -> list[RawUpdate]:
        """Fetch recent updates from this provider's source.

        Returns:
            List of RawUpdate objects. Empty list if nothing new or on error.
        """
        ...


# ── Provider Registry ─────────────────────────────────────────────────

_registry: dict[str, Type[BaseProvider]] = {}


def register_provider(cls: Type[BaseProvider]) -> Type[BaseProvider]:
    """Decorator to register a provider class."""
    # Instantiate temporarily to get the name
    try:
        instance = cls()
        name = instance.name
    except Exception:
        name = cls.__name__.lower()
    _registry[name] = cls
    logger.info("Registered provider: %s (%s)", name, cls.__name__)
    return cls


def get_providers() -> list[BaseProvider]:
    """Return instantiated list of all registered providers."""
    _ensure_imported()
    return [cls() for cls in _registry.values()]


def get_provider_names() -> list[str]:
    """Return list of registered provider names."""
    _ensure_imported()
    return list(_registry.keys())


def _ensure_imported():
    """Ensure all provider modules are imported (triggers @register_provider decorators)."""
    if _registry:
        return  # Already loaded
    # Import provider modules to trigger registration
    try:
        from src.providers import pib_provider  # noqa: F401
    except Exception:
        pass
    try:
        from src.providers import incometax_provider  # noqa: F401
    except Exception:
        pass
    try:
        from src.providers import cbdt_provider  # noqa: F401
    except Exception:
        pass
    try:
        from src.providers import mof_provider  # noqa: F401
    except Exception:
        pass
