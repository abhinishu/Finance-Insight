"""
FastAPI main application for Finance-Insight
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import calculations, discovery, reports, rules, use_cases
from app.engine.translator import smoke_test_gemini, initialize_gemini, GEMINI_AVAILABLE
from app.database import create_db_engine, get_database_url, get_session_factory
from app.core.config import get_google_api_key

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def mask_password_in_url(database_url: str) -> str:
    """
    Mask password in database URL for safe logging.
    
    Args:
        database_url: Full database connection string
        
    Returns:
        URL with password masked as '***'
    """
    try:
        parsed = urlparse(database_url)
        if parsed.password:
            # Replace password with ***
            masked_netloc = f"{parsed.username}:***@{parsed.hostname}"
            if parsed.port:
                masked_netloc += f":{parsed.port}"
            masked_url = urlunparse((
                parsed.scheme,
                masked_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            return masked_url
        return database_url
    except Exception:
        # If parsing fails, return a safe version
        if '@' in database_url:
            parts = database_url.split('@')
            if len(parts) == 2:
                return f"{parts[0].split(':')[0]}:***@{parts[1]}"
        return database_url


async def check_database_connection(max_retries: int = 3, retry_delay: int = 5) -> bool:
    """
    Pre-flight health check: Attempt to connect to database with retry logic.
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Seconds to wait between retries
        
    Returns:
        True if connection successful, False otherwise
    """
    database_url = get_database_url()
    masked_url = mask_password_in_url(database_url)
    
    logger.info("=" * 70)
    logger.info("PRE-FLIGHT HEALTH CHECK: Database Connection")
    logger.info("=" * 70)
    logger.info(f"Attempting to connect to database...")
    logger.info(f"Database URL: {masked_url}")
    
    for attempt in range(1, max_retries + 1):
        try:
            engine = create_db_engine()
            SessionFactory = get_session_factory(engine)
            session = SessionFactory()
            
            # Simple query to verify connection
            result = session.execute(text("SELECT 1")).scalar()
            session.close()
            
            if result == 1:
                logger.info(f"✅ Database connection successful (attempt {attempt}/{max_retries})")
                logger.info("=" * 70)
                return True
                
        except SQLAlchemyError as e:
            logger.warning(f"⚠️ Database connection attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                logger.info(f"Waiting {retry_delay} seconds before retry...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("=" * 70)
                logger.error("❌ DATABASE CONNECTION ERROR")
                logger.error("=" * 70)
                logger.error(f"Failed to connect after {max_retries} attempts.")
                logger.error(f"Database URL (password masked): {masked_url}")
                logger.error("Please verify:")
                logger.error("  1. PostgreSQL server is running")
                logger.error("  2. Database exists and is accessible")
                logger.error("  3. Connection credentials are correct")
                logger.error("  4. Network/firewall allows connection")
                logger.error("=" * 70)
                return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during database connection: {e}")
            logger.error(f"Database URL (password masked): {masked_url}")
            return False
    
    return False


async def check_gemini_api() -> bool:
    """
    Pre-flight health check: Verify Gemini API key is active by listing models.
    
    Returns:
        True if API key is valid, False otherwise
    """
    logger.info("=" * 70)
    logger.info("PRE-FLIGHT HEALTH CHECK: Gemini API")
    logger.info("=" * 70)
    
    if not GEMINI_AVAILABLE:
        logger.warning("⚠️ Gemini package not available - API check skipped")
        logger.warning("Install with: pip install google-generativeai")
        logger.info("=" * 70)
        return False
    
    try:
        # Get API key (will raise SystemExit if not found, which is fine for startup)
        try:
            api_key = get_google_api_key()
            logger.info("API key found in configuration")
        except SystemExit:
            logger.error("❌ GEMINI API KEY ERROR")
            logger.error("=" * 70)
            logger.error("No Gemini API key found. Please set GOOGLE_API_KEY in .env file.")
            logger.error("=" * 70)
            return False
        
        # Initialize Gemini and verify key is active by attempting to create a model
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Try to create a model instance to verify API key is active
            logger.info("Verifying API key by initializing a model...")
            try:
                # Try to list models (this will fail if API key is invalid)
                models = list(genai.list_models())
                model_count = len(models)
                logger.info(f"✅ Gemini API key is active - {model_count} models available")
            except AttributeError:
                # If list_models doesn't exist, try creating a model instance instead
                model = genai.GenerativeModel('gemini-2.5-flash')
                logger.info("✅ Gemini API key is active - model initialization successful")
            except Exception as list_error:
                # Fallback: try to create a simple model to verify key
                try:
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    logger.info("✅ Gemini API key is active - model initialization successful")
                except Exception as model_error:
                    raise list_error  # Raise the original error
            
            logger.info("=" * 70)
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            if 'api key' in error_msg or 'authentication' in error_msg or 'invalid' in error_msg:
                logger.error("❌ GEMINI API KEY ERROR")
                logger.error("=" * 70)
                logger.error("API key is invalid or inactive.")
                logger.error(f"Error: {e}")
                logger.error("Please verify your GOOGLE_API_KEY in .env file.")
                logger.error("=" * 70)
            else:
                logger.warning(f"⚠️ Gemini API check encountered an error: {e}")
                logger.warning("This may be a temporary network issue. Continuing startup...")
                logger.info("=" * 70)
            return False
            
    except Exception as e:
        logger.error(f"❌ Unexpected error during Gemini API check: {e}")
        logger.info("=" * 70)
        return False


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup - Pre-flight health checks
    logger.info("")
    logger.info("🚀 Starting Finance-Insight API...")
    logger.info("Phase 3.1: Portability & Zero-Touch Setup")
    logger.info("")
    
    # Pre-flight check 1: Database connection with retry
    db_ok = await check_database_connection(max_retries=3, retry_delay=5)
    if not db_ok:
        logger.error("")
        logger.error("⚠️ WARNING: Database connection failed. Some features may not work.")
        logger.error("The application will continue to start, but database operations will fail.")
        logger.error("")
    
    # Pre-flight check 2: Gemini API key verification
    gemini_ok = await check_gemini_api()
    if not gemini_ok:
        logger.warning("")
        logger.warning("⚠️ WARNING: Gemini API key verification failed.")
        logger.warning("GenAI rule translation features will not be available.")
        logger.warning("")
    
    # Legacy smoke test (for backward compatibility)
    if gemini_ok:
        try:
            smoke_test_gemini()
        except Exception as e:
            logger.warning(f"Smoke test encountered an error (non-fatal): {e}")
    
    logger.info("✅ Finance-Insight API startup complete!")
    logger.info("")
    
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

