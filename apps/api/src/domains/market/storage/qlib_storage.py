from datetime import datetime
from typing import Any
from storage.models import FactorValue, IndicatorValue, Stock


class QlibStorage:
    """Storage implementation for factors and indicators."""

    def __init__(self, config: dict):
        self.config = config

    def _get_or_create_stock(self, symbol: str) -> Stock:
        """Get or create a stock record (simplified for verification)."""
        # In a real implementation, this would query the database.
        # For verification, we return a mock stock object.
        # Note: This is a placeholder and not meant for production use.
        return Stock(ticker=symbol)

    def _save_factors(self, session, data: Any, timestamp: datetime) -> None:
        """Save factor batch to the factors table."""
        for factor in data.factors:
            # Get or create stock
            stock = self._get_or_create_stock(factor.symbol)
            db_factor = FactorValue(
                symbol=factor.symbol,
                timestamp=factor.timestamp,
                factor_name=factor.factor_name,
                factor_type=factor.factor_type,
                value=factor.value,
                data_timestamp=factor.data_timestamp,
                ic_score=factor.ic_score,
                ir_score=factor.ir_score
            )
            session.add(db_factor)

    def _save_indicators(self, session, data: Any, timestamp: datetime) -> None:
        """Save indicator batch to the indicators table."""
        for indicator in data.indicators:
            # Get or create stock
            stock = self._get_or_create_stock(indicator.symbol)
            db_indicator = IndicatorValue(
                symbol=indicator.symbol,
                timestamp=indicator.timestamp,
                indicator=indicator.indicator,
                value=indicator.value,
                meta_data=str(indicator.metadata) if indicator.metadata else None
            )
            session.add(db_indicator)