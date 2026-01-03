# Type 2B Rule JSON Schema Design

**Document Purpose:** JSON schema definition for `predicate_json` column to support Type 2B rules (arithmetic of multiple queries)

**Status:** Design Proposal  
**Date:** 2026-01-01  
**Rule Type:** Type 2B (FILTER_ARITHMETIC)

---

## Requirements

Type 2B rules combine multiple independent queries with arithmetic operators.

**Example (NODE_ID 4 - "Commissions"):**
```
SUM(DAILY_COMMISION) WHERE Strategy='CORE' 
+ 
SUM(DAILY_TRADING) WHERE Strategy='CORE' AND Process_2 IN ('SWAP COMMISSION', 'SD COMMISSION')
```

**Requirements:**
1. Support multiple queries (2+)
2. Each query has its own measure
3. Each query has its own filter conditions
4. Support arithmetic operators: `+`, `-`, `*`, `/`
5. Support complex expressions: `(Query1 + Query2) * 0.5`
6. Backward compatible with existing Type 1/Type 2 rules

---

## Proposed JSON Schema

### Schema Version 2.0 (Type 2B Support)

```json
{
  "version": "2.0",
  "rule_type": "FILTER_ARITHMETIC",
  "expression": {
    "operator": "+",
    "operands": [
      {
        "type": "query",
        "query_id": "query_1"
      },
      {
        "type": "query",
        "query_id": "query_2"
      }
    ]
  },
  "queries": [
    {
      "query_id": "query_1",
      "measure": "daily_commission",
      "aggregation": "SUM",
      "filters": [
        {
          "field": "strategy",
          "operator": "=",
          "value": "CORE"
        }
      ]
    },
    {
      "query_id": "query_2",
      "measure": "daily_trade",
      "aggregation": "SUM",
      "filters": [
        {
          "field": "strategy",
          "operator": "=",
          "value": "CORE"
        },
        {
          "field": "process_2",
          "operator": "IN",
          "values": ["SWAP COMMISSION", "SD COMMISSION"]
        }
      ]
    }
  ],
  "logic_en": "SUM(DAILY_COMMISION) where Strategy='CORE' + SUM(DAILY_TRADING) where Strategy='CORE' and Process_2 in ('SWAP COMMISSION', 'SD COMMISSION')"
}
```

---

## Detailed Schema Definition

### Root Object

```typescript
interface Type2BRule {
  version: "2.0";                    // Schema version
  rule_type: "FILTER_ARITHMETIC";   // Rule type identifier
  expression: ArithmeticExpression;  // Root arithmetic expression
  queries: Query[];                 // Array of query definitions
  logic_en: string;                 // Natural language description
}
```

### Arithmetic Expression

```typescript
interface ArithmeticExpression {
  operator: "+" | "-" | "*" | "/";  // Arithmetic operator
  operands: Operand[];               // Array of operands (2+)
}

interface Operand {
  type: "query" | "constant" | "expression";  // Operand type
  query_id?: string;                 // Reference to query (if type="query")
  value?: number;                    // Constant value (if type="constant")
  expression?: ArithmeticExpression;  // Nested expression (if type="expression")
}
```

### Query Definition

```typescript
interface Query {
  query_id: string;                  // Unique identifier within rule
  measure: string;                   // Measure name: "daily_pnl" | "daily_commission" | "daily_trade"
  aggregation: "SUM" | "AVG" | "COUNT" | "MAX" | "MIN";  // Aggregation function
  filters: Filter[];                  // Array of filter conditions
}

interface Filter {
  field: string;                     // Dimension field name
  operator: "=" | "!=" | "IN" | "NOT IN" | ">" | "<" | ">=" | "<=" | "LIKE" | "IS NULL" | "IS NOT NULL";
  value?: string | number;            // Single value (for =, !=, >, <, etc.)
  values?: (string | number)[];      // Array of values (for IN, NOT IN)
}
```

---

## Example: NODE_ID 4 - "Commissions"

### Complete JSON Payload

