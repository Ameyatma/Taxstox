"""TaxStox Backend — FastAPI Application Entry Point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup/shutdown."""
    # Startup
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("src").setLevel(logging.INFO)
    yield
    # Shutdown — nothing to clean up (no persistence)


app = FastAPI(
    title="TaxStox — ITR Auto-Filing Engine",
    description="Upload Form 16 + AIS. Answer 5 yes/no questions. Download validated ITR JSON.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "TaxStox",
        "tagline": "File ITR in 2 minutes. Master your stocks.",
        "docs": "/docs",
    }
