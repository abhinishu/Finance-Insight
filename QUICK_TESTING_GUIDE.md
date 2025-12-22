# Quick Testing Guide - UX & Engineering Alignment Sprint

## 🚀 Quick Start Testing

### Step 1: Data Reseeding (5 minutes)
```bash
python scripts/reseed_pnl_data.py --count 10000
```
**Verify:**
- ✅ 10,000+ rows in `fact_pnl_gold` table
- ✅ MTD = sum of daily values for each month
- ✅ YTD = sum from Jan 1 to current date

---

### Step 2: Tab 1 → Tab 2 & 3 Sync (3 minutes)
1. **Tab 1:** Create a report
   - Select measures: Daily, MTD, YTD
   - Select dimensions: Book, Strategy
   - Save report

2. **Tab 2:** Verify
   - ✅ Only selected measures displayed (Daily, MTD, YTD)
   - ✅ Hierarchy filtered by selected dimensions

3. **Tab 3:** Verify
   - ✅ Only selected measures displayed
   - ✅ Same hierarchy structure as Tab 2

---

### Step 3: Tab 3 Enhancements (10 minutes)

#### A. Rule Icons (fx)
1. Create a rule for any node
2. ✅ Verify "fx" icon appears next to node name (amber/orange)

#### B. Rule Recall
1. Select a node with an existing rule
2. ✅ Verify rule loads into editor:
   - AI Mode: Shows `logic_en` text
   - Standard Mode: Shows conditions

#### C. Multi-Node Selection
1. Select multiple nodes (Ctrl+Click or Shift+Click)
2. ✅ Verify all selected nodes highlighted
3. Create a rule
4. ✅ Verify rule applies to all selected nodes

---

### Step 4: Tree Unification (5 minutes)
1. **Tab 2:** Expand 3-4 nodes
2. **Switch to Tab 3**
3. ✅ Verify same nodes are expanded
4. **Tab 3:** Collapse one, expand another
5. **Switch back to Tab 2**
6. ✅ Verify changes reflected

---

### Step 5: Pre-Calculation Audit (5 minutes)
1. **Tab 3:** Create 2-3 rules for different nodes
2. Click **"Run Waterfall Calculation"**
3. ✅ Verify audit drawer opens
4. ✅ Verify shows:
   - All active rules listed
   - Logic description for each
   - Estimated impact (rows affected)
   - Percentage affected
5. Click **"Confirm & Calculate"**
6. ✅ Verify calculation runs

---

### Step 6: Golden Equation Verification (5 minutes)
1. **Tab 4:** Open Executive Dashboard
2. ✅ Verify columns:
   - Natural GL (Baseline)
   - Adjusted P&L (Rule-adjusted)
   - Reconciliation Plug (Natural - Adjusted)
3. ✅ Verify: **Natural = Adjusted + Plug**
4. ✅ Check all measures: Daily, MTD, YTD, PYTD

---

## ⚠️ Common Issues & Fixes

### Tab 3 Crashes
- ✅ **FIXED:** Added `loadRules` function
- ✅ **FIXED:** Safe rules Map access
- ✅ **FIXED:** Function ordering issues

### Rules Not Loading
- Check backend is running
- Verify use case is selected
- Check browser console for errors

### Tree Not Syncing
- Clear localStorage: `localStorage.clear()`
- Refresh page
- Try expanding nodes again

### Audit Drawer Not Opening
- Verify at least one rule exists with `sql_where`
- Check browser console for API errors
- Verify backend `/api/v1/rules/preview` endpoint works

---

## 📊 Testing Checklist Summary

| Feature | Quick Test | Status |
|---------|-----------|--------|
| Data Reseeding | Run script, check DB | ⬜ |
| Schema Sync | Tab 1 → Tab 2 & 3 | ⬜ |
| Rule Icons (fx) | Create rule, see icon | ⬜ |
| Rule Recall | Select node, see rule load | ⬜ |
| Multi-Node Select | Select multiple nodes | ⬜ |
| Tree Unification | Expand in Tab 2, check Tab 3 | ⬜ |
| Pre-Calculation Audit | Click calculate, see drawer | ⬜ |
| Golden Equation | Tab 4, verify math | ⬜ |

---

## 🎯 Expected Results

### ✅ All Features Working
- Tab 3 loads without crashing
- Rules display with "fx" icons
- Tree expansion syncs between tabs
- Audit drawer shows before calculation
- Golden Equation holds true

### 📝 Report Issues
If any feature doesn't work:
1. Note which feature
2. Check browser console for errors
3. Check backend logs
4. Document steps to reproduce

---

**Total Testing Time:** ~30 minutes for complete verification

**Status:** Ready for testing! 🚀