```json
{
  "version": "2.0",
  "rule_type": "FILTER_ARITHMETIC",
  "expression": {
    "operator": "+",
    "operands": [
      {
        "type": "query",
        "query_id": "query_1"
      },
      {
        "type": "query",
        "query_id": "query_2"
      }
    ]
  },
  "queries": [
    {
      "query_id": "query_1",
      "measure": "daily_commission",
      "aggregation": "SUM",
      "filters": [
        {
          "field": "strategy",
          "operator": "=",
          "value": "CORE"
        }
      ]
    },
    {
      "query_id": "query_2",
      "measure": "daily_trade",
      "aggregation": "SUM",
      "filters": [
        {
          "field": "strategy",
          "operator": "=",
          "value": "CORE"
        },
        {
          "field": "process_2",
          "operator": "IN",
          "values": ["SWAP COMMISSION", "SD COMMISSION"]
        }
      ]
    }
  ],
  "logic_en": "SUM(DAILY_COMMISION) where Strategy='CORE' + SUM(DAILY_TRADING) where Strategy='CORE' and Process_2 in ('SWAP COMMISSION', 'SD COMMISSION')"
}
```

### SQL Generation (Reference)

From this JSON, the engine would generate:

```sql
-- Query 1
SELECT SUM(daily_commission) 
FROM fact_pnl_use_case_3 
WHERE strategy = 'CORE';

-- Query 2
SELECT SUM(daily_trade) 
FROM fact_pnl_use_case_3 
WHERE strategy = 'CORE' 
  AND process_2 IN ('SWAP COMMISSION', 'SD COMMISSION');

-- Result
result = query_1_result + query_2_result;
```

---

## Advanced Examples

### Example 1: Complex Expression with Constants

**Rule:** `(Query1 + Query2) * 0.5`

```json
{
  "version": "2.0",
  "rule_type": "FILTER_ARITHMETIC",
  "expression": {
    "operator": "*",
    "operands": [
      {
        "type": "expression",
        "expression": {
          "operator": "+",
          "operands": [
            {
              "type": "query",
              "query_id": "query_1"
            },
            {
              "type": "query",
              "query_id": "query_2"
            }
          ]
        }
      },
      {
        "type": "constant",
        "value": 0.5
      }
    ]
  },
  "queries": [
    {
      "query_id": "query_1",
      "measure": "daily_pnl",
      "aggregation": "SUM",
      "filters": [
        {
          "field": "strategy",
          "operator": "=",
          "value": "CORE"
        }
      ]
    },
    {
      "query_id": "query_2",
      "measure": "daily_commission",
      "aggregation": "SUM",
      "filters": [
        {
          "field": "strategy",
          "operator": "=",
          "value": "CORE"
        }
      ]
    }
  ],
  "logic_en": "(SUM(DAILY_PNL) where Strategy='CORE' + SUM(DAILY_COMMISION) where Strategy='CORE') * 0.5"
}
```

### Example 2: Three Queries with Subtraction

**Rule:** `Query1 - Query2 - Query3`

```json
{
  "version": "2.0",
  "rule_type": "FILTER_ARITHMETIC",
  "expression": {
    "operator": "-",
    "operands": [
      {
        "type": "query",
        "query_id": "query_1"
      },
      {
        "type": "query",
        "query_id": "query_2"
      },
      {
        "type": "query",
        "query_id": "query_3"
      }
    ]
  },
  "queries": [
    {
      "query_id": "query_1",
      "measure": "daily_pnl",
      "aggregation": "SUM",
      "filters": [
        {
          "field": "strategy",
          "operator": "=",
          "value": "CORE"
        }
      ]
    },
    {
      "query_id": "query_2",
      "measure": "daily_commission",
      "aggregation": "SUM",
      "filters": [
        {
          "field": "strategy",
          "operator": "=",
          "value": "CORE"
        }
      ]
    },
    {
      "query_id": "query_3",
      "measure": "daily_trade",
      "aggregation": "SUM",
      "filters": [
        {
          "field": "strategy",
          "operator": "=",
          "value": "CORE"
        },
        {
          "field": "process_2",
          "operator": "=",
          "value": "ABC"
        }
      ]
    }
  ],
  "logic_en": "SUM(DAILY_PNL) where Strategy='CORE' - SUM(DAILY_COMMISION) where Strategy='CORE' - SUM(DAILY_TRADING) where Strategy='CORE' and Process_2='ABC'"
}
```

