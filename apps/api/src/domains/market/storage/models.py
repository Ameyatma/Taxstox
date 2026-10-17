import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, Boolean, PrimaryKeyConstraint, UniqueConstraint, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship

from src.domains.market.storage.database import Base


def _short_uid() -> str:
    """Return a 12-character short UUID matching Taxstox canonical format."""
    return str(uuid.uuid4())[:12]


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    exchange = Column(String(50))
    sector = Column(String(100))
    industry = Column(String(100))
    is_active = Column(Integer, default=1)


class EODCandle(Base):
    __tablename__ = "eod_candles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), ForeignKey("stocks.ticker"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    vwap = Column(Float)
    as_of_date = Column(DateTime, nullable=False)
    publish_date = Column(DateTime, nullable=False)

    __table_args__ = (
        Index('idx_eod_candles_sym_ts', 'symbol', text('timestamp DESC')),
    )


class NewsCatalyst(Base):
    __tablename__ = "news_catalysts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), ForeignKey("stocks.ticker"), nullable=False)
    publish_timestamp = Column(DateTime, nullable=False)
    headline = Column(String(500))
    content = Column(String)
    sentiment_score = Column(Float)
    confidence = Column(Float)
    catalyst_type = Column(String(50))
    rationale = Column(String)


class RecommendationSignal(Base):
    __tablename__ = "recommendation_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    symbol = Column(String(10), ForeignKey("stocks.ticker"), nullable=False)
    final_rating = Column(String(20))
    composite_score = Column(Float)
    tech_score = Column(Float)
    sentiment_score = Column(Float)
    stop_loss_price = Column(Float)
    target_price = Column(Float)

    __table_args__ = (
        Index('idx_signals_sym_ts', 'symbol', text('date DESC')),
    )


class FactorValue(Base):
    __tablename__ = "factors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), ForeignKey("stocks.ticker"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    factor_name = Column(String(50), nullable=False)
    factor_type = Column(String(50))
    value = Column(Float)
    data_timestamp = Column(DateTime)
    ic_score = Column(Float)
    ir_score = Column(Float)


class IndicatorValue(Base):
    __tablename__ = "indicators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), ForeignKey("stocks.ticker"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    indicator = Column(String(50), nullable=False)
    value = Column(Float)
    meta_data = Column(String)  # Renamed from metadata to avoid conflict


# Consumer (Multi-Tenant) Schemas


class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(String(12), primary_key=True, default=_short_uid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    portfolio = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")


class Portfolio(Base):
    __tablename__ = "portfolios"

    user_id = Column(String(12), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(10), nullable=False)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Composite primary key
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'symbol', name='pk_portfolio'),
    )

    # Relationships
    user = relationship("User", back_populates="portfolio")


class NotificationLog(Base):
    """
    Record of an alert already delivered to a user.

    The unique constraint is the idempotency guarantee: a repeat pipeline run for the
    same trading day finds the row already present and skips the duplicate push.
    """
    __tablename__ = "notification_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(12), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(10), nullable=False)
    alert_type = Column(String(50), nullable=False)
    date = Column(DateTime, nullable=False)  # the trading day the alert belongs to
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint(
            'user_id', 'symbol', 'alert_type', 'date',
            name='uq_notification_log_user_symbol_type_date'
        ),
        Index('idx_notification_log_lookup', 'user_id', 'symbol', 'alert_type', 'date'),
    )


# Autonomous research (RD-Agent) schemas


class AlphaFactor(Base):
    """A machine-proposed technical factor, persisted with its measured IC."""
    __tablename__ = "alpha_factors"

    id = Column(String(12), primary_key=True, default=_short_uid)
    name = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(String(1000))
    python_code = Column(Text, nullable=False)
    information_coefficient = Column(Float)
    win_rate = Column(Float)
    is_active = Column(Boolean, default=False, nullable=False)
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))