# NLP Sample Queries for Use Case 3: America Cash Equity Trading

**Document Purpose:** Natural language query examples for GenAI training and testing

**Use Case:** America Cash Equity Trading Structure  
**Date:** 2026-01-01  
**Status:** Training Data

---

## Overview

This document contains 10 natural language queries that the "America Cash Equity Trading" dataset can answer. These queries demonstrate the types of questions users might ask when analyzing the P&L data.

**Key Features:**
- Queries reference specific nodes in the hierarchy
- Queries use business terminology (not technical IDs)
- Queries demonstrate different rule types (Type 1, 2, 2B, 3)
- Queries show various aggregation patterns

---

## Sample Queries

### 1. Simple Node Breakdown

**Query:** "Show me the breakdown of Core Ex CRB."

**Expected Response:**
- Display NODE_3 (Core Ex CRB) and its children:
  - NODE_4 (Commissions)
  - NODE_7 (Trading)
- Show daily P&L values for each node
- Explain that Core Ex CRB = Commissions + Trading (Type 3 rule)

**Rule Type:** Type 3 (Node Arithmetic)  
**Nodes Involved:** NODE_3, NODE_4, NODE_7

---

### 2. Commission Calculation Explanation

**Query:** "How is Commissions calculated?"

**Expected Response:**
- Explain that Commissions (NODE_4) uses Type 2B rule
- Formula: `SUM(daily_commission) WHERE strategy='CORE' + SUM(daily_trade) WHERE strategy='CORE' AND process_2 IN ('SWAP COMMISSION', 'SD COMMISSION')`
- Show the two component queries and their results
- Display the final sum

**Rule Type:** Type 2B (FILTER_ARITHMETIC)  
**Nodes Involved:** NODE_4

---

### 3. Trading Net Calculation

**Query:** "Calculate Net Trading excluding Inventory."

**Expected Response:**
- Identify that this refers to NODE_8 (Facilitations)
- Explain formula: `NODE_7 - NODE_9` (Trading - Inventory Management)
- Show intermediate values:
  - NODE_7 (Trading) = NODE_3 - NODE_4
  - NODE_9 (Inventory Management) = SUM(daily_pnl) WHERE strategy='CORE' AND process_2='Inventory Management'
- Display final result

**Rule Type:** Type 3 (Node Arithmetic)  
**Nodes Involved:** NODE_7, NODE_8, NODE_9

---

### 4. Product Line Filtering

**Query:** "What is the total P&L for CORE Products?"

**Expected Response:**
- Identify NODE_2 (CORE Products)
- Apply Type 1 rule: `SUM(daily_pnl) WHERE product_line='CORE Products'`
- Display aggregated result
- Show breakdown by child nodes (Core Ex CRB, CRB, ETF Amber, MSET)

**Rule Type:** Type 1 (Simple Filter)  
**Nodes Involved:** NODE_2

---

### 5. Swap Commission Analysis

**Query:** "Show me all Swap Commission transactions."

**Expected Response:**
- Identify NODE_6 (Swap Commission)
- Apply Type 2 rule: `SUM(daily_trade) WHERE strategy='CORE' AND process_2 IN ('SWAP COMMISSION', 'SD COMMISSION')`
- Display filtered fact rows
- Show aggregated total
- Explain that this feeds into NODE_4 (Commissions) calculation

**Rule Type:** Type 2 (Multi-Condition)  
**Nodes Involved:** NODE_6, NODE_4

---

### 6. CRB Book Breakdown

**Query:** "What is the P&L for CRB books?"

**Expected Response:**
- Identify NODE_10 (CRB)
- Apply Type 2 rule: `SUM(daily_pnl) WHERE strategy='CORE' AND book IN ('MSAL', 'ETFUS', 'Central Risk Book', 'CRB Risk')`
- Display filtered fact rows
- Show aggregated total
- Explain relationship to NODE_2 (CORE Products)

**Rule Type:** Type 2 (Multi-Condition with IN)  
**Nodes Involved:** NODE_10

---

### 7. Commission Components

**Query:** "Break down Commissions into Non-Swap and Swap components."

**Expected Response:**
- Identify NODE_4 (Commissions) as parent
- Show children:
  - NODE_5 (Commissions Non Swap) = `SUM(daily_commission) WHERE strategy='CORE'`
  - NODE_6 (Swap Commission) = `SUM(daily_trade) WHERE strategy='CORE' AND process_2 IN ('SWAP COMMISSION', 'SD COMMISSION')`
- Display values for each component
- Show that NODE_4 = NODE_5 + NODE_6 (via Type 2B rule)