### Example 3: Division with Multiple Conditions

**Rule:** `Query1 / Query2`

```json
{
  "version": "2.0",
  "rule_type": "FILTER_ARITHMETIC",
  "expression": {
    "operator": "/",
    "operands": [
      {
        "type": "query",
        "query_id": "query_1"
      },
      {
        "type": "query",
        "query_id": "query_2"
      }
    ]
  },
  "queries": [
    {
      "query_id": "query_1",
      "measure": "daily_pnl",
      "aggregation": "SUM",
      "filters": [
        {
          "field": "strategy",
          "operator": "=",
          "value": "CORE"
        },
        {
          "field": "process_2",
          "operator": "=",
          "value": "Inventory Management"
        }
      ]
    },
    {
      "query_id": "query_2",
      "measure": "daily_trade",
      "aggregation": "SUM",
      "filters": [
        {
          "field": "strategy",
          "operator": "=",
          "value": "CORE"
        }
      ]
    }
  ],
  "logic_en": "SUM(DAILY_PNL) where Strategy='CORE' and Process_2='Inventory Management' / SUM(DAILY_TRADING) where Strategy='CORE'"
}
```

---

## Backward Compatibility

### Type 1 Rule (Simple Filter) - Version 1.0

```json
{
  "version": "1.0",
  "rule_type": "FILTER_SIMPLE",
  "measure": "daily_pnl",
  "aggregation": "SUM",
  "filters": [
    {
      "field": "strategy",
      "operator": "=",
      "value": "CORE"
    }
  ],
  "logic_en": "SUM(DAILY_PNL) where Strategy='CORE'"
}
```

### Type 2 Rule (Multi-Condition) - Version 1.0

```json
{
  "version": "1.0",
  "rule_type": "FILTER_MULTI",
  "measure": "daily_pnl",
  "aggregation": "SUM",
  "filters": [
    {
      "field": "strategy",
      "operator": "=",
      "value": "CORE"
    },
    {
      "field": "process_2",
      "operator": "=",
      "value": "Inventory Management"
    }
  ],
  "logic_en": "SUM(DAILY_PNL) where Strategy='CORE' and Process_2='Inventory Management'"
}
```

**Note:** Version 1.0 rules can be migrated to Version 2.0 format by wrapping in a single-query expression.

---

## Field Mapping (Use Case 3 Input Table)

### Dimensions
- `cost_center` → `cost_center`
- `division` → `division`
- `business_area` → `business_area`
- `product_line` → `product_line`
- `strategy` → `strategy`
- `process_1` → `process_1`
- `process_2` → `process_2`
- `book` → `book`

### Measures
- `daily_pnl` → `daily_pnl`
- `daily_commission` → `daily_commission`
- `daily_trade` → `daily_trade`

---

## Validation Rules

### Schema Validation
1. `version` must be "2.0" for Type 2B rules
2. `rule_type` must be "FILTER_ARITHMETIC"
3. `expression.operator` must be one of: `+`, `-`, `*`, `/`
4. `expression.operands` must have at least 2 operands
5. All `query_id` references in `expression.operands` must exist in `queries` array
6. Each query must have unique `query_id`
7. `measure` must be one of: `daily_pnl`, `daily_commission`, `daily_trade`
8. `aggregation` must be one of: `SUM`, `AVG`, `COUNT`, `MAX`, `MIN`
9. Filter `operator` must match value type:
   - `IN`, `NOT IN` → requires `values` array
   - `=`, `!=`, `>`, `<`, `>=`, `<=`, `LIKE` → requires `value` (single)
   - `IS NULL`, `IS NOT NULL` → no value required

### Business Logic Validation
1. Division by zero check: If operator is `/`, ensure denominator is not zero
2. Query result validation: Each query must return exactly one row (aggregation result)
3. Measure existence: Verify measure exists in input table schema
4. Field existence: Verify all filter fields exist in input table schema

---

## SQL Generation Algorithm

### Step 1: Generate SQL for Each Query

