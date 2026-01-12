# Phase 1 Performance Fixes - Change Log

## Overview
Phase 1 fixes target the frontend to eliminate redundant API calls and improve Tab 3 loading performance.

## Changes Made

### Fix 2: Request Deduplication & Freshness Check Optimization
- **File**: `frontend/src/components/RuleEditor.tsx`
- **Lines Modified**: ~546, ~1103-1343, ~1572-1641
- **Changes**:
  1. **Added AbortController** (line ~546):
     - Added `abortControllerRef` to track and cancel duplicate requests
     - Prevents multiple simultaneous calls to `/results` endpoint
  
  2. **Modified `loadHierarchyForUseCase`** (lines ~1103-1343):
     - Added AbortController support to cancel previous requests when new one starts
     - Extracts freshness data (`is_outdated`, `run_timestamp`) from `/results` response
     - Updates `isCalculationOutdated` and `lastCalculated` state directly from response
     - Handles canceled requests gracefully (no error shown)
  
  3. **Removed Duplicate useEffects** (lines ~1572-1641):
     - Removed `checkFreshness` useEffect that made duplicate `/results` call
     - Removed `loadLastRun` useEffect that made another duplicate `/results` call
     - Freshness data now loaded as part of initial hierarchy load
     - **Impact**: Eliminates 2 redundant `/results` API calls per tab switch

### Fix 5: Optimize Rules Loading (Remove Redundant Preview Calls)
- **File**: `frontend/src/components/RuleEditor.tsx`
- **Lines Modified**: ~598-697
- **Changes**:
  1. **Optimized Rules Loading useEffect** (lines ~598-697):
     - Changed from loading ALL rules and ALL impact data to only loading missing rules
     - Removed 28+ `/rules/preview` calls that were made on every initial load
     - Impact data (`affected_rows`, `total_rows`, `estimatedImpact`) now loaded lazily
     - Only updates `predicate_json` if missing (for rule type detection)
     - Only adds rules that don't exist in `/results` response (rare case)
     - **Impact**: Eliminates ~28 redundant `/rules/preview` API calls, saving ~10-15 seconds

## Performance Impact

### Before Phase 1:
- **Tab 3 Load Time**: 15-20+ seconds
- **API Calls on Tab Switch**:
  - 3x `/results` calls (1 initial + 2 duplicate freshness checks)
  - 1x `/rules` call
  - 28+ `/rules/preview` calls (for impact data)
  - **Total**: ~32 API calls

### After Phase 1:
- **Expected Tab 3 Load Time**: 3-5 seconds (estimated 70-80% improvement)
- **API Calls on Tab Switch**:
  - 1x `/results` call (with freshness data included)
  - 1x `/rules` call (only for missing rules, rare)
  - 0x `/rules/preview` calls (lazy loaded when audit drawer opens)
  - **Total**: ~2 API calls

## Files Modified
1. `frontend/src/components/RuleEditor.tsx`

## Testing Checklist
- [ ] Navigate from Tab 2 to Tab 3 - should load in <5 seconds
- [ ] Verify rules are displayed correctly (from `/results` response)
- [ ] Verify freshness indicator works (is_outdated flag)
- [ ] Verify last calculated timestamp displays
- [ ] Open audit drawer - impact data should load on demand
- [ ] Verify no console errors related to canceled requests

## Rollback Instructions
If issues occur, revert changes using:
```bash
git restore frontend/src/components/RuleEditor.tsx
```

## Phase 1.5 Optimizations (Additional)

### Changes Made:
1. **Reduced Rules Loading Delay** (line ~685):
   - Reduced timeout from 500ms to 100ms
   - Rules are already loaded from `/results`, so minimal delay is sufficient
   - **Impact**: Saves ~400ms per tab switch

2. **Prevent Duplicate Re-flattening** (lines ~931-952):
   - Added refs to track last flattened state (`lastFlattenedRulesSizeRef`, `lastFlattenedHierarchyLengthRef`)
   - Only re-flatten if rules or hierarchy actually changed
   - **Impact**: Eliminates 2-3 unnecessary re-flattening operations

3. **Removed Redundant Re-flattening in Rules useEffect** (line ~655):
   - Removed re-flattening from rules loading useEffect
   - Re-flattening is now handled by the dedicated useEffect that watches rules changes
   - **Impact**: Prevents duplicate flattening operations

### Expected Performance After Phase 1.5:
- **Tab 3 Load Time**: 5-8 seconds (down from 10+ seconds)
- **Re-flattening Operations**: 1 (down from 3-4)
- **Total Delay from Rules Loading**: 100ms (down from 500ms)

## Notes
- Impact data (affected_rows) is now loaded lazily when the audit drawer is opened
- This means audit summary may show 0s initially, but will populate when drawer opens
- If audit summary needs to be visible immediately, we can add a separate lazy loading mechanism
- Backend `/results` endpoint performance may still be a bottleneck (5-8 seconds) - consider Phase 2 optimizations

