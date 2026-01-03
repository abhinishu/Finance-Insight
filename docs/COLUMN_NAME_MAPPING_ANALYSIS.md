# Column Name Mapping Analysis: Strategy ID vs Strategy

## Problem Statement

**Issue:**
- User creates a rule in Tab 3 (Standard Mode) selecting "Strategy ID" from dropdown
- Rule is created with SQL: `strategy_id = 'CORE'`
- When calculation runs for Use Case 3, error occurs:
  ```
  column "strategy_id" does not exist
  HINT: Perhaps you meant to reference the column "fact_pnl_use_case_3.strategy"
  ```

**Root Cause:**
- Frontend shows "Strategy ID" (assumes `fact_pnl_gold` schema)
- Use Case 3 uses `fact_pnl_use_case_3` table which has column `strategy` (not `strategy_id`)
- No column mapping logic exists to translate field names based on use case/table

---

## Root Cause Analysis

### 1. Frontend Hardcoded Field List

**File:** `frontend/src/components/RuleEditor.tsx`

**Location 1: Standard Mode Fields (Line 512-518)**
```typescript
const availableFields = [
  { value: 'account_id', label: 'Account ID' },
  { value: 'cc_id', label: 'Cost Center ID' },
  { value: 'book_id', label: 'Book ID' },
  { value: 'strategy_id', label: 'Strategy ID' },  // ❌ Wrong for Use Case 3
  { value: 'trade_date', label: 'Trade Date' },
]
```

**Location 2: Field Helper (Line 1348-1357)**
```typescript
const availableFieldsForHelper = [
  { field: 'book_id', label: 'Book ID', type: 'String' },
  { field: 'strategy_id', label: 'Strategy ID', type: 'String' },  // ❌ Wrong for Use Case 3
  { field: 'account_id', label: 'Account ID', type: 'String' },
  { field: 'cc_id', label: 'Cost Center ID', type: 'String' },
  // ...
]
```

**Problem:**
- Hardcoded list assumes `fact_pnl_gold` schema
- No use case awareness
- Always shows `strategy_id`, `book_id`, `cc_id` (fact_pnl_gold naming)

---

### 2. Backend Field Validation

**File:** `app/services/rules.py`

**Location: FACT_TABLE_FIELDS (Line 19-29)**
```python
FACT_TABLE_FIELDS = {
    'account_id': 'String',
    'cc_id': 'String',
    'book_id': 'String',
    'strategy_id': 'String',  # ❌ Only for fact_pnl_gold
    'trade_date': 'Date',
    'daily_pnl': 'Numeric',
    'mtd_pnl': 'Numeric',
    'ytd_pnl': 'Numeric',
    'pytd_pnl': 'Numeric',
}
```

**Location: validate_field_exists (Line 42-52)**
```python
def validate_field_exists(field: str) -> bool:
    """
    Validate that a field exists in the fact_pnl_gold schema.
    """
    return field in FACT_TABLE_FIELDS  # ❌ Only checks fact_pnl_gold
```

**Problem:**
- Hardcoded for `fact_pnl_gold` schema only
- No use case awareness
- Validates `strategy_id` as valid (for fact_pnl_gold) but fails at execution (for fact_pnl_use_case_3)

---

### 3. Backend SQL Generation

**File:** `app/services/rules.py`

**Location: convert_json_to_sql (Line 126-180)**
```python
def convert_json_to_sql(predicate_json: Dict[str, Any]) -> str:
    # ...
    for cond in conditions:
        field = cond['field']  # ❌ Uses field name directly
        # ...
        sql_parts.append(f"{field} {sql_operator} '{escaped_value}'")  # ❌ No mapping
    # ...
    return sql_where
```

**Problem:**
- Uses field name directly in SQL
- No column mapping based on use case/table
- Generates `strategy_id = 'CORE'` which fails for `fact_pnl_use_case_3`

---

### 4. SQL Execution

**File:** `app/services/calculator.py`

**Location: apply_rule_to_leaf (Line 104-116)**
```python
if table_name == 'fact_pnl_use_case_3':
    sql_query = f"""
        SELECT 
            COALESCE(SUM(pnl_daily), 0) as daily_pnl,
            ...
        FROM fact_pnl_use_case_3
        WHERE {sql_where}  # ❌ sql_where contains 'strategy_id' but table has 'strategy'
    """
```

**Problem:**
- `sql_where` contains `strategy_id = 'CORE'`
- Table `fact_pnl_use_case_3` has column `strategy` (not `strategy_id`)
- SQL execution fails: column does not exist

---

## Column Name Mapping Reference

