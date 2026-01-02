# Decimal Precision Policy

**Document Purpose:** Mandatory policy for financial calculations - Decimal type only, never float

**Status:** MANDATORY  
**Date:** 2026-01-01  
**Priority:** CRITICAL - Financial System Requirement

---

## Policy Statement

**ALL financial calculations MUST use Python's `Decimal` type. The use of `float` in financial calculations is STRICTLY FORBIDDEN.**

**Rationale:**
- Floating point arithmetic introduces rounding errors (0.1 + 0.2 = 0.300000004)
- In trading P&L systems, being off by a penny is unacceptable
- Regulatory requirements demand exact precision
- Audit trails must show exact values

---

## Database Schema

### ✅ CORRECT: Use Numeric Type

```sql
-- ✅ CORRECT
daily_pnl NUMERIC(18, 2)  -- PostgreSQL Numeric type
mtd_pnl NUMERIC(18, 2)
ytd_pnl NUMERIC(18, 2)
```

**SQLAlchemy:**
```python
# ✅ CORRECT
daily_pnl = Column(Numeric(18, 2), nullable=False)
```

---

## Python Code

### ✅ CORRECT: Use Decimal Type

```python
from decimal import Decimal

# ✅ CORRECT: Load from database
daily = Decimal(str(fact.daily_pnl))  # Convert to Decimal

# ✅ CORRECT: Arithmetic operations
result = node3_daily - node4_daily  # Both Decimal, result is Decimal

# ✅ CORRECT: Aggregation
total = sum(Decimal(str(row['daily_pnl'])) for row in facts_df)

# ✅ CORRECT: Return Decimal
return {
    'daily': Decimal('100.01'),  # Decimal
    'mtd': Decimal('500.50'),    # Decimal
    'ytd': Decimal('1000.00')     # Decimal
}
```

### ❌ FORBIDDEN: Use Float Type

```python
# ❌ FORBIDDEN: Float conversion
daily = float(fact.daily_pnl)  # ❌ NO!

# ❌ FORBIDDEN: Float arithmetic
result = float(node3_daily) - float(node4_daily)  # ❌ NO!

# ❌ FORBIDDEN: Float aggregation
total = sum(float(row['daily_pnl']) for row in facts_df)  # ❌ NO!

# ❌ FORBIDDEN: Return float
return {
    'daily': 100.01,  # ❌ NO! Must be Decimal
}
```

---

## Exception: JSONB Storage

**PostgreSQL JSONB Limitation:** JSONB does not support Decimal type directly.

**Allowed Pattern:** Convert to float ONLY at the very end, for JSONB storage:

```python
# ✅ ALLOWED: Convert Decimal to float ONLY for JSONB storage
measure_vector = {
    'daily': round(float(measures.get('daily', Decimal('0'))), 4),  # ✅ OK for storage
    'mtd': round(float(measures.get('mtd', Decimal('0'))), 4),      # ✅ OK for storage
    'ytd': round(float(measures.get('ytd', Decimal('0'))), 4),         # ✅ OK for storage
}

# Store in JSONB
result_obj.measure_vector = measure_vector  # JSONB accepts float
```

**CRITICAL RULES:**
1. ✅ Calculations must use Decimal throughout
2. ✅ Convert to float ONLY when storing in JSONB
3. ✅ Use `round(float(decimal_value), 4)` to maintain precision
4. ✅ Never use float in intermediate calculations

---

## Type 3 Engine Requirements

**MANDATORY:** Type 3 engine must use Decimal throughout

```python
# ✅ CORRECT: Type 3 Engine
from decimal import Decimal

def evaluate_type3_expression(
    expression: str,
    node_values: Dict[str, Dict[str, Decimal]]  # All Decimal
) -> Dict[str, Decimal]:
    """
    Evaluate Type 3 arithmetic expression.
    
    CRITICAL: All values must be Decimal, never float.
    """
    # Parse expression
    # Get node values (already Decimal)
    node3_daily = node_values['NODE_3']['daily']  # Decimal
    node4_daily = node_values['NODE_4']['daily']  # Decimal
    
    # Calculate (Decimal arithmetic)
    result_daily = node3_daily - node4_daily  # ✅ Decimal
    
    # Return Decimal
    return {
        'daily': result_daily,  # ✅ Decimal
        'mtd': node3_daily - node4_daily,  # ✅ Decimal
        'ytd': node3_daily - node4_daily,  # ✅ Decimal
    }
```

