# Performance Analysis: Tab 3 & Tab 4 Loading (10+ seconds)

## Problem Statement
- **Tab 3**: Still takes ~10 seconds to load (down from 15-20s, but needs improvement)
- **Tab 4**: Also slow when loading results
- Both tabs call the same expensive `/results` endpoint

## Root Cause Analysis (From Terminal Logs)

### 🔴 CRITICAL ISSUE #1: Backend Recalculates Natural Rollups on EVERY Request

**Location**: `app/api/routes/calculations.py` - `get_calculation_results()` function

**Evidence from Logs**:
- Lines 224-227, 320-322, 345-346, 408-409, 463-464, 505-506, 560-561, 657-658, 755-756, 853-854
- **Every `/results` call triggers**: `[Strategy Path] Calculating rollup for use_case_id: fce60983-0328-496b-b6e1-34249ec5aa5a`
- **Each rollup does**:
  1. Loads 776 rows from `fact_pnl_use_case_3` (Lines 228, 238, 349, 410, 465, 507, 562, 659, 757, 855)
  2. Creates DataFrame with 776 rows
  3. Calculates bottom-up aggregation from depth 4 to 0
  4. Matches 11/11 nodes with non-zero values
  5. Executes 3 Math rules (NODE_4, NODE_7, NODE_8)
  6. Returns rollup totals

**Time per rollup**: ~5-7 seconds
**Total calls in logs**: 10+ rollup calculations for a single tab switch

**Code Location**:
```python
# app/api/routes/calculations.py ~Line 410-412
# This runs EVERY TIME, even if:
# - Data hasn't changed
# - A calculation run already exists
# - Same request was made seconds ago
natural_results = _calculate_strategy_rollup(
    db, use_case_id, hierarchy_dict, children_dict, leaf_nodes
)
```

---

### 🔴 CRITICAL ISSUE #2: No Caching of Natural Rollup Results

**Problem**: Natural rollup values are recalculated even when:
- The underlying fact table data hasn't changed
- The same use case is requested multiple times
- A recent calculation run exists with the same data

**Impact**: 
- Tab 3: 1-2 `/results` calls = 5-14 seconds
- Tab 4: 1 `/results` call = 5-7 seconds
- **Total wasted time**: 10-21 seconds per tab switch

---

### 🟡 ISSUE #3: Frontend Still Makes Multiple Calls (After Phase 1 Fixes)

**Tab 3**:
- ✅ Fixed: Removed duplicate freshness check useEffects
- ✅ Fixed: Added AbortController for deduplication
- ⚠️ Still happening: Multiple `/results` calls from different code paths
  - Initial load: `loadHierarchyForUseCase()` → `/results`
  - Rules loading: May trigger additional calls

**Tab 4**:
- Calls `/results` once on mount (Line 571-575 in ExecutiveDashboard.tsx)
- But the single call still takes 5-7 seconds due to backend recalculation

---

## Proposed Solutions

### 🎯 SOLUTION 1: Cache Natural Rollup Results (HIGHEST IMPACT)

**Approach**: Cache natural rollup results in memory with TTL (Time-To-Live)