### fact_pnl_gold (Use Cases 1 & 2)
| Frontend Field | Database Column | Type |
|----------------|----------------|------|
| Strategy ID | `strategy_id` | String |
| Book ID | `book_id` | String |
| Cost Center ID | `cc_id` | String |
| Account ID | `account_id` | String |
| Trade Date | `trade_date` | Date |

### fact_pnl_use_case_3 (Use Case 3)
| Frontend Field | Database Column | Type |
|----------------|----------------|------|
| Strategy ID | `strategy` ⚠️ | String |
| Book ID | `book` ⚠️ | String |
| Cost Center ID | `cost_center` ⚠️ | String |
| Account ID | ❌ Not available | - |
| Trade Date | `effective_date` ⚠️ | Date |

**Key Differences:**
- `strategy_id` → `strategy`
- `book_id` → `book`
- `cc_id` → `cost_center`
- `trade_date` → `effective_date`
- `account_id` → Not available in Use Case 3

---

## Solution Options

### Option 1: Backend Column Mapping (Recommended) ⭐

**Add column mapping function similar to `get_measure_column_name` but for dimension columns.**

**Implementation:**

1. **Create `get_dimension_column_name()` function:**
   ```python
   def get_dimension_column_name(field_name: str, table_name: str) -> str:
       """
       Map frontend field name to actual database column name based on table.
       
       Args:
           field_name: Frontend field name (e.g., 'strategy_id', 'book_id')
           table_name: Target table name (e.g., 'fact_pnl_use_case_3')
       
       Returns:
           Actual database column name
       """
       if table_name == 'fact_pnl_use_case_3':
           mapping = {
               'strategy_id': 'strategy',
               'book_id': 'book',
               'cc_id': 'cost_center',
               'trade_date': 'effective_date',
               'account_id': None,  # Not available
           }
           mapped = mapping.get(field_name)
           if mapped is None:
               raise ValueError(f"Field '{field_name}' not available in {table_name}")
           return mapped
       elif table_name == 'fact_pnl_entries':
           # fact_pnl_entries might have different naming
           mapping = {
               'strategy_id': 'strategy_id',  # Keep as-is if same
               'book_id': 'book_id',
               'cc_id': 'cc_id',
               'trade_date': 'pnl_date',
           }
           return mapping.get(field_name, field_name)  # Default to field_name if not mapped
       else:
           # fact_pnl_gold: use field name as-is
           return field_name
   ```

2. **Update `convert_json_to_sql()` to accept use_case:**
   ```python
   def convert_json_to_sql(
       predicate_json: Dict[str, Any],
       use_case: Optional[UseCase] = None
   ) -> str:
       # Determine table name
       table_name = 'fact_pnl_gold'  # Default
       if use_case and use_case.input_table_name:
           table_name = use_case.input_table_name
       
       # ...
       for cond in conditions:
           field = cond['field']
           # Map field name to actual column name
           mapped_field = get_dimension_column_name(field, table_name)
           # Use mapped_field in SQL
           sql_parts.append(f"{mapped_field} {sql_operator} '{escaped_value}'")
   ```

3. **Update rule creation endpoint to pass use_case:**
   ```python
   @router.post("/use-cases/{use_case_id}/rules", ...)
   def create_rule(...):
       use_case = db.query(UseCase).filter(...).first()
       # ...
       sql_where = convert_json_to_sql(predicate_json, use_case=use_case)
   ```

**Pros:**
- ✅ Centralized mapping logic
- ✅ Works for all use cases
- ✅ Backward compatible (fact_pnl_gold unchanged)
- ✅ No frontend changes needed initially

**Cons:**
- ⚠️ Frontend still shows wrong field names for Use Case 3
- ⚠️ User confusion (sees "Strategy ID" but it maps to "strategy")

---

### Option 2: Frontend Use Case Awareness

**Make frontend aware of use case and show correct field names.**

**Implementation:**

1. **Fetch use case configuration:**
   ```typescript
   // In RuleEditor.tsx
   const [useCaseConfig, setUseCaseConfig] = useState<any>(null)
   
   useEffect(() => {
     if (selectedUseCaseId) {
       // Fetch use case to get input_table_name
       axios.get(`${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}`)
         .then(res => {
           setUseCaseConfig(res.data)
         })
     }
   }, [selectedUseCaseId])
   ```

2. **Dynamic field list based on use case:**
   ```typescript
   const getAvailableFields = () => {
     if (useCaseConfig?.input_table_name === 'fact_pnl_use_case_3') {
       return [
         { value: 'strategy', label: 'Strategy' },  // ✅ Correct name
         { value: 'book', label: 'Book' },
         { value: 'cost_center', label: 'Cost Center' },
         { value: 'effective_date', label: 'Effective Date' },
       ]
     } else {
       // Default: fact_pnl_gold
       return [
         { value: 'account_id', label: 'Account ID' },
         { value: 'cc_id', label: 'Cost Center ID' },
         { value: 'book_id', label: 'Book ID' },
         { value: 'strategy_id', label: 'Strategy ID' },
         { value: 'trade_date', label: 'Trade Date' },
       ]
     }
   }
   
   const availableFields = getAvailableFields()
   ```

