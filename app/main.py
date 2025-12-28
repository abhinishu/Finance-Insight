"""
FastAPI main application for Finance-Insight
"""

import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, calculations, discovery, reports, rules, runs, use_cases
from app.engine.translator import smoke_test_gemini
from init_app import init_db
from init_app import init_db

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
    
    # Initialize database schema on startup
    try:
        init_db()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't raise - allow app to start even if schema check fails
        # (useful for development when DB might not be available)
    
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

# Configure CORS - Must be added before routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(discovery.router)
app.include_router(use_cases.router)
app.include_router(reports.router)
# Phase 2: Rules router
app.include_router(rules.router)
# Phase 2: Calculations router
app.include_router(calculations.router)
# Phase 3: Admin router
app.include_router(admin.router)
# Phase 3.2: Runs router (date-anchored run selection)
app.include_router(runs.router)


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