```python
def generate_query_sql(query: Query, table_name: str) -> str:
    """
    Generate SQL for a single query.
    
    Example:
    query = {
        "query_id": "query_1",
        "measure": "daily_commission",
        "aggregation": "SUM",
        "filters": [
            {"field": "strategy", "operator": "=", "value": "CORE"}
        ]
    }
    
    Returns:
    SELECT SUM(daily_commission) 
    FROM fact_pnl_use_case_3 
    WHERE strategy = 'CORE'
    """
    # Build SELECT clause
    select_clause = f"{query['aggregation']}({query['measure']})"
    
    # Build WHERE clause
    where_conditions = []
    for filter in query['filters']:
        if filter['operator'] == '=':
            where_conditions.append(f"{filter['field']} = '{filter['value']}'")
        elif filter['operator'] == 'IN':
            values = ", ".join([f"'{v}'" for v in filter['values']])
            where_conditions.append(f"{filter['field']} IN ({values})")
        # ... handle other operators
    
    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
    
    return f"SELECT {select_clause} FROM {table_name} WHERE {where_clause}"
```

### Step 2: Evaluate Expression

```python
def evaluate_expression(expression: ArithmeticExpression, query_results: Dict[str, float]) -> float:
    """
    Evaluate arithmetic expression using query results.
    
    Example:
    expression = {
        "operator": "+",
        "operands": [
            {"type": "query", "query_id": "query_1"},
            {"type": "query", "query_id": "query_2"}
        ]
    }
    
    query_results = {
        "query_1": 100.0,
        "query_2": 50.0
    }
    
    Returns: 150.0
    """
    if expression['operator'] == '+':
        return sum([get_operand_value(op, query_results) for op in expression['operands']])
    elif expression['operator'] == '-':
        values = [get_operand_value(op, query_results) for op in expression['operands']]
        result = values[0]
        for v in values[1:]:
            result -= v
        return result
    elif expression['operator'] == '*':
        result = 1.0
        for op in expression['operands']:
            result *= get_operand_value(op, query_results)
        return result
    elif expression['operator'] == '/':
        values = [get_operand_value(op, query_results) for op in expression['operands']]
        result = values[0]
        for v in values[1:]:
            if v == 0:
                raise ValueError("Division by zero")
            result /= v
        return result

def get_operand_value(operand: Operand, query_results: Dict[str, float]) -> float:
    """Get value for an operand."""
    if operand['type'] == 'query':
        return query_results[operand['query_id']]
    elif operand['type'] == 'constant':
        return operand['value']
    elif operand['type'] == 'expression':
        return evaluate_expression(operand['expression'], query_results)
```

---

## Database Storage

### metadata_rules Table

```sql
-- Example row for NODE_ID 4
INSERT INTO metadata_rules (
    use_case_id,
    node_id,
    rule_type,
    measure_name,  -- NULL for Type 2B (multiple measures)
    predicate_json,
    sql_where,     -- NULL for Type 2B (generated from predicate_json)
    logic_en
) VALUES (
    '...',
    'NODE_4',
    'FILTER_ARITHMETIC',
    NULL,
    '{"version": "2.0", "rule_type": "FILTER_ARITHMETIC", ...}'::jsonb,
    NULL,
    'SUM(DAILY_COMMISION) where Strategy=''CORE'' + SUM(DAILY_TRADING) where Strategy=''CORE'' and Process_2 in (''SWAP COMMISSION'', ''SD COMMISSION'')'
);
```

**Note:** 
- `measure_name` is NULL for Type 2B (multiple measures)
- `sql_where` is NULL for Type 2B (generated dynamically from `predicate_json`)

---

## Summary

### Key Features
✅ Supports multiple independent queries  
✅ Each query has its own measure and filters  
✅ Supports arithmetic operators: `+`, `-`, `*`, `/`  
✅ Supports complex nested expressions  
✅ Backward compatible with Type 1/Type 2 rules  
✅ Extensible for future enhancements  

### For NODE_ID 4
The JSON schema fully supports the requirement:
- Query 1: `SUM(DAILY_COMMISION) WHERE Strategy='CORE'`
- Query 2: `SUM(DAILY_TRADING) WHERE Strategy='CORE' AND Process_2 IN (...)`
- Operator: `+` (addition)
- Result: `Query1 + Query2`

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-01  
**Status:** Ready for Implementation


