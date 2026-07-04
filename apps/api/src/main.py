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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup/shutdown."""
    # Startup: initialize DB, configure logging
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("src").setLevel(logging.INFO)

    from src.db.database import init_db
    init_db()
    logging.getLogger(__name__).info("Database initialized.")

    yield
    # Shutdown — nothing to clean up (no persistence)


app = FastAPI(
    title="TaxStox — ITR Auto-Filing Engine",
    description="Upload Form 16 + AIS. Answer 5 yes/no questions. Download validated ITR JSON.",
    version="0.1.0",
    lifespan=lifespan,
)

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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "TaxStox",
        "tagline": "File ITR in 2 minutes. Master your stocks.",
        "docs": "/docs",
    }
