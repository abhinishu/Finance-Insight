"""
GenAI Translator Module - Logic Abstraction Layer
Translates natural language to validated SQL WHERE clauses using Google Gemini Pro.

CRITICAL ARCHITECTURE:
1. Natural Language → JSON Predicate (Gemini Pro)
2. Validate JSON Predicate (check fields exist in fact schema)
3. JSON Predicate → SQL WHERE (only after validation passes)

This three-stage approach prevents AI "hallucination" by validating fields
before SQL generation. All intermediate steps are stored for auditability.
"""

import json
import logging
import os
import time
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Ensure .env is loaded before checking GEMINI_API_KEY
load_dotenv()

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    logger = logging.getLogger(__name__)
    logger.warning("google.generativeai not installed. GenAI features will be disabled.")

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        RetryError
    )
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("tenacity not installed. Retry logic will use basic implementation.")

from pydantic import ValidationError

logger = logging.getLogger(__name__)

# Fact table schema (for validation and prompt engineering)
FACT_TABLE_SCHEMA = {
    'account_id': 'String',
    'cc_id': 'String',
    'book_id': 'String',
    'strategy_id': 'String',
    'trade_date': 'Date',
    'daily_pnl': 'Numeric',
    'mtd_pnl': 'Numeric',
    'ytd_pnl': 'Numeric',
    'pytd_pnl': 'Numeric',
}

# Allowed fields for Gemini (whitelist)
ALLOWED_FIELDS = list(FACT_TABLE_SCHEMA.keys())

# Supported operators for GenAI translation
GENAI_SUPPORTED_OPERATORS = ['equals', 'not_equals', 'in', 'not_in', 'greater_than', 'less_than']

# System instruction for Gemini (optimized for token efficiency - minimal)
# Only essential: Fields whitelist + JSON format
SYSTEM_INSTRUCTION = f"""Translate to JSON: {{'conditions': [{{'field': str, 'operator': str, 'value': any}}], 'conjunction': 'AND'}}

Fields: {', '.join(ALLOWED_FIELDS)}
Operators: {', '.join(GENAI_SUPPORTED_OPERATORS)}
JSON only, no markdown."""

# Step 4.3: Comparison mode system instruction
COMPARISON_SYSTEM_INSTRUCTION = f"""You are a financial data expert analyzing P&L comparisons between two calculation runs.
The user is currently comparing Run A (Baseline) and Run B (Target). Focus your analysis on the deltas between these two versions.
When translating natural language filters, consider the context of comparing these runs.

Translate to JSON: {{'conditions': [{{'field': str, 'operator': str, 'value': any}}], 'conjunction': 'AND'}}
Fields: {', '.join(ALLOWED_FIELDS)}
Operators: {', '.join(GENAI_SUPPORTED_OPERATORS)}
JSON only, no markdown."""


# Custom exception for quota errors
class QuotaExceededError(Exception):
    """Raised when Gemini API quota is exceeded."""
    pass


def is_quota_error(exception: Exception) -> bool:
    """Check if exception is a quota/rate limit error."""
    error_str = str(exception).lower()
    return any(keyword in error_str for keyword in ['429', 'quota', 'rate limit', 'too many requests'])


# Retry decorator using tenacity for exponential backoff
if TENACITY_AVAILABLE:
    retry_on_quota = retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),  # 4s, then 10s (as specified)
        retry=retry_if_exception_type((QuotaExceededError, Exception)),
        reraise=True
    )
