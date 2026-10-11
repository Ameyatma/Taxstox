from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import os
import logging
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

# DATABASE_URL is loaded from environment (Taxstox uses dotenv; production sets DATABASE_URL)
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./data/stox/stock_intelligence.db"  # Default to SQLite for development consistency
)

# Handle postgres:// URL format for SQLAlchemy compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

logger = logging.getLogger(__name__)

# SQLite does not accept the QueuePool sizing arguments used for Postgres, so only
# apply connection pooling to server-backed databases.
_engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}
if not DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(pool_size=10, max_overflow=20)

# Create engine
engine = create_engine(DATABASE_URL, **_engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create scoped session for thread safety
db_session = scoped_session(SessionLocal)

# Base class for declarative models
Base = declarative_base()
Base.query = db_session.query_property()

def _check_timescaledb_available() -> bool:
    """Check if TimescaleDB extension is available in the database."""
    try:
        with engine.connect() as conn:
            # Try to query the TimescaleDB version
            result = conn.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"))
            return result.rowcount > 0
    except Exception as e:
        logger.debug(f"TimescaleDB not available: {e}")
        return False

def _create_standard_table(table_name: str, create_sql: str):
    """Create a standard table if it doesn't exist."""
    try:
        with engine.connect() as conn:
            # Check if table exists
            inspector = inspect(engine)
            if not inspector.has_table(table_name):
                logger.info(f"Creating standard table: {table_name}")
                conn.execute(text(create_sql))
                conn.commit()
            else:
                logger.debug(f"Table {table_name} already exists")
    except Exception as e:
        logger.error(f"Error creating table {table_name}: {e}")
        raise

def _create_hypertable(table_name: str, time_column: str):
    """Convert a table to a TimescaleDB hypertable."""
    try:
        with engine.connect() as conn:
            # Check if TimescaleDB is available
            if not _check_timescaledb_available():
                logger.warning("TimescaleDB not available, creating standard table instead")
                return False

            # Check if table is already a hypertable
            result = conn.execute(text(
                "SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = :table_name"
            ), {"table_name": table_name})

            if result.rowcount > 0:
                logger.debug(f"Table {table_name} is already a hypertable")
                return True

            # Create the hypertable
            logger.info(f"Creating hypertable: {table_name}")
            conn.execute(text(
                f"SELECT create_hypertable('{table_name}', '{time_column}', if_not_exists => TRUE)"
            ))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error creating hypertable {table_name}: {e}")
        # Fall back to standard table
        return False

def init_db():
    """Initialize the database by creating all tables with TimescaleDB support where available."""
    # Import all models here to ensure they are registered with Base.metadata
    from src.domains.market.storage import models

    timescaledb_available = _check_timescaledb_available()
    logger.info(f"TimescaleDB available: {timescaledb_available}")

    if timescaledb_available:
        # Create extension if it doesn't exist
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
                conn.commit()
                logger.info("TimescaleDB extension created/confirmed")
        except Exception as e:
            logger.error(f"Failed to create TimescaleDB extension: {e}")
            timescaledb_available = False

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Conditionally create hypertables for time-series tables
    if timescaledb_available:
        # Try to create hypertables - if they fail, tables remain as standard tables
        _create_hypertable("eod_candles", "timestamp")
        _create_hypertable("recommendation_signals", "date")
    else:
        logger.info("Using standard tables (TimescaleDB not available)")

@contextmanager
def get_db_session():
    """Context manager for getting a database session (scripts, tasks, pipelines)."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db():
    """FastAPI dependency that yields a database session and closes it after the request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()