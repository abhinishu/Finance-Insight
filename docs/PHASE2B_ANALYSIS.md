# Phase 2B: Performance Analysis & Next Steps

## Analysis of Terminal Logs

### ✅ What's Working (Cache is Active)
1. **Cache HITs are working**: Multiple `[Rollup Cache] Cache HIT` messages show cache is being used
2. **Rollup calculations are cached**: After first calculation, subsequent requests use cache (age: 1.7s, 2.1s, 2.5s, etc.)
3. **Cache expiration is working**: One entry expired after 167.2s and was recalculated

### ❌ Remaining Bottlenecks

#### 1. **Redundant `get_unified_pnl()` Call** (HIGH IMPACT)
**Location**: `app/api/routes/calculations.py` line ~401

**Problem**: 
- `get_unified_pnl()` is called separately to get baseline totals
- This executes a **full SQL query** even when rollup is cached
- The rollup results already contain all the data needed to calculate totals
- This is redundant work that happens on EVERY request

**Evidence from logs**:
```
Line 182-186: get_unified_pnl called → SQL query executed
Line 243-248: get_unified_pnl called → SQL query executed  
Line 305-309: get_unified_pnl called → SQL query executed
Line 366-370: get_unified_pnl called → SQL query executed
Line 428-432: get_unified_pnl called → SQL query executed
```

**Impact**: Each `get_unified_pnl()` call takes ~100-200ms (SQL query + processing)

**Solution**: Calculate totals from cached `natural_results` instead of calling `get_unified_pnl()`

---

#### 2. **Math Rules Executed on Every Request** (MEDIUM IMPACT)
**Location**: `app/services/unified_pnl_service.py` (called from rollup functions)

**Problem**:
- Math Rules (Type 3) are executed even when using cached rollup
- Logs show: `[Math Rules] Found 4 Type 3 rules to execute` on every request
- These rules process the same data repeatedly

**Evidence from logs**:
```
Line 151-167: Math Rules executed (first request)
Line 212-228: Math Rules executed (cached request)
Line 274-290: Math Rules executed (cached request)
Line 335-351: Math Rules executed (cached request)
Line 397-413: Math Rules executed (cached request)
```

**Impact**: Math Rules processing takes ~50-100ms per request

**Solution Options**:
- **Option A**: Cache Math Rules results separately (if rules don't change)
- **Option B**: Move Math Rules execution to calculation run (not on every `/results` call)
- **Option C**: Only execute Math Rules when data actually changes

---

#### 3. **Multiple `/results` Calls from Frontend** (LOW-MEDIUM IMPACT)
**Evidence from logs**:
- Multiple `GET /api/v1/use-cases/{id}/results` requests
- Multiple `GET /api/v1/use-cases/{id}/rules` requests

**Status**: This was addressed in Phase 1, but may need further optimization

---

## Recommended Fixes (Priority Order)

### **Fix 1: Eliminate Redundant `get_unified_pnl()` Call** (HIGHEST IMPACT)
**Estimated Speedup**: 100-200ms per request

**Approach**: 
- Calculate baseline totals from `natural_results` dictionary
- Sum up `daily`, `mtd`, `ytd` from root nodes
- Only call `get_unified_pnl()` if `natural_results` is empty (fallback)

**Code Change**:
```python
# Instead of:
baseline_pnl = get_unified_pnl(db, use_case_id, pnl_date=None, scenario='ACTUAL')

# Do:
if natural_results:
    # Calculate totals from cached rollup results
    root_nodes = [node_id for node_id, node in hierarchy_dict.items() 
                  if node.parent_node_id is None]
    baseline_pnl = {
        'daily_pnl': sum(natural_results.get(node_id, {}).get('daily', Decimal('0')) 
                        for node_id in root_nodes),
        'mtd_pnl': sum(natural_results.get(node_id, {}).get('mtd', Decimal('0')) 
                      for node_id in root_nodes),
        'ytd_pnl': sum(natural_results.get(node_id, {}).get('ytd', Decimal('0')) 
                      for node_id in root_nodes)
    }
else:
    # Fallback to get_unified_pnl if rollup failed
    baseline_pnl = get_unified_pnl(db, use_case_id, pnl_date=None, scenario='ACTUAL')
```

---

### **Fix 2: Cache Math Rules Results** (MEDIUM IMPACT)
**Estimated Speedup**: 50-100ms per request

**Approach**:
- Math Rules operate on `natural_results` which is already cached
- Cache the Math Rules output separately
- Invalidate when rules change or when rollup cache is invalidated

**Alternative**: Move Math Rules execution to calculation run phase (not on every `/results` call)

---

### **Fix 3: Increase Cache TTL** (LOW IMPACT, EASY)
**Current**: 30 seconds
**Suggested**: 60-120 seconds

**Rationale**: 
- Natural rollup values don't change frequently
- Only change when fact tables are updated or calculation runs
- Longer TTL reduces cache misses

---

## Expected Performance After Fixes

### Current (After Phase 2A):
- **First request**: 5-7 seconds
- **Cached requests**: ~500ms-1s (still has `get_unified_pnl()` overhead)

### After Fix 1 (Eliminate `get_unified_pnl()`):
- **First request**: 5-7 seconds (unchanged)
- **Cached requests**: ~200-400ms (50-60% faster)

### After Fix 1 + Fix 2 (Cache Math Rules):
- **First request**: 5-7 seconds (unchanged)
- **Cached requests**: ~100-200ms (80-90% faster)

### After All Fixes:
- **First request**: 5-7 seconds
- **Cached requests**: <200ms (90%+ faster than original)

---

## Implementation Plan

### Phase 2B.1: Fix 1 (Eliminate `get_unified_pnl()`)
- **Risk**: Low (simple calculation from existing data)
- **Effort**: 30 minutes
- **Impact**: High (100-200ms per request)

### Phase 2B.2: Fix 2 (Cache Math Rules)
- **Risk**: Medium (need to ensure rules are invalidated correctly)
- **Effort**: 1-2 hours
- **Impact**: Medium (50-100ms per request)

### Phase 2B.3: Fix 3 (Increase TTL)
- **Risk**: Very Low (simple config change)
- **Effort**: 5 minutes
- **Impact**: Low (reduces cache misses)

---

## Next Steps

1. **Immediate**: Implement Fix 1 (highest impact, lowest risk)
2. **Short-term**: Implement Fix 2 (if Fix 1 doesn't provide enough speedup)
3. **Optional**: Implement Fix 3 (easy win)

Would you like me to proceed with Fix 1 first?