**Implementation**:
1. Add in-memory cache (using Python's `functools.lru_cache` or `cachetools`)
2. Cache key: `(use_case_id, fact_table_hash, hierarchy_hash)`
3. TTL: 30 seconds (configurable)
4. Invalidate cache when:
   - New calculation run is created
   - Fact table data changes (if we can detect this)
   - Manual cache clear endpoint

**Expected Impact**:
- **First request**: 5-7 seconds (calculates and caches)
- **Subsequent requests**: <1 second (serves from cache)
- **Tab 3 improvement**: 10s → 1-2s (80-90% faster)
- **Tab 4 improvement**: 5-7s → <1s (85-90% faster)

**Files to Modify**:
- `app/api/routes/calculations.py` - Add caching wrapper around `_calculate_strategy_rollup` and `_calculate_legacy_rollup`
- `app/services/unified_pnl_service.py` - Add cache to `calculate_rollup` function

**Risk Level**: 🟢 LOW
- Easy to revert (just remove cache decorator)
- No database schema changes
- Backward compatible

---

### 🎯 SOLUTION 2: Use Saved Calculation Results When Available

**Approach**: If a recent calculation run exists, use its natural values instead of recalculating

**Current Behavior**:
- Even when `fact_calculated_results` has natural values, we still recalculate
- Code checks for `run` but still recalculates natural values

**Proposed Change**:
```python
# If we have a recent run (< 5 minutes old), use its natural values
# Only recalculate if:
# - No run exists
# - Run is older than 5 minutes
# - Explicitly requested (force_recalculate=true)
```

**Expected Impact**:
- **With recent run**: 5-7s → <1s (load from DB instead of recalculate)
- **Without run**: Still 5-7s (but that's expected)

**Files to Modify**:
- `app/api/routes/calculations.py` - Check run timestamp before recalculating

**Risk Level**: 🟡 MEDIUM
- Need to ensure saved natural values are correct
- May need to verify data freshness

---

### 🎯 SOLUTION 3: Optimize Database Queries (MEDIUM IMPACT)

**Approach**: Optimize the fact table query and aggregation

**Current Issues**:
- Loads all 776 rows every time
- Creates DataFrame every time
- Multiple passes over data

**Proposed Changes**:
1. Add database indexes on fact table (if not already present)
2. Use SQL aggregation instead of Python DataFrame operations where possible
3. Cache the fact table query result (separate from rollup cache)

**Expected Impact**:
- **Query time**: 1-2s → 0.5-1s (50% faster)
- **Total rollup time**: 5-7s → 4-6s (20-30% faster)

**Files to Modify**:
- `app/engine/waterfall.py` - Optimize `load_facts_from_use_case_3`
- `app/services/unified_pnl_service.py` - Optimize rollup calculation

**Risk Level**: 🟡 MEDIUM
- Need to verify query correctness
- May require database migration for indexes

---

### 🎯 SOLUTION 4: Frontend Request Deduplication (LOW IMPACT - Already Partially Done)

**Approach**: Further optimize frontend to prevent any duplicate calls

**Current Status**:
- ✅ AbortController added (Phase 1)
- ✅ Duplicate useEffects removed (Phase 1)
- ⚠️ May still have race conditions

**Proposed Changes**:
1. Add request queue to prevent concurrent `/results` calls
2. Share results between Tab 3 and Tab 4 if same use case
3. Prefetch results when hovering over tab (optional)

**Expected Impact**:
- **Eliminates**: 1-2 redundant calls
- **Time saved**: 5-10 seconds (if backend still slow)
- **Time saved**: <1 second (if backend is cached)

**Files to Modify**:
- `frontend/src/components/RuleEditor.tsx` - Add request queue
- `frontend/src/components/ExecutiveDashboard.tsx` - Share cache with Tab 3

**Risk Level**: 🟢 LOW
- Frontend-only changes
- Easy to revert

---

## Recommended Implementation Order

### Phase 2A: Backend Caching (HIGHEST PRIORITY)
**Time Estimate**: 2-3 hours
**Impact**: 80-90% performance improvement
**Risk**: Low
**Revert Difficulty**: Easy (remove decorator)

**Changes**:
1. Add `@lru_cache` or `cachetools.TTLCache` to rollup functions
2. Add cache invalidation on calculation runs
3. Add optional `force_recalculate` query parameter

### Phase 2B: Use Saved Results (MEDIUM PRIORITY)
**Time Estimate**: 1-2 hours
**Impact**: 50-70% improvement when runs exist
**Risk**: Medium
**Revert Difficulty**: Easy (revert conditional logic)

**Changes**:
1. Check run timestamp before recalculating
2. Use `fact_calculated_results.natural_value` if recent

### Phase 2C: Query Optimization (LOW PRIORITY)
**Time Estimate**: 3-4 hours
**Impact**: 20-30% improvement
**Risk**: Medium
**Revert Difficulty**: Medium (need to revert SQL changes)

**Changes**:
1. Add database indexes
2. Optimize SQL queries
3. Cache fact table queries

---

## Expected Performance After All Fixes

### Tab 3 (Business Rules)
- **Current**: 10 seconds
- **After Phase 2A (Caching)**: 1-2 seconds (80-90% faster)
- **After Phase 2A+B (Caching + Saved Results)**: <1 second (90-95% faster)
- **After All Phases**: <1 second consistently

### Tab 4 (Executive Dashboard)
- **Current**: 5-7 seconds
- **After Phase 2A (Caching)**: <1 second (85-90% faster)
- **After Phase 2A+B**: <0.5 seconds (90-95% faster)

---

## Rollback Plan

All changes are designed to be easily revertible:

1. **Caching**: Remove `@lru_cache` decorator → reverts to original behavior
2. **Saved Results**: Remove conditional check → always recalculates
3. **Query Optimization**: Revert SQL changes → back to original queries
4. **Frontend**: Revert component changes → back to original code

Each phase can be reverted independently without affecting others.

---

## Testing Checklist

After implementing each phase:

- [ ] Tab 3 loads in <2 seconds (Phase 2A)
- [ ] Tab 4 loads in <1 second (Phase 2A)
- [ ] Results are correct (verify against original)
- [ ] Cache invalidation works (run calculation, verify fresh results)
- [ ] No errors in console/backend logs
- [ ] Performance improvement is measurable

---

## Next Steps

1. **Review this analysis** - Confirm approach is acceptable
2. **Approve Phase 2A** - Start with backend caching (highest impact, lowest risk)
3. **Implement Phase 2A** - Add caching to rollup functions
4. **Test and measure** - Verify performance improvement
5. **Proceed to Phase 2B** - If Phase 2A isn't sufficient

