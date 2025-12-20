"""
FastAPI main application for Finance-Insight
"""

import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import calculations, discovery, reports, rules, use_cases
from app.engine.translator import smoke_test_gemini

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    logger.info("Starting Finance-Insight API...")
    logger.info("Phase 2: Hybrid Rule Engine initialized")
    
    # Run Gemini API smoke test
    try:
        smoke_test_gemini()
    except Exception as e:
        logger.warning(f"Smoke test encountered an error (non-fatal): {e}")
    
    yield
    # Shutdown
    logger.info("Shutting down Finance-Insight API...")


# Create FastAPI app
app = FastAPI(
    title="Finance-Insight API",
    description="Financial Logic Overlay Engine - Discovery-First Workflow",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(discovery.router)
app.include_router(use_cases.router)
app.include_router(reports.router)
# Phase 2: Rules router
app.include_router(rules.router)
# Phase 2: Calculations router
app.include_router(calculations.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Finance-Insight API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

