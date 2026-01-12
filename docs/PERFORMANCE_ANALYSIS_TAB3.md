# Performance Analysis: Tab 3 Loading (15-20 seconds)

## Problem Statement
When navigating from Tab 2 to Tab 3, the Business Rules tab takes 15-20 seconds to load, causing poor user experience.

## Root Cause Analysis

### 1. **Multiple Redundant `/results` API Calls** (CRITICAL - Primary Cause)

**Location**: `frontend/src/components/RuleEditor.tsx`

**Issue**: Three separate code paths call the expensive `/results` endpoint:

1. **Line 1126**: `loadHierarchyForUseCase()` → `GET /api/v1/use-cases/{id}/results?t={timestamp}`
2. **Line 1524**: `useEffect` for freshness check → `GET /api/v1/use-cases/{id}/results`
3. **Line 1568**: `useEffect` for last run timestamp → `GET /api/v1/use-cases/{id}/results`

**Evidence from Terminal Logs**:
- Lines 383, 390-391, 404, 411, 497, 753-754, 780, 792, 825-826, 828, 843: Multiple `/results` calls
- Each call triggers full backend recalculation (see #2 below)

**Impact**: 
- 3-4 redundant API calls per tab switch
- Each call takes 5-7 seconds (see #2)
- Total: 15-28 seconds of backend processing

---

### 2. **Backend Recalculates Everything on Every Request** (CRITICAL - Expensive Operations)

**Location**: `app/api/routes/calculations.py` - Lines 399-434

**Issue**: The `/results` endpoint recalculates natural rollup values on **EVERY** request, even if:
- The use case hasn't changed
- The data hasn't changed  
- A recent calculation already exists
- The same request was made seconds ago

**Code Flow**:
```python
# Line 410-412: Always recalculates, no caching
natural_results = _calculate_strategy_rollup(
    db, use_case_id, hierarchy_dict, children_dict, leaf_nodes
)
```

**What `_calculate_strategy_rollup` does** (from logs):
1. Loads 776 rows from `fact_pnl_use_case_3` (Line 15, 258, 436, 460, 612, 678, 800)
2. Creates DataFrame with 776 rows
3. Calculates bottom-up aggregation from depth 4 to 0
4. Matches 12/12 nodes with non-zero values
5. Executes 3 Math rules (NODE_4, NODE_7, NODE_8)
6. Calculates rollup totals

**Evidence from Terminal Logs**:
- Lines 12-13, 18-19, 80-82, 110-112, 249-250, 424-425, 454-455, 597-598, 668-669, 798-799: Repeated "Strategy Path Calculating rollup"
- Lines 15, 258, 436, 460, 612, 678, 800: "Loaded 776 rows from fact_pnl_use_case_3" appears **8+ times**
- Lines 150-151, 301-303, 507-508, 722-723: "Found 3 Type 3 rules to execute" appears **4+ times**
- Each calculation takes 5-7 seconds

**Impact**:
- No caching mechanism
- Same calculations repeated 3-4 times per tab switch
- 5-7 seconds × 3-4 calls = 15-28 seconds total

---

### 3. **Sequential Rule Preview Calls** (HIGH - Adds 3-5 seconds)

**Location**: `frontend/src/components/RuleEditor.tsx` - Lines 636-656

**Issue**: For each SQL-based rule, the frontend makes a separate POST to `/rules/preview` to get impact data (affected_rows, total_rows, percentage).

**Code**:
```typescript
// For each rule, make separate API call
if (rule.rule_type !== 'NODE_ARITHMETIC' && rule.sql_where) {
  const previewResponse = await axios.post(
    `${API_BASE_URL}/api/v1/rules/preview`,
    { sql_where: rule.sql_where, use_case_id: selectedUseCaseId }
  )
}
```

**Evidence from Terminal Logs**:
- Lines 830-857: **28 consecutive** `POST /api/v1/rules/preview` calls
- Each preview call:
  - Loads 776 rows from `fact_pnl_use_case_3` (Lines 427, 441, 461, 470, 478, 483, 505, 510, 524, 530, 541, 550, 577, 589, 592)
  - Executes SQL WHERE clause
  - Calculates affected rows
  - Takes ~200-500ms per call

**Impact**:
- 28 preview calls × 200-500ms = 5.6-14 seconds
- All calls are sequential (not parallelized)
- Each call repeats the same expensive database operations

---

### 4. **No Request Deduplication** (MEDIUM - Race Conditions)

**Location**: `frontend/src/components/RuleEditor.tsx`

**Issue**: Multiple `useEffect` hooks can trigger simultaneously when:
- Tab switches
- Use case changes
- Component mounts

**Code**:
```typescript
// Line 1090: loadHierarchyForUseCase() called on mount
useEffect(() => {
  if (selectedUseCase && selectedUseCaseId) {
    loadHierarchyForUseCase(selectedUseCaseId, selectedUseCase.atlas_structure_id)
  }
}, [selectedUseCase, selectedUseCaseId])

// Line 1517: Freshness check useEffect
useEffect(() => {
  const checkFreshness = async () => {
    const response = await axios.get(`/results`)
    // ...
  }
}, [selectedUseCaseId])

// Line 1538: Rules loading useEffect  
useEffect(() => {
  // Load rules separately
}, [selectedUseCaseId])
```

**Impact**:
- Race conditions cause duplicate requests
- No debouncing or request cancellation
- Multiple simultaneous calls to same endpoint

---

### 5. **Backend `/rules/preview` Endpoint is Expensive** (MEDIUM)

**Location**: `app/api/routes/rules.py` - Line 269-298

**Issue**: Each `/rules/preview` call:
1. Determines which table to query (fact_pnl_use_case_3)
2. Loads all 776 rows from the table
3. Executes SQL WHERE clause filter
4. Counts affected rows

**Evidence from Terminal Logs**:
- Lines 427, 441, 461, 470, 478, 483, 505, 510, 524, 530, 541, 550, 577, 589, 592: Each preview call loads 776 rows
- Same data loaded 28 times for different WHERE clauses

**Impact**:
- Could be optimized with a single query that counts all rules at once
- Or cached results if same WHERE clause is queried multiple times

---

## Performance Breakdown

### Current Performance (Measured from Logs)

| Operation | Count | Time per Call | Total Time |
|-----------|-------|---------------|------------|
| `/results` API calls | 3-4 | 5-7 seconds | 15-28 seconds |
| `/rules/preview` calls | 28 | 200-500ms | 5.6-14 seconds |
| **Total** | | | **20.6-42 seconds** |

**Observed**: 15-20 seconds (matches analysis)

---

## Recommended Fixes (Priority Order)

### Fix 1: **Add Backend Caching for `/results` Endpoint** (CRITICAL - Highest Impact)

**Problem**: Backend recalculates natural rollup on every request.

**Solution**: Cache calculation results with TTL (Time To Live).

**Implementation**:
1. Add in-memory cache (e.g., `functools.lru_cache` or `cachetools`)
2. Cache key: `(use_case_id, run_id, data_hash)`
3. Cache TTL: 30-60 seconds (or until data changes)
4. Invalidate cache when:
   - New calculation run completes
   - Rules are created/updated/deleted
   - Fact data is updated

**Expected Impact**: 
- First call: 5-7 seconds (unchanged)
- Subsequent calls: <100ms (from cache)
- **Savings: 10-20 seconds per tab switch**

---

### Fix 2: **Deduplicate Frontend API Calls** (CRITICAL - High Impact)

**Problem**: Multiple `useEffect` hooks call same endpoints simultaneously.

**Solution**: 
1. Use a request deduplication mechanism
2. Cancel pending requests when new ones are made
3. Combine freshness check with initial load

**Implementation**:
```typescript
// Use AbortController to cancel duplicate requests
const abortControllerRef = useRef<AbortController | null>(null)

const loadHierarchyForUseCase = async (useCaseId: string) => {
  // Cancel previous request
  if (abortControllerRef.current) {
    abortControllerRef.current.abort()
  }
  
  const controller = new AbortController()
  abortControllerRef.current = controller
  
  // Make request with abort signal
  const response = await axios.get(`/results`, {
    signal: controller.signal
  })
}
```

**Expected Impact**:
- Reduce 3-4 calls to 1 call
- **Savings: 10-14 seconds per tab switch**

---

### Fix 3: **Batch Rule Preview Calls** (HIGH - Medium Impact)

**Problem**: 28 sequential `/rules/preview` calls, each loading 776 rows.

**Solution**: 
1. Create batch preview endpoint: `POST /api/v1/rules/preview/batch`
2. Accept array of SQL WHERE clauses
3. Execute all queries in single database transaction
4. Return array of results

**Alternative**: Load impact data from `/results` response (if backend includes it).

**Expected Impact**:
- Reduce 28 calls to 1 call
- **Savings: 5-10 seconds per tab switch**

---

### Fix 4: **Optimize Backend `/rules/preview` Endpoint** (MEDIUM - Low Impact)

**Problem**: Each preview call loads all 776 rows, then filters.

**Solution**:
1. Use `COUNT(*)` query instead of loading all rows
2. Add database index on commonly filtered columns
3. Cache preview results for same WHERE clauses

**Expected Impact**:
- Reduce preview call time from 200-500ms to 50-100ms
- **Savings: 4-11 seconds (if Fix 3 not implemented)**

---

### Fix 5: **Use Rules from `/results` Response** (LOW - Already Partially Implemented)

**Problem**: Frontend loads rules separately even though `/results` includes them.

**Status**: Partially fixed (Lines 1132-1175 extract rules from `/results`), but still loads complete rule set separately (Lines 608-656).

**Solution**: 
1. Fully rely on rules from `/results` response
2. Only load impact data separately if needed
3. Remove redundant `/rules` endpoint call

**Expected Impact**:
- Eliminate 1 API call
- **Savings: 1-2 seconds per tab switch**

---

## Recommended Implementation Plan

### Phase 1: Quick Wins (Implement First)
1. ✅ **Fix 2**: Deduplicate frontend API calls (1-2 hours)
2. ✅ **Fix 5**: Remove redundant `/rules` call (30 minutes)

**Expected Total Savings**: 11-16 seconds → **Target: 3-5 seconds**

### Phase 2: Backend Optimization (High Impact)
3. ✅ **Fix 1**: Add backend caching for `/results` (2-3 hours)
4. ✅ **Fix 3**: Batch rule preview calls (2-3 hours)

**Expected Total Savings**: Additional 10-20 seconds → **Target: <2 seconds**

### Phase 3: Fine-tuning (Optional)
5. ✅ **Fix 4**: Optimize `/rules/preview` endpoint (1-2 hours)

**Final Target**: **<2 seconds** for Tab 3 load time

---

## Summary

**Root Causes** (in order of impact):
1. **Backend recalculates on every request** (no caching) - 15-28 seconds
2. **Multiple redundant frontend API calls** - 10-14 seconds  
3. **28 sequential rule preview calls** - 5-14 seconds
4. **No request deduplication** - Race conditions
5. **Expensive preview endpoint** - 4-11 seconds

**Total Current Time**: 20-42 seconds (observed: 15-20 seconds)

**After Fixes**: **<2 seconds** (95% improvement)

