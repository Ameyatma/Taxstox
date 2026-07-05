"""TaxStox Backend — FastAPI Application Entry Point."""

from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()  # Load .env file for local dev (DATABASE_URL, etc.)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router as itr_router
from src.api.auth_routes import router as auth_router
from src.api.dashboard import router as dashboard_router
from src.api.calculators import router as calculators_router
from src.api.simulation import router as simulation_router
from src.api.tax_routes import router as tax_router
from src.middleware.correlation import CorrelationMiddleware
from src.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup/shutdown."""
    # Startup: structured logging, DB init, scheduler
    setup_logging()
    logger.info("TaxStox backend starting")

    from src.db.database import init_db, init_tax_tables

    init_db()
    init_tax_tables()
    logger.info("Database initialized")

    # Start the tax sync scheduler
    from src.scheduler import start_scheduler

    start_scheduler()
    logger.info("Scheduler started")

    yield
    # Shutdown
    from src.scheduler import stop_scheduler

    stop_scheduler()
    logger.info("TaxStox backend stopped")


app = FastAPI(
    title="TaxStox — ITR Auto-Filing Engine",
    description="Upload Form 16 + AIS. Answer 5 yes/no questions. Download validated ITR JSON.",
    version="0.1.0",
    lifespan=lifespan,
)

# Correlation ID — must be added before other middleware
app.add_middleware(CorrelationMiddleware)

# CORS — allow frontend (local dev + production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://taxstox.com",
        "https://www.taxstox.com",
        "https://taxstox.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(itr_router)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(calculators_router)
app.include_router(simulation_router)
app.include_router(tax_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "TaxStox",
        "tagline": "File ITR in 2 minutes. Master your stocks.",
        "docs": "/docs",
    }


@app.get("/api/v1/health")
async def health_check():
    """Enhanced health check with dependency status."""
    import os

    health = {
        "status": "ok",
        "service": "TaxStox ITR Engine",
        "version": "0.1.0",
    }

    # Database connectivity check
    try:
        from src.db.database import get_db

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        health["database"] = "connected"
    except Exception as e:
        health["database"] = "disconnected"
        health["database_error"] = str(e)[:200]

    # JWT secret configured check
    jwt_secret = os.environ.get("TAXSTOX_JWT_SECRET", "")
    if jwt_secret and jwt_secret != "taxstox-dev-secret-change-in-production":
        health["jwt_secret"] = "configured"
    else:
        health["jwt_secret"] = "missing_or_default"

    return health
