"""
PHASE 2C: Rules Cache
In-memory cache for rules loading to improve performance.

Cache Strategy:
- TTL: 60 seconds (configurable)
- Cache Key: use_case_id
- Invalidation: On rule create/update/delete or manual clear
"""

import time
from typing import Dict, Optional, Tuple, Any, List
from uuid import UUID

logger = None
try:
    import logging
    logger = logging.getLogger(__name__)
except:
    pass

# In-memory cache: {cache_key: (rules_data, timestamp)}
# rules_data is a list of Row objects or dicts from the database query
_rules_cache: Dict[str, Tuple[List[Any], float]] = {}
_cache_ttl: float = 60.0  # 60 seconds TTL


def _get_cache_key(use_case_id: UUID) -> str:
    """
    Generate cache key from use_case_id.
    
    Args:
        use_case_id: Use case UUID
    
    Returns:
        Cache key string
    """
    return f"rules:{use_case_id}"


def get_cached_rules(
    use_case_id: UUID,
    force_reload: bool = False
) -> Optional[List[Any]]:
    """
    Get cached rules data if available and not expired.
    
    Args:
        use_case_id: Use case UUID
        force_reload: If True, skip cache and return None
    
    Returns:
        Cached rules data list or None if not cached/expired
    """
    if force_reload:
        return None
    
    cache_key = _get_cache_key(use_case_id)
    current_time = time.time()
    
    if cache_key in _rules_cache:
        rules_data, cached_time = _rules_cache[cache_key]
        age = current_time - cached_time
        
        if age < _cache_ttl:
            if logger:
                logger.info(f"[Rules Cache] Cache HIT for {use_case_id} (age: {age:.1f}s)")
            return rules_data
        else:
            # Cache expired, remove it
            del _rules_cache[cache_key]
            if logger:
                logger.info(f"[Rules Cache] Cache EXPIRED for {use_case_id} (age: {age:.1f}s)")
    
    if logger:
        logger.info(f"[Rules Cache] Cache MISS for {use_case_id}")
    return None


def set_cached_rules(
    use_case_id: UUID,
    rules_data: List[Any]
) -> None:
    """
    Store rules data in cache.
    
    Args:
        use_case_id: Use case UUID
        rules_data: Rules data list from database query
    """
    cache_key = _get_cache_key(use_case_id)
    current_time = time.time()
    
    _rules_cache[cache_key] = (rules_data, current_time)
    
    if logger:
        logger.info(f"[Rules Cache] Cached rules for {use_case_id} (key: {cache_key}, count: {len(rules_data)})")


def invalidate_cache(use_case_id: Optional[UUID] = None) -> int:
    """
    Invalidate cache entries.
    
    Args:
        use_case_id: If provided, only invalidate entries for this use case.
                     If None, invalidate all entries.
    
    Returns:
        Number of cache entries invalidated
    """
    if use_case_id is None:
        # Clear all cache
        count = len(_rules_cache)
        _rules_cache.clear()
        if logger:
            logger.info(f"[Rules Cache] Cleared all cache entries ({count} entries)")
        return count
    else:
        # Clear only entries for this use case
        cache_key = _get_cache_key(use_case_id)
        if cache_key in _rules_cache:
            del _rules_cache[cache_key]
            if logger:
                logger.info(f"[Rules Cache] Cleared cache entry for use_case_id {use_case_id}")
            return 1
        else:
            if logger:
                logger.info(f"[Rules Cache] No cache entry found for use_case_id {use_case_id}")
            return 0


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics for monitoring.
    
    Returns:
        Dictionary with cache statistics
    """
    current_time = time.time()
    total_entries = len(_rules_cache)
    expired_entries = 0
    valid_entries = 0
    
    for key, (rules_data, cached_time) in _rules_cache.items():
        age = current_time - cached_time
        if age >= _cache_ttl:
            expired_entries += 1
        else:
            valid_entries += 1
    
    return {
        "total_entries": total_entries,
        "valid_entries": valid_entries,
        "expired_entries": expired_entries,
        "ttl_seconds": _cache_ttl
    }

