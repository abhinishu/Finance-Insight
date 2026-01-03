# Rule Editor Issues - Root Cause Analysis

## 🔍 Issue Summary

The user reported three issues when trying to edit the "Swap Commission" rule:

1. **Default Mode Issue**: Modal opens in AI Mode by default and doesn't show existing rule
2. **Missing Rule in Standard Mode**: When switching to Standard Mode, existing rule is not displayed
3. **Missing Process_2 Field**: Process_2 field is not available in the dropdown for Use Case 3

---

## 📊 Issue 1: Default Mode & Missing Existing Rule Display

### Root Cause Analysis

**Location:** `frontend/src/components/RuleEditor.tsx`

**Problem 1.1: Default Mode Initialization**
- **Line 497**: `const [editorMode, setEditorMode] = useState<'ai' | 'standard'>('ai')`
- **Issue**: The editor always defaults to `'ai'` mode, regardless of whether an existing rule exists
- **Impact**: When opening "Manage Rule", users see AI Mode even if the rule was created in Standard Mode

**Problem 1.2: Rule Loading Timing**
- **Lines 2103-2152**: Rule loading logic is in `onSelectionChanged` callback
- **Line 3055**: Modal opens with `setModalOpen(true)` but doesn't trigger rule loading
- **Issue**: The rule loading happens when a node is selected, but if the modal opens before the rule is fully loaded, or if the user switches modes, the rule data may not be available
- **Impact**: Existing rule is not displayed when modal opens

**Problem 1.3: Mode Switching Loses Rule Data**
- **Lines 3189-3192**: When toggling between AI and Standard Mode, `setRulePreview(null)` is called
- **Issue**: This clears the rule preview, but doesn't preserve the existing rule data
- **Impact**: If user switches modes, they lose the existing rule context

### Expected Behavior

1. When opening "Manage Rule" for a node with an existing rule:
   - **If rule has `predicate_json`**: Default to Standard Mode and populate conditions
   - **If rule has `logic_en` but no `predicate_json`**: Default to AI Mode and populate prompt
   - **If rule has `rule_expression`**: Default to Standard Mode (Math) and populate formula

2. When switching modes:
   - Preserve existing rule data
   - If switching from AI to Standard and rule has `predicate_json`, populate conditions
   - If switching from Standard to AI and rule has `logic_en`, populate prompt

### Recommended Fix

**Step 1: Smart Default Mode Detection**
```typescript
// When modal opens, check existing rule and set appropriate mode
useEffect(() => {
  if (modalOpen && selectedNodes.length === 1) {
    const node = selectedNodes[0]
    if (node.hasRule && node.rule) {
      const rule = node.rule
      
      // Determine default mode based on rule type
      if (rule.rule_type === 'NODE_ARITHMETIC' && rule.rule_expression) {
        setEditorMode('standard')
        setStandardRuleType('math')
        setMathFormula(rule.rule_expression)
      } else if (rule.predicate_json) {
        // Standard Mode Filter rule - default to Standard Mode
        setEditorMode('standard')
        setStandardRuleType('filter')
        setSelectedMeasure(rule.measure_name || 'daily_pnl')
        // Load conditions
        const conditions: RuleCondition[] = []
        if (rule.predicate_json.conditions) {
          rule.predicate_json.conditions.forEach((cond: any) => {
            conditions.push({
              field: cond.field || '',
              operator: cond.operator || 'equals',
              value: cond.value || ''
            })
          })
        }
        if (conditions.length > 0) {
          setConditions(conditions)
        }
      } else if (rule.logic_en) {
        // AI Mode rule - default to AI Mode
        setEditorMode('ai')
        setAiPrompt(rule.logic_en)
      }
      
      // Load preview
      if (rule.sql_where) {
        setRulePreview({
          logic_en: rule.logic_en,
          sql_where: rule.sql_where,
          predicate_json: rule.predicate_json,
          translation_successful: true
        })
      }
    } else {
      // No existing rule - default to Standard Mode (as user requested)
      setEditorMode('standard')
      setStandardRuleType('filter')
    }
  }
}, [modalOpen, selectedNodes])
```

**Step 2: Preserve Rule Data When Switching Modes**
```typescript
// Update mode toggle to preserve rule data
onChange={(e) => {
  const newMode = e.target.checked ? 'ai' : 'standard'
  
  // Before switching, save current rule data
  const currentNode = selectedNodes[0]
  if (currentNode?.hasRule && currentNode?.rule) {
    const rule = currentNode.rule
    
    if (newMode === 'standard' && rule.predicate_json) {
      // Switching to Standard Mode - load conditions
      setStandardRuleType('filter')
      setSelectedMeasure(rule.measure_name || 'daily_pnl')
      const conditions: RuleCondition[] = []
      if (rule.predicate_json.conditions) {
        rule.predicate_json.conditions.forEach((cond: any) => {
          conditions.push({
            field: cond.field || '',
            operator: cond.operator || 'equals',
            value: cond.value || ''
          })
        })
      }
      if (conditions.length > 0) {
        setConditions(conditions)
      }
    } else if (newMode === 'ai' && rule.logic_en) {
      // Switching to AI Mode - load prompt
      setAiPrompt(rule.logic_en)
    }
  }
  
  setEditorMode(newMode)
  // Don't clear rulePreview - preserve it
}}
```

