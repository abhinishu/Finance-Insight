"""
Robust Configuration Loader for Finance-Insight
Implements security-hardened API key loading with multiple fallback strategies.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
_project_root = Path(__file__).parent.parent.parent
_env_file = _project_root / ".env"
load_dotenv(_env_file)


def get_google_api_key() -> str:
    """
    Robust API key loader with security hardening.
    
    Loading Strategy (in order):
    1. Load from .env file (highest priority)
    2. Fallback to os.environ.get("GOOGLE_API_KEY")
    3. Fallback to os.environ.get("GEMINI_API_KEY") for backward compatibility
    4. Validation: Strip whitespace to prevent accidental spaces
    5. Security Error: Raise SystemExit if no key found
    
    Returns:
        str: The Google Gemini API key (stripped of whitespace)
    
    Raises:
        SystemExit: If no API key is found in any location
    """
    # Strategy 1: Load from .env file (already loaded by load_dotenv above)
    api_key = os.getenv("GOOGLE_API_KEY")
    
    # Strategy 2: Fallback to environment variable (if not in .env)
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY")
    
    # Strategy 3: Backward compatibility with GEMINI_API_KEY
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    
    # Strategy 4: Clean the key (remove accidental spaces)
    if api_key:
        api_key = api_key.strip()
    
    # Strategy 5: Validation - Raise security error if no key found
    if not api_key:
        error_msg = (
            "\n" + "="*70 + "\n"
            "SECURITY ERROR: No API Key found!\n"
            "="*70 + "\n"
            "The Google Gemini API key is required but was not found.\n\n"
            "Please do one of the following:\n"
            "1. Create a .env file in the project root with:\n"
            "   GOOGLE_API_KEY=your_api_key_here\n\n"
            "2. Set the environment variable:\n"
            "   export GOOGLE_API_KEY=your_api_key_here\n\n"
            "3. See .env.example for a template.\n"
            "="*70 + "\n"
        )
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    return api_key


def get_database_url() -> str:
    """
    Get database URL from environment variables.
    
    Returns:
        str: Database connection URL
    """
    return os.getenv(
        "DATABASE_URL",
        "postgresql://finance_user:finance_pass@localhost:5432/finance_insight"
    )

