"""
Rule Cache Module - Caches GenAI translations to reduce API costs.
Stores successful translations for 30 days.
"""

import hashlib
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# In-memory cache (in production, use Redis or similar)
_translation_cache: Dict[str, Dict[str, Any]] = {}

# Cache TTL: 30 days in seconds
CACHE_TTL_SECONDS = 30 * 24 * 60 * 60


def _normalize_logic_en(logic_en: str) -> str:
    """
    Normalize natural language input for cache key generation.
    Removes extra whitespace and converts to lowercase.
    
    Args:
        logic_en: Natural language description
    
    Returns:
        Normalized string
    """
    return ' '.join(logic_en.lower().split())


def _generate_cache_key(logic_en: str) -> str:
    """
    Generate cache key from natural language input.
    
    Args:
        logic_en: Natural language description
    
    Returns:
        Cache key (MD5 hash)
    """
    normalized = _normalize_logic_en(logic_en)
    return hashlib.md5(normalized.encode()).hexdigest()


def get_cached_translation(logic_en: str) -> Optional[Dict[str, Any]]:
    """
    Get cached translation if available and not expired.
    
    Args:
        logic_en: Natural language description
    
    Returns:
        Cached result dictionary with 'predicate_json' and 'sql_where', or None
    """
    cache_key = _generate_cache_key(logic_en)
    cached_entry = _translation_cache.get(cache_key)
    
    if not cached_entry:
        return None
    
    # Check if cache entry is expired
    current_time = time.time()
    if current_time - cached_entry['timestamp'] > CACHE_TTL_SECONDS:
        # Remove expired entry
        del _translation_cache[cache_key]
        logger.debug(f"Cache entry expired for: {logic_en}")
        return None
    
    logger.debug(f"Cache hit for: {logic_en}")
    return {
        'predicate_json': cached_entry['predicate_json'],
        'sql_where': cached_entry['sql_where']
    }


def cache_translation(
    logic_en: str,
    predicate_json: Dict[str, Any],
    sql_where: str
):
    """
    Cache a successful translation.
    
    Args:
        logic_en: Natural language description
        predicate_json: Generated JSON predicate
        sql_where: Generated SQL WHERE clause
    """
    cache_key = _generate_cache_key(logic_en)
    
    _translation_cache[cache_key] = {
        'predicate_json': predicate_json,
        'sql_where': sql_where,
        'timestamp': time.time(),
        'original_logic_en': logic_en  # Store for debugging
    }
    
    logger.debug(f"Cached translation for: {logic_en}")
    
    # Optional: Log cache size (for monitoring)
    if len(_translation_cache) % 10 == 0:
        logger.info(f"Translation cache size: {len(_translation_cache)} entries")


def clear_cache():
    """
    Clear all cached translations.
    Useful for testing or cache invalidation.
    """
    global _translation_cache
    count = len(_translation_cache)
    _translation_cache.clear()
    logger.info(f"Cleared translation cache ({count} entries)")


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    current_time = time.time()
    valid_entries = sum(
        1 for entry in _translation_cache.values()
        if current_time - entry['timestamp'] <= CACHE_TTL_SECONDS
    )
    expired_entries = len(_translation_cache) - valid_entries
    
    return {
        'total_entries': len(_translation_cache),
        'valid_entries': valid_entries,
        'expired_entries': expired_entries,
        'cache_ttl_days': CACHE_TTL_SECONDS / (24 * 60 * 60)
    }

