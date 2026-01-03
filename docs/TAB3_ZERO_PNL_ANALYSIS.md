# Tab 3 Zero P&L Analysis: Commissions (Non Swap)

## Problem Statement

**Issue:** Tab 3 (Business Rules) shows Daily P&L = **0.00** for "Commissions (Non Swap)"  
**Expected:** Tab 3 should show Daily P&L = **19,999.79** (same as Tab 4 Original Daily P&L)

**Tab 4 (Executive View):** Shows Original Daily P&L = **19,999.79** ✅

---

## Root Cause

### The Bug

**File:** `frontend/src/components/RuleEditor.tsx`  
**Line:** 920

**Current Code:**
```typescript
daily_pnl: node.adjusted_value?.daily?.toString() || node.natural_value?.daily?.toString() || '0',
```

**Problem:**
- When `adjusted_value.daily = 0`, it becomes the string `"0"`
- String `"0"` is **truthy** in JavaScript
- The `||` operator stops at the first truthy value
- Fallback to `natural_value` **never executes**
- Result: `daily_pnl = "0"` ❌

### Why Tab 4 Works

**Tab 4 uses `natural_value` directly:**
- `natural_value.daily = "19999.79"` ✅
- No fallback logic needed

### Why Tab 3 Fails

**Tab 3 uses `adjusted_value` first:**
- `adjusted_value.daily = "0"` (rule returns 0 because `strategy = 'CORE'` doesn't exist)
- String `"0"` is truthy → fallback never happens
- Result: `daily_pnl = "0"` ❌

---

## Data Flow Analysis

### API Response (`/api/v1/use-cases/{id}/results`)

**For Commissions (Non Swap) (NODE_5):**
```json
{
  "node_id": "NODE_5",
  "node_name": "Commissions (Non Swap)",
  "natural_value": {
    "daily": "19999.79"  ✅ (from natural rollup)
  },
  "adjusted_value": {
    "daily": "0.00"  ❌ (rule returns 0)
  },
  "plug": {
    "daily": "19999.79"
  },
  "is_override": true
}
```

### Tab 3 Processing

**Line 920:**
```typescript
daily_pnl: node.adjusted_value?.daily?.toString() || node.natural_value?.daily?.toString() || '0'
```

**Execution:**
1. `node.adjusted_value?.daily` = `"0.00"` ✅ (exists)
2. `.toString()` = `"0"` ✅ (converts to string)
3. `"0" || ...` = `"0"` ❌ (truthy, stops here)
4. `natural_value` never checked ❌
5. Result: `daily_pnl = "0"` ❌

### Tab 4 Processing

**Uses `natural_value` directly:**
- `natural_value.daily = "19999.79"` ✅
- Displays: **19,999.79** ✅

---

## The JavaScript Truthiness Issue

**In JavaScript:**
- `"0"` is **truthy** (non-empty string)
- `0` is **falsy** (number zero)
- `"0" || "19999.79"` evaluates to `"0"` (first truthy value)

**The Fix:**
- Need to check if value is **meaningful** (not just "0")
- OR always use `natural_value` for Tab 3 (since it shows "Original" values)

---

## Recommended Fix

### Option 1: Always Use Natural Value (Recommended)

**Tab 3 should show "Original" P&L values, not "Adjusted" values.**

```typescript
// Line 920-922 in RuleEditor.tsx
daily_pnl: node.natural_value?.daily?.toString() || '0',
mtd_pnl: node.natural_value?.mtd?.toString() || '0',
ytd_pnl: node.natural_value?.ytd?.toString() || '0',
```

**Pros:**
- Matches Tab 4 behavior (shows Original values)
- Simple and clear
- No truthiness issues

**Cons:**
- Changes current behavior (was showing Adjusted)

### Option 2: Check if Adjusted is Meaningful

```typescript
const adjustedDaily = parseFloat(node.adjusted_value?.daily || '0');
const naturalDaily = parseFloat(node.natural_value?.daily || '0');
daily_pnl: (adjustedDaily !== 0 ? adjustedDaily : naturalDaily).toString(),
```

**Pros:**
- Preserves intent to show Adjusted when available
- Handles zero case correctly

**Cons:**
- More complex logic
- Still might not match user expectation (Tab 3 should show Original)

### Option 3: Use Natural When Adjusted is Zero

```typescript
const adjusted = node.adjusted_value?.daily;
const natural = node.natural_value?.daily;
daily_pnl: (adjusted && parseFloat(adjusted) !== 0 ? adjusted : natural)?.toString() || '0',
```

**Pros:**
- Shows Adjusted when non-zero
- Falls back to Natural when Adjusted is zero

**Cons:**
- Complex logic
- Might confuse users (inconsistent behavior)

---

## Verification

**Current State:**
- Tab 3: Shows `adjusted_value = 0` → Displays **0.00** ❌
- Tab 4: Shows `natural_value = 19999.79` → Displays **19,999.79** ✅

**After Fix (Option 1):**
- Tab 3: Shows `natural_value = 19999.79` → Displays **19,999.79** ✅
- Tab 4: Shows `natural_value = 19999.79` → Displays **19,999.79** ✅
- **Consistent!** ✅

---

## Summary

| Component | Field Used | Value | Display | Status |
|-----------|------------|-------|---------|--------|
| **Tab 3** | `adjusted_value.daily` | `"0"` (truthy) | **0.00** | ❌ Wrong |
| **Tab 4** | `natural_value.daily` | `"19999.79"` | **19,999.79** | ✅ Correct |

**Root Cause:** JavaScript truthiness - string `"0"` prevents fallback to `natural_value`

**Fix:** Use `natural_value` directly for Tab 3 (Option 1 recommended)

