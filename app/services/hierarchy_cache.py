"""
PHASE 2C: Hierarchy Cache
In-memory cache for hierarchy loading to improve performance.

Cache Strategy:
- TTL: 120 seconds (configurable)
- Cache Key: use_case_id
- Invalidation: On structure modification or manual clear
"""

import time
from typing import Dict, Optional, Tuple, List, Any
from uuid import UUID

logger = None
try:
    import logging
    logger = logging.getLogger(__name__)
except:
    pass

# In-memory cache: {cache_key: (hierarchy_data, timestamp)}
# hierarchy_data is a tuple: (hierarchy_dict, children_dict, leaf_nodes)
_hierarchy_cache: Dict[str, Tuple[Tuple[Dict, Dict, List], float]] = {}
_cache_ttl: float = 120.0  # 120 seconds TTL (hierarchy rarely changes)


def _get_cache_key(use_case_id: UUID) -> str:
    """
    Generate cache key from use_case_id.
    
    Args:
        use_case_id: Use case UUID
    
    Returns:
        Cache key string
    """
    return f"hierarchy:{use_case_id}"


def get_cached_hierarchy(
    use_case_id: UUID,
    force_reload: bool = False
) -> Optional[Tuple[Dict, Dict, List]]:
    """
    Get cached hierarchy data if available and not expired.
    
    Args:
        use_case_id: Use case UUID
        force_reload: If True, skip cache and return None
    
    Returns:
        Cached hierarchy tuple (hierarchy_dict, children_dict, leaf_nodes) or None if not cached/expired
    """
    if force_reload:
        return None
    
    cache_key = _get_cache_key(use_case_id)
    current_time = time.time()
    
    if cache_key in _hierarchy_cache:
        hierarchy_data, cached_time = _hierarchy_cache[cache_key]
        age = current_time - cached_time
        
        if age < _cache_ttl:
            if logger:
                logger.info(f"[Hierarchy Cache] Cache HIT for {use_case_id} (age: {age:.1f}s)")
            return hierarchy_data
        else:
            # Cache expired, remove it
            del _hierarchy_cache[cache_key]
            if logger:
                logger.info(f"[Hierarchy Cache] Cache EXPIRED for {use_case_id} (age: {age:.1f}s)")
    
    if logger:
        logger.info(f"[Hierarchy Cache] Cache MISS for {use_case_id}")
    return None


def set_cached_hierarchy(
    use_case_id: UUID,
    hierarchy_dict: Dict,
    children_dict: Dict,
    leaf_nodes: List
) -> None:
    """
    Store hierarchy data in cache.
    
    Args:
        use_case_id: Use case UUID
        hierarchy_dict: Dictionary mapping node_id -> node data
        children_dict: Dictionary mapping parent_node_id -> list of children node_ids
        leaf_nodes: List of leaf node_ids
    """
    cache_key = _get_cache_key(use_case_id)
    current_time = time.time()
    
    hierarchy_data = (hierarchy_dict, children_dict, leaf_nodes)
    _hierarchy_cache[cache_key] = (hierarchy_data, current_time)
    
    if logger:
        logger.info(
            f"[Hierarchy Cache] Cached hierarchy for {use_case_id} "
            f"(key: {cache_key}, nodes: {len(hierarchy_dict)}, leaf_nodes: {len(leaf_nodes)})"
        )


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
        count = len(_hierarchy_cache)
        _hierarchy_cache.clear()
        if logger:
            logger.info(f"[Hierarchy Cache] Cleared all cache entries ({count} entries)")
        return count
    else:
        # Clear only entries for this use case
        cache_key = _get_cache_key(use_case_id)
        if cache_key in _hierarchy_cache:
            del _hierarchy_cache[cache_key]
            if logger:
                logger.info(f"[Hierarchy Cache] Cleared cache entry for use_case_id {use_case_id}")
            return 1
        else:
            if logger:
                logger.info(f"[Hierarchy Cache] No cache entry found for use_case_id {use_case_id}")
            return 0


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics for monitoring.
    
    Returns:
        Dictionary with cache statistics
    """
    current_time = time.time()
    total_entries = len(_hierarchy_cache)
    expired_entries = 0
    valid_entries = 0
    
    for key, (hierarchy_data, cached_time) in _hierarchy_cache.items():
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