---

## Type 2B Engine Requirements

**MANDATORY:** Type 2B engine must use Decimal throughout

```python
# ✅ CORRECT: Type 2B Engine
from decimal import Decimal

def execute_type2b_rule(
    rule: MetadataRule,
    facts_df: pd.DataFrame  # Decimal columns
) -> Dict[str, Decimal]:
    """
    Execute Type 2B rule (arithmetic of queries).
    
    CRITICAL: All calculations must use Decimal.
    """
    # Execute Query 1
    query1_result = facts_df[
        (facts_df['strategy'] == 'CORE')
    ]['daily_commission'].sum()  # ✅ Returns Decimal
    
    # Execute Query 2
    query2_result = facts_df[
        (facts_df['strategy'] == 'CORE') &
        (facts_df['process_2'].isin(['SWAP COMMISSION', 'SD COMMISSION']))
    ]['daily_trade'].sum()  # ✅ Returns Decimal
    
    # Arithmetic (Decimal)
    result = query1_result + query2_result  # ✅ Decimal
    
    return {
        'daily': result,  # ✅ Decimal
        'mtd': Decimal('0'),  # ✅ Decimal
        'ytd': Decimal('0'),  # ✅ Decimal
    }
```

---

## Code Audit Checklist

### Files to Audit

- [ ] `app/engine/waterfall.py` - ✅ Already uses Decimal
- [ ] `app/engine/type3_engine.py` - **NEW** - Must use Decimal only
- [ ] `app/engine/type2b_engine.py` - **NEW** - Must use Decimal only
- [ ] `app/services/orchestrator.py` - ⚠️ Has float conversions (for JSONB only - verify)
- [ ] `app/services/fact_service.py` - ✅ Already uses Decimal
- [ ] `app/services/unified_pnl_service.py` - ⚠️ Has float conversions (for JSONB only - verify)

### Audit Pattern

```python
# Search for float usage
grep -r "float(" app/

# Verify each usage:
# 1. Is it ONLY for JSONB storage? ✅ OK
# 2. Is it in calculation path? ❌ MUST FIX
# 3. Is it in aggregation? ❌ MUST FIX
```

---

## Testing Requirements

### Unit Tests

```python
def test_type3_decimal_precision():
    """Test that Type 3 arithmetic maintains Decimal precision."""
    node_values = {
        'NODE_3': {'daily': Decimal('100.01')},
        'NODE_4': {'daily': Decimal('50.02')}
    }
    
    result = evaluate_type3_expression('NODE_3 - NODE_4', node_values)
    
    # Must be exactly 49.99, not 49.9900000001
    assert result['daily'] == Decimal('49.99')
    assert isinstance(result['daily'], Decimal)  # Must be Decimal, not float
```

### Integration Tests

```python
def test_type3_penny_accuracy():
    """Test that Type 3 rules maintain penny accuracy."""
    # Create test data with exact penny values
    # Execute Type 3 rule
    # Verify result matches expected penny value exactly
    assert result['daily'] == Decimal('100.00')  # Exact match required
```

---

## Linter Rules

**Add to `.cursorrules` or linting config:**

```python
# Financial calculations must use Decimal, not float
# Rule: Flag float() calls in financial calculation files
# Exception: float() allowed only for JSONB storage conversion
```

---

## Summary

**✅ DO:**
- Use `Decimal` for all financial calculations
- Use `Numeric(18, 2)` in database schema
- Convert to `float` ONLY for JSONB storage
- Use `round(float(decimal_value), 4)` for JSONB conversion

**❌ DON'T:**
- Use `float` in calculation paths
- Use `float` in aggregation
- Use `float` in arithmetic operations
- Return `float` from calculation functions

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-01  
**Status:** MANDATORY POLICY