**Rule Type:** Type 2, Type 2B  
**Nodes Involved:** NODE_4, NODE_5, NODE_6

---

### 8. Trading vs Commissions Comparison

**Query:** "Compare Trading and Commissions for Core Ex CRB."

**Expected Response:**
- Identify NODE_3 (Core Ex CRB) as parent
- Show children:
  - NODE_4 (Commissions) - Type 2B rule
  - NODE_7 (Trading) - Type 3 rule (NODE_3 - NODE_4)
- Display side-by-side comparison
- Calculate difference: Trading - Commissions
- Explain that Trading = Core Ex CRB - Commissions

**Rule Type:** Type 2B, Type 3  
**Nodes Involved:** NODE_3, NODE_4, NODE_7

---

### 9. ETF Amber Strategy Analysis

**Query:** "What is the P&L for ETF Amber strategy?"

**Expected Response:**
- Identify NODE_11 (ETF Amber)
- Apply Type 1 rule: `SUM(daily_pnl) WHERE strategy='ETF Amer'`
- Note: Node name "ETF Amber" maps to strategy value "ETF Amer"
- Display aggregated result
- Show filtered fact rows

**Rule Type:** Type 1 (Simple Filter)  
**Nodes Involved:** NODE_11

---

### 10. MSET Process Analysis

**Query:** "Show me the P&L breakdown for MSET process."

**Expected Response:**
- Identify NODE_12 (MSET)
- Apply Type 1 rule: `SUM(daily_pnl) WHERE process_1='MSET'`
- Display aggregated result
- Show filtered fact rows
- Explain that this is a process-level filter

**Rule Type:** Type 1 (Simple Filter)  
**Nodes Involved:** NODE_12

---

## Query Patterns

### Pattern 1: Node Name Lookup
- User mentions node name (e.g., "Core Ex CRB")
- System maps to NODE_ID (e.g., "NODE_3")
- System retrieves rule and executes

### Pattern 2: Calculation Explanation
- User asks "How is X calculated?"
- System identifies node and rule type
- System explains formula and shows components

### Pattern 3: Comparison Queries
- User compares two nodes (e.g., "Trading vs Commissions")
- System retrieves both nodes
- System displays side-by-side comparison

### Pattern 4: Breakdown Queries
- User asks for breakdown (e.g., "Break down Commissions")
- System identifies parent node
- System shows all children with their values

### Pattern 5: Filter-Based Queries
- User mentions dimension value (e.g., "CORE Products", "ETF Amber")
- System maps to appropriate node
- System applies rule and displays results

---

## GenAI Training Notes

### Key Mappings

1. **Node Name → Node ID:**
   - "Core Ex CRB" → NODE_3
   - "Commissions" → NODE_4
   - "Trading" → NODE_7
   - "CORE Products" → NODE_2
   - "CRB" → NODE_10
   - "ETF Amber" → NODE_11 (strategy: "ETF Amer")
   - "MSET" → NODE_12

2. **Business Terms:**
   - "Net Trading" → NODE_8 (Facilitations)
   - "Swap Commission" → NODE_6
   - "Non-Swap Commission" → NODE_5
   - "Inventory" → NODE_9 (Inventory Management)

3. **Rule Type Indicators:**
   - "calculated" → Type 3 (Node Arithmetic)
   - "sum of" → Type 1 or Type 2
   - "combination of" → Type 2B
   - "where" → Type 1 or Type 2 (filtering)

---

## Expected GenAI Behavior

### Query Understanding
1. Parse natural language query
2. Identify node names mentioned
3. Map to NODE_IDs
4. Determine query intent (breakdown, calculation, comparison)

### Response Generation
1. Retrieve node hierarchy
2. Identify applicable rules
3. Execute rules (if needed)
4. Format response with:
   - Node values
   - Rule explanations
   - Formula breakdowns
   - Supporting data

### Error Handling
1. Unknown node name → Suggest similar nodes
2. Ambiguous query → Ask for clarification
3. Missing data → Explain data availability
4. Calculation error → Show error details

---

## Testing Checklist

- [ ] Query 1: Node breakdown works
- [ ] Query 2: Calculation explanation works
- [ ] Query 3: Net calculation works
- [ ] Query 4: Product line filtering works
- [ ] Query 5: Swap commission analysis works
- [ ] Query 6: CRB book breakdown works
- [ ] Query 7: Commission components work
- [ ] Query 8: Comparison queries work
- [ ] Query 9: ETF Amber strategy works
- [ ] Query 10: MSET process works

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-01  
**Status:** Ready for GenAI Training