else:
    # Fallback: basic retry decorator
    def retry_on_quota(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(3):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if is_quota_error(e) and attempt < 2:
                        wait_time = 4 if attempt == 0 else 10
                        logger.warning(f"Quota error (attempt {attempt + 1}/3). Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise
            return None
        return wrapper


def initialize_gemini():
    """
    Initialize Google Gemini Pro client (using gemini-pro-latest).
    
    Returns:
        Configured GenerativeModel instance
    
    Raises:
        ValueError: If GEMINI_API_KEY is not set or package not installed
    """
    if not GEMINI_AVAILABLE:
        raise ValueError(
            "google.generativeai package is not installed. "
            "Install it with: pip install google-generativeai==0.3.0"
        )
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please set it to your Google Gemini API key."
        )
    genai.configure(api_key=api_key)
    
    # Note: system_instruction parameter not available in google-generativeai 0.3.0
    # We'll include it in the prompt instead
    # ROOT CAUSE FIX: gemini-1.5-flash-latest does NOT exist in v1beta API
    # Use gemini-2.5-flash (stable, available) as primary, with fallback to gemini-flash-latest
    # Flash models have higher rate limits and lower costs for free tier
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("Gemini API initialized successfully with gemini-2.5-flash")
    except Exception as e:
        # Fallback to gemini-flash-latest (always points to latest stable)
        try:
            model = genai.GenerativeModel('gemini-flash-latest')
            logger.info("Gemini API initialized successfully with gemini-flash-latest (fallback)")
        except Exception as e2:
            # Final fallback to gemini-2.0-flash (older but stable)
            model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("Gemini API initialized successfully with gemini-2.0-flash (final fallback)")
    
    return model


def smoke_test_gemini() -> bool:
    """
    Smoke test to verify Gemini API connection on startup.
    Performs a simple "Hello World" translation to confirm the 'Brain' is alive.
    
    Returns:
        True if smoke test passes, False otherwise
    """
    try:
        if not GEMINI_AVAILABLE:
            logger.warning("Gemini package not available - smoke test skipped")
            return False
        
        logger.info("Running Gemini API smoke test...")
        model = initialize_gemini()
        
        # Simple test prompt with system instruction included
        test_prompt = "Exclude book B01"
        full_prompt = f"""{SYSTEM_INSTRUCTION}

Translate this natural language filter to JSON predicate:

{test_prompt}"""
        
        response = model.generate_content(
            full_prompt,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 1000,
            }
        )
        
        response_text = response.text.strip()
        logger.info(f"✅ Gemini API Smoke Test PASSED - Response received: {response_text[:100]}...")
        logger.info("🧠 GenAI 'Brain' is ALIVE and ready for rule translation!")
        return True
        
    except ValueError as e:
        logger.warning(f"⚠️ Gemini API smoke test failed (expected if API key not set): {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Gemini API smoke test failed: {e}")
        return False


