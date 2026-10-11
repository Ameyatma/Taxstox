from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional
from datetime import datetime

T = TypeVar('T')

class BaseStorage(ABC, Generic[T]):
    """Base class for all storage backends."""

    @abstractmethod
    async def save(self, data: T, timestamp: datetime) -> None:
        """Save data with a timestamp (for point-in-time correctness)."""
        pass

    @abstractmethod
    async def get(self, timestamp: datetime) -> Optional[T]:
        """Get the most recent data as of the given timestamp (point-in-time query)."""
        pass

    @abstractmethod
    async def get_range(self, start: datetime, end: datetime) -> list[T]:
        """Get data within a timestamp range."""
        pass