---

## 📊 Issue 2: Missing Process_2 Field in Dropdown

### Root Cause Analysis

**Location:** `app/api/routes/use_cases.py` lines 315-322

**Problem:**
The schema endpoint for Use Case 3 (`fact_pnl_use_case_3`) only returns 4 fields:
- `strategy`
- `book`
- `cost_center`
- `effective_date`

**Missing Fields:**
- `process_1` (exists in table)
- `process_2` (exists in table - user needs this!)

**Table Schema Verification:**
From `app/models.py` lines 328-351, `FactPnlUseCase3` has:
- `cost_center`
- `division`
- `business_area`
- `product_line`
- `strategy`
- `process_1` ⚠️ **MISSING**
- `process_2` ⚠️ **MISSING** (User needs this!)
- `book`

### Expected Behavior

The schema endpoint should return ALL dimension fields from `fact_pnl_use_case_3`:
- `strategy`
- `book`
- `cost_center`
- `process_1`
- `process_2` ⭐ **CRITICAL - User needs this**
- `division` (optional)
- `business_area` (optional)
- `product_line` (optional)
- `effective_date`

### Recommended Fix

**Update Schema Endpoint:**
```python
if table_name == 'fact_pnl_use_case_3':
    # Use Case 3: fact_pnl_use_case_3 uses different column names
    fields = [
        {'value': 'strategy', 'label': 'Strategy', 'type': 'String'},
        {'value': 'book', 'label': 'Book', 'type': 'String'},
        {'value': 'cost_center', 'label': 'Cost Center', 'type': 'String'},
        {'value': 'process_1', 'label': 'Process 1', 'type': 'String'},  # ✅ ADD
        {'value': 'process_2', 'label': 'Process 2', 'type': 'String'},  # ✅ ADD (CRITICAL)
        {'value': 'division', 'label': 'Division', 'type': 'String'},  # ✅ ADD (optional)
        {'value': 'business_area', 'label': 'Business Area', 'type': 'String'},  # ✅ ADD (optional)
        {'value': 'product_line', 'label': 'Product Line', 'type': 'String'},  # ✅ ADD (optional)
        {'value': 'effective_date', 'label': 'Effective Date', 'type': 'Date'},
    ]
```

---

## 📋 Summary of Issues & Fixes

| Issue | Root Cause | Fix Location | Priority |
|-------|-----------|--------------|----------|
| **1. Default Mode** | Always defaults to 'ai' | `RuleEditor.tsx` line 497 | ⭐⭐⭐ High |
| **2. Missing Rule Display** | Rule loading only in `onSelectionChanged`, not on modal open | `RuleEditor.tsx` lines 2103-2152 | ⭐⭐⭐ High |
| **3. Mode Switch Loses Data** | `setRulePreview(null)` clears data | `RuleEditor.tsx` line 3191 | ⭐⭐⭐ High |
| **4. Missing Process_2** | Schema endpoint only returns 4 fields | `use_cases.py` lines 315-322 | ⭐⭐⭐⭐⭐ Critical |

---

## 🎯 Implementation Checklist

### Backend Fixes
- [ ] Update `/api/v1/use-cases/{id}/schema` endpoint to include `process_1`, `process_2`, and other dimension fields for Use Case 3

### Frontend Fixes
- [ ] Add `useEffect` to detect existing rule and set appropriate default mode when modal opens
- [ ] Update mode toggle to preserve rule data when switching modes
- [ ] Ensure rule loading happens when modal opens, not just on selection change
- [ ] Default to Standard Mode when no existing rule exists (as user requested)

---

## 🔍 Verification Steps

After fixes are applied:

1. **Test Default Mode:**
   - Open "Manage Rule" for a node with Standard Mode rule → Should open in Standard Mode
   - Open "Manage Rule" for a node with AI Mode rule → Should open in AI Mode
   - Open "Manage Rule" for a node with no rule → Should open in Standard Mode (default)

2. **Test Rule Display:**
   - Open "Manage Rule" for "Swap Commission" → Should show existing rule conditions
   - Switch from AI to Standard Mode → Should preserve and display rule data
   - Switch from Standard to AI Mode → Should preserve and display rule prompt

3. **Test Process_2 Field:**
   - Open "Manage Rule" for Use Case 3
   - Click "Add Condition"
   - Select field dropdown → Should show "Process 2" option
   - Select "Process 2" → Should allow adding condition with "in" operator for multiple values