@retry_on_quota
def translate_natural_language_to_json(
    logic_en: str,
    fact_schema: Optional[Dict[str, Any]] = None,
    comparison_context: Optional[Dict[str, str]] = None
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Stage 1: Translate natural language to structured JSON predicate using Gemini Pro.
    
    This is the FIRST stage - no SQL is generated yet. Only JSON predicate.
    Uses strict system instruction with whitelisted fields only.
    
    Args:
        logic_en: Natural language description (e.g., "Exclude all EMEA OTC trades")
        fact_schema: Optional fact table schema (defaults to FACT_TABLE_SCHEMA)
    
    Returns:
        Tuple of (predicate_json, errors)
        - predicate_json: Structured JSON predicate
        - errors: List of error messages (empty if successful)
    
    Example output:
        {
            "conditions": [
                {"field": "strategy_id", "operator": "equals", "value": "EQUITY"}
            ],
            "conjunction": "AND"
        }
    """
    if fact_schema is None:
        fact_schema = FACT_TABLE_SCHEMA
    
    try:
        # Initialize Gemini model
        model = initialize_gemini()
        
        # Step 4.3: Use comparison context if provided
        system_instruction = SYSTEM_INSTRUCTION
        if comparison_context and comparison_context.get('baseline_run_id') and comparison_context.get('target_run_id'):
            system_instruction = COMPARISON_SYSTEM_INSTRUCTION
            comparison_note = f"\n\nContext: Comparing Baseline Run ({comparison_context.get('baseline_run_id')}) vs Target Run ({comparison_context.get('target_run_id')})."
        else:
            comparison_note = ""
        
        # Build full prompt with system instruction (since system_instruction param not available in 0.3.0)
        full_prompt = f"""{system_instruction}{comparison_note}

Translate this natural language filter to JSON predicate:

{logic_en}"""
        
        # Call Gemini Pro
        response = model.generate_content(
            full_prompt,
            generation_config={
                "temperature": 0.1,  # Low temperature for consistent output
                "max_output_tokens": 1000,
            }
        )
        
        # Parse JSON from response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        predicate_json = json.loads(response_text)
        
        # Check for error in response
        if 'error' in predicate_json:
            return None, [predicate_json['error']]
        
        # Validate structure
        if 'conditions' not in predicate_json:
            return None, ["Response missing 'conditions' field"]
        
        if not isinstance(predicate_json['conditions'], list):
            return None, ["'conditions' must be a list"]
        
        logger.info(f"Successfully translated natural language to JSON: {logic_en}")
        return predicate_json, []
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Gemini response: {e}")
        return None, [f"Invalid JSON response from Gemini: {str(e)}"]
    except Exception as e:
        error_str = str(e)
        # Check for quota/rate limit errors - raise QuotaExceededError for retry logic
        if is_quota_error(e):
            logger.warning(f"Gemini API quota/rate limit exceeded: {e}")
            # Raise for tenacity retry decorator
            raise QuotaExceededError(f"Gemini API quota exceeded: {str(e)}") from e
        logger.error(f"Error calling Gemini API: {e}", exc_info=True)
        return None, [f"Gemini API error: {str(e)}"]


def validate_json_predicate(
    predicate_json: Dict[str, Any],
    fact_schema: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Stage 2: Validate JSON predicate against fact table schema.
    
    Checks that all fields in the predicate exist in fact_pnl_gold.
    
    Args:
        predicate_json: JSON predicate from Gemini
        fact_schema: Optional fact table schema (defaults to FACT_TABLE_SCHEMA)
    
    Returns:
        List of error messages (empty if validation passes)
    """
    if fact_schema is None:
        fact_schema = FACT_TABLE_SCHEMA
    
    errors = []
    
    if 'conditions' not in predicate_json:
        errors.append("Missing 'conditions' field in predicate")
        return errors
    
    conditions = predicate_json.get('conditions', [])
    if not isinstance(conditions, list):
        errors.append("'conditions' must be a list")
        return errors
    
    for idx, condition in enumerate(conditions):
        if not isinstance(condition, dict):
            errors.append(f"Condition {idx + 1} is not a dictionary")
            continue
        
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        # Validate field exists
        if not field:
            errors.append(f"Condition {idx + 1}: Missing 'field'")
        elif field not in fact_schema:
            errors.append(
                f"Condition {idx + 1}: Field '{field}' does not exist in fact_pnl_gold. "
                f"Allowed fields: {list(fact_schema.keys())}"
            )
        
        # Validate operator
        if not operator:
            errors.append(f"Condition {idx + 1}: Missing 'operator'")
        elif operator not in GENAI_SUPPORTED_OPERATORS:
            errors.append(
                f"Condition {idx + 1}: Operator '{operator}' is not supported. "
                f"Supported operators: {GENAI_SUPPORTED_OPERATORS}"
            )
        
        # Validate value
        if 'value' not in condition:
            errors.append(f"Condition {idx + 1}: Missing 'value'")
        elif operator in ['in', 'not_in'] and not isinstance(value, list):
            errors.append(f"Condition {idx + 1}: Operator '{operator}' requires a list value")
    
    return errors


@retry_on_quota
def translate_rule(
    logic_en: str,
    use_cache: bool = True,
    comparison_context: Optional[Dict[str, str]] = None,
    table_name: str = 'fact_pnl_gold'
) -> Tuple[Optional[Dict[str, Any]], Optional[str], List[str], bool]:
    """
    Main translation function: Natural Language → JSON → Validate → SQL.
    
    This is the complete pipeline that ensures safety:
    1. Call Gemini to get JSON predicate
    2. Validate JSON against fact schema
    3. Convert JSON to SQL (using existing RuleService functions)
    
    Args:
        logic_en: Natural language description
        use_cache: Whether to use cached translations (default: True)
        comparison_context: Optional context for comparison rules
        table_name: Target table name for column mapping (default: 'fact_pnl_gold')
    
    Returns:
        Tuple of (predicate_json, sql_where, errors, translation_successful)
        - predicate_json: Validated JSON predicate (None if failed)
        - sql_where: Generated SQL WHERE clause (None if failed)
        - errors: List of error messages
        - translation_successful: Boolean indicating success
    """
    errors = []
    
    # Check cache first (if enabled)
    if use_cache:
        from app.engine.rule_cache import get_cached_translation
        cached_result = get_cached_translation(logic_en)
        if cached_result:
            logger.info(f"Using cached translation for: {logic_en}")
            return cached_result['predicate_json'], cached_result['sql_where'], [], True
    
    # Stage 1: Natural Language → JSON Predicate (Gemini)
    try:
        predicate_json, translation_errors = translate_natural_language_to_json(logic_en, None, comparison_context)
        if translation_errors:
            errors.extend(translation_errors)
            return None, None, errors, False
        
        if not predicate_json:
            errors.append("Failed to generate JSON predicate from natural language")
            return None, None, errors, False
    except QuotaExceededError as e:
        # Re-raise for retry decorator, but format user-friendly message
        errors.append(f"Gemini API quota exceeded. Please wait a few minutes and try again.")
        logger.warning(f"Quota exceeded in translate_rule: {e}")
        raise
    
    # Stage 2: Validate JSON Predicate
    validation_errors = validate_json_predicate(predicate_json)
    if validation_errors:
        errors.extend(validation_errors)
        return None, None, errors, False
    
    # Stage 3: JSON Predicate → SQL WHERE (using existing RuleService)
    try:
        from app.services.rules import convert_json_to_sql
        sql_where = convert_json_to_sql(predicate_json, table_name)
    except Exception as e:
        errors.append(f"Failed to convert JSON to SQL: {str(e)}")
        return predicate_json, None, errors, False
    
    # Cache successful translation
    if use_cache:
        from app.engine.rule_cache import cache_translation
        cache_translation(logic_en, predicate_json, sql_where)
    
    logger.info(f"Successfully translated rule: {logic_en} → {sql_where}")
    return predicate_json, sql_where, [], True


@retry_on_quota
def generate_business_rules_summary(rules: List[Dict[str, Any]]) -> str:
    """
    Generate a one-sentence LLM summary of combined business rules.
    
    Args:
        rules: List of rule dictionaries with logic_en, node_name, etc.
    
    Returns:
        One-sentence summary of the combined rules
    """
    if not rules:
        return "No business rules defined. Calculation will use natural GL values only."
    
    try:
        model = initialize_gemini()
        
        # Build prompt with rule summaries
        rules_text = "\n".join([
            f"- {rule.get('node_name', rule.get('node_id', 'Unknown'))}: {rule.get('logic_en', 'No description')}"
            for rule in rules
        ])
        
        prompt = f"""Generate a concise one-sentence business summary of these financial rules:

{rules_text}

The summary should:
- Be executive-friendly (no technical jargon)
- Highlight the main actions (exclude, normalize, adjust, etc.)
- Mention key dimensions affected (books, strategies, desks, etc.)
- Be under 100 words

Example format: "This execution will exclude 2 internal books and normalize Strategy 'CORE' across 12 desks."

Summary:"""
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 150,
            }
        )
        
        summary = response.text.strip()
        # Remove quotes if present
        summary = summary.strip('"').strip("'")
        
        logger.info(f"Generated business rules summary: {summary}")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate business rules summary: {e}")
        # Fallback summary
        rule_count = len(rules)
        leaf_count = sum(1 for r in rules if r.get('is_leaf', False))
        return f"This execution will apply {rule_count} business rule{'' if rule_count == 1 else 's'} ({leaf_count} leaf-level, {rule_count - leaf_count} parent-level) to adjust the financial baseline."
