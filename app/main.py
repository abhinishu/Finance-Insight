"""
FastAPI main application for Finance-Insight
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import discovery, use_cases, reports

# Create FastAPI app
app = FastAPI(
    title="Finance-Insight API",
    description="Financial Logic Overlay Engine - Discovery-First Workflow",
    version="1.0.0"
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