**Pros:**
- ✅ User sees correct field names
- ✅ No confusion
- ✅ Better UX

**Cons:**
- ⚠️ Requires backend column mapping anyway (for existing rules)
- ⚠️ More complex frontend logic

---

### Option 3: Combined Approach (Recommended) ⭐⭐

**Implement both backend mapping AND frontend awareness.**

**Implementation:**

1. **Backend:** Add `get_dimension_column_name()` function (Option 1)
2. **Backend:** Update `convert_json_to_sql()` to use mapping
3. **Frontend:** Add use case awareness (Option 2)
4. **Backend:** Add API endpoint to return available fields for a use case:
   ```python
   @router.get("/use-cases/{use_case_id}/available-fields")
   def get_available_fields(use_case_id: UUID, db: Session = Depends(get_db)):
       use_case = db.query(UseCase).filter(...).first()
       table_name = use_case.input_table_name or 'fact_pnl_gold'
       
       if table_name == 'fact_pnl_use_case_3':
           return {
               'fields': [
                   {'value': 'strategy', 'label': 'Strategy', 'type': 'String'},
                   {'value': 'book', 'label': 'Book', 'type': 'String'},
                   {'value': 'cost_center', 'label': 'Cost Center', 'type': 'String'},
                   {'value': 'effective_date', 'label': 'Effective Date', 'type': 'Date'},
               ]
           }
       else:
           # Default: fact_pnl_gold
           return {
               'fields': [
                   {'value': 'strategy_id', 'label': 'Strategy ID', 'type': 'String'},
                   # ...
               ]
           }
   ```

4. **Frontend:** Fetch available fields from API:
   ```typescript
   useEffect(() => {
     if (selectedUseCaseId) {
       axios.get(`${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/available-fields`)
         .then(res => {
           setAvailableFields(res.data.fields)
         })
     }
   }, [selectedUseCaseId])
   ```

**Pros:**
- ✅ Best UX (correct field names)
- ✅ Backward compatible (existing rules work via mapping)
- ✅ Single source of truth (backend)
- ✅ Future-proof (easy to add new use cases)

**Cons:**
- ⚠️ More implementation work
- ⚠️ Requires API endpoint

---

## Recommended Solution

**Option 3: Combined Approach**

**Phase 1 (Immediate Fix):**
1. Add `get_dimension_column_name()` function
2. Update `convert_json_to_sql()` to use mapping
3. Update rule creation endpoint to pass use_case

**Phase 2 (UX Improvement):**
4. Add API endpoint for available fields
5. Update frontend to fetch and display correct fields

**Why:**
- Phase 1 fixes the immediate bug (existing rules work)
- Phase 2 improves UX (users see correct field names)
- Backward compatible
- Future-proof

---

## Implementation Checklist

### Backend Changes

- [ ] Create `get_dimension_column_name()` function in `app/engine/waterfall.py`
- [ ] Update `convert_json_to_sql()` to accept `use_case` parameter
- [ ] Update `convert_json_to_sql()` to use column mapping
- [ ] Update rule creation endpoint to pass `use_case` to `convert_json_to_sql()`
- [ ] Add API endpoint `/use-cases/{id}/available-fields` (optional, for Phase 2)
- [ ] Update `validate_field_exists()` to be table-aware (optional)

### Frontend Changes

- [ ] Fetch use case configuration on selection
- [ ] Make `availableFields` dynamic based on use case (Phase 2)
- [ ] Update field helper to use dynamic fields (Phase 2)

### Testing

- [ ] Test rule creation for Use Case 1 (fact_pnl_gold) - should work as before
- [ ] Test rule creation for Use Case 3 (fact_pnl_use_case_3) - should map correctly
- [ ] Test existing rules still work (backward compatibility)
- [ ] Test calculation execution with mapped column names

---

## Summary

**Root Cause:**
- Frontend hardcoded field list assumes `fact_pnl_gold` schema
- Backend SQL generation uses field names directly without mapping
- Use Case 3 uses different column names (`strategy` vs `strategy_id`)

**Solution:**
- Add backend column mapping function
- Update SQL generation to use mapping
- (Optional) Make frontend use case-aware for better UX

**Impact:**
- ✅ Fixes immediate bug
- ✅ Backward compatible
- ✅ Future-proof for new use cases

