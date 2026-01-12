"""
PHASE 2A: Rollup Result Cache
In-memory cache for natural rollup calculations to improve performance.

Cache Strategy:
- TTL: 30 seconds (configurable)
- Cache Key: (use_case_id, hierarchy_hash)
- Invalidation: On calculation run creation or manual clear
"""

import time
import hashlib
from typing import Dict, Optional, Tuple, Any
from uuid import UUID
from decimal import Decimal

logger = None
try:
    import logging
    logger = logging.getLogger(__name__)
except:
    pass

# In-memory cache: {cache_key: (result, timestamp)}
_rollup_cache: Dict[str, Tuple[Dict[str, Dict[str, Decimal]], float]] = {}
_cache_ttl: float = 30.0  # 30 seconds TTL


def _get_cache_key(use_case_id: UUID, hierarchy_dict: Dict) -> str:
    """
    Generate cache key from use_case_id and hierarchy structure.
    
    Args:
        use_case_id: Use case UUID
        hierarchy_dict: Hierarchy dictionary (used to detect structure changes)
    
    Returns:
        Cache key string
    """
    # Create a hash of the hierarchy structure (node_ids and their relationships)
    # This ensures cache is invalidated if hierarchy changes
    hierarchy_str = str(sorted([
        (node_id, node.parent_node_id if hasattr(node, 'parent_node_id') else None)
        for node_id, node in hierarchy_dict.items()
    ]))
    hierarchy_hash = hashlib.md5(hierarchy_str.encode()).hexdigest()[:8]
    
    return f"rollup:{use_case_id}:{hierarchy_hash}"


def get_cached_rollup(
    use_case_id: UUID,
    hierarchy_dict: Dict,
    force_recalculate: bool = False
) -> Optional[Dict[str, Dict[str, Decimal]]]:
    """
    Get cached rollup result if available and not expired.
    
    Args:
        use_case_id: Use case UUID
        hierarchy_dict: Hierarchy dictionary
        force_recalculate: If True, skip cache and return None
    
    Returns:
        Cached result dict or None if not cached/expired
    """
    if force_recalculate:
        return None
    
    cache_key = _get_cache_key(use_case_id, hierarchy_dict)
    current_time = time.time()
    
    if cache_key in _rollup_cache:
        result, cached_time = _rollup_cache[cache_key]
        age = current_time - cached_time
        
        if age < _cache_ttl:
            if logger:
                logger.info(f"[Rollup Cache] Cache HIT for {use_case_id} (age: {age:.1f}s)")
            return result
        else:
            # Cache expired, remove it
            del _rollup_cache[cache_key]
            if logger:
                logger.info(f"[Rollup Cache] Cache EXPIRED for {use_case_id} (age: {age:.1f}s)")
    
    if logger:
        logger.info(f"[Rollup Cache] Cache MISS for {use_case_id}")
    return None


def set_cached_rollup(
    use_case_id: UUID,
    hierarchy_dict: Dict,
    result: Dict[str, Dict[str, Decimal]]
) -> None:
    """
    Store rollup result in cache.
    
    Args:
        use_case_id: Use case UUID
        hierarchy_dict: Hierarchy dictionary
        result: Rollup result dictionary
    """
    cache_key = _get_cache_key(use_case_id, hierarchy_dict)
    current_time = time.time()
    
    _rollup_cache[cache_key] = (result, current_time)
    
    if logger:
        logger.info(f"[Rollup Cache] Cached rollup for {use_case_id} (key: {cache_key})")


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
        count = len(_rollup_cache)
        _rollup_cache.clear()
        if logger:
            logger.info(f"[Rollup Cache] Cleared all cache entries ({count} entries)")
        return count
    else:
        # Clear only entries for this use case
        keys_to_remove = [
            key for key in _rollup_cache.keys()
            if key.startswith(f"rollup:{use_case_id}:")
        ]
        for key in keys_to_remove:
            del _rollup_cache[key]
        
        if logger:
            logger.info(f"[Rollup Cache] Cleared {len(keys_to_remove)} cache entries for use_case_id {use_case_id}")
        return len(keys_to_remove)


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics for monitoring.
    
    Returns:
        Dictionary with cache statistics
    """
    current_time = time.time()
    total_entries = len(_rollup_cache)
    expired_entries = 0
    valid_entries = 0
    
    for key, (result, cached_time) in _rollup_cache.items():
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

