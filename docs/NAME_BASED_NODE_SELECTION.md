# Name-Based Node Selection - UX Requirement

**Document Purpose:** UX design for Type 3 rule builder with name-based auto-complete

**Status:** Design Specification  
**Date:** 2026-01-01  
**Priority:** HIGH - User Experience Critical

---

## Problem Statement

**The Worry:** Business users think in names ("Core Ex CRB", "Commissions"), not node IDs ("NODE_3", "NODE_4").

**The Risk:** If UI forces users to look up IDs (e.g., "What is Node 4 again?"), they will hate the tool.

**Example Problem:**
```
Current Plan: User types "NODE_3 - NODE_4"
User Thinks: "What is NODE_3? What is NODE_4?"
User Frustration: High ❌
```

**Required Solution:**
```
User Types: "Core Ex CRB - Commissions"
System Stores: "NODE_3 - NODE_4"
User Experience: Excellent ✅
```

---

## Solution: Name-Based Auto-Complete

### UI Design

#### Type 3 Rule Builder with Auto-Complete

```
┌─────────────────────────────────────────────────────────┐
│ Node Arithmetic Expression Builder                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Expression:                                             │
│                                                         │
│ [Core Ex CRB ▼] [-] [Commissions ▼]                    │
│   └─ Auto-complete dropdown                            │
│   └─ Shows: "Core Ex CRB (NODE_3)"                      │
│                                                         │
│ Operators:                                              │
│   [+] [-] [*] [/]                                       │
│                                                         │
│ Expression Preview:                                     │
│   NODE_3 - NODE_4                                       │
│                                                         │
│ Dependencies:                                            │
│   • Core Ex CRB (NODE_3)                                │
│   • Commissions (NODE_4)                                │
│                                                         │
│ [Validate] [Preview Impact] [Save]                     │
└─────────────────────────────────────────────────────────┘
```

### User Flow

1. **User clicks "Add Node"**
   - Auto-complete dropdown appears
   - User types "Core..."
   - System suggests: "Core Ex CRB (NODE_3)", "Core Products (NODE_2)"
   - User selects "Core Ex CRB (NODE_3)"
   - **System stores:** `NODE_3`
   - **UI displays:** "Core Ex CRB"

2. **User clicks operator "-"**
   - Operator added to expression

3. **User clicks "Add Node" again**
   - Auto-complete dropdown appears
   - User types "Comm..."
   - System suggests: "Commissions (NODE_4)"
   - User selects "Commissions (NODE_4)"
   - **System stores:** `NODE_4`
   - **UI displays:** "Commissions"

4. **Expression Complete**
   - **User sees:** "Core Ex CRB - Commissions"
   - **System stores:** "NODE_3 - NODE_4"
   - **System validates:** Dependencies exist, no circular dependency

---

## Backend API Design

### Endpoint 1: Node Search (Auto-Complete)

```python
@router.get("/api/v1/hierarchy/nodes/search")
def search_nodes(
    use_case_id: UUID,
    query: str,  # User types "Core..."
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Search hierarchy nodes by name for auto-complete.
    
    Args:
        use_case_id: Use case ID to filter nodes
        query: Search query (node name)
        limit: Maximum results to return
    
    Returns:
        [
            {
                "node_id": "NODE_3",
                "node_name": "Core Ex CRB",
                "display": "Core Ex CRB (NODE_3)",
                "depth": 2,
                "is_leaf": false
            },
            ...
        ]
    """
    use_case = db.query(UseCase).filter(
        UseCase.use_case_id == use_case_id
    ).first()
    
    if not use_case:
        raise HTTPException(404, "Use case not found")
    
    nodes = db.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == use_case.atlas_structure_id,
        DimHierarchy.node_name.ilike(f"%{query}%")
    ).limit(limit).all()
    
    return [
        {
            "node_id": node.node_id,
            "node_name": node.node_name,
            "display": f"{node.node_name} ({node.node_id})",
            "depth": node.depth,
            "is_leaf": node.is_leaf
        }
        for node in nodes
    ]
```

### Endpoint 2: Node Lookup (Get Name from ID)

```python
@router.get("/api/v1/hierarchy/nodes/{node_id}")
def get_node(
    node_id: str,
    use_case_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get node details by node_id.
    
    Returns:
        {
            "node_id": "NODE_3",
            "node_name": "Core Ex CRB",
            "display": "Core Ex CRB (NODE_3)",
            "depth": 2,
            "is_leaf": false,
            "parent_node_id": "NODE_2"
        }
    """
    use_case = db.query(UseCase).filter(
        UseCase.use_case_id == use_case_id
    ).first()
    
    if not use_case:
        raise HTTPException(404, "Use case not found")
    
    node = db.query(DimHierarchy).filter(
        DimHierarchy.node_id == node_id,
        DimHierarchy.atlas_source == use_case.atlas_structure_id
    ).first()
    
    if not node:
        raise HTTPException(404, f"Node '{node_id}' not found")
    
    return {
        "node_id": node.node_id,
        "node_name": node.node_name,
        "display": f"{node.node_name} ({node.node_id})",
        "depth": node.depth,
        "is_leaf": node.is_leaf,
        "parent_node_id": node.parent_node_id
    }
```

### Endpoint 3: Get All Nodes (for Expression Builder)

```python
@router.get("/api/v1/hierarchy/nodes")
def list_nodes(
    use_case_id: UUID,
    db: Session = Depends(get_db)
):
    """
    List all nodes for a use case (for expression builder).
    
    Returns:
        [
            {
                "node_id": "NODE_2",
                "node_name": "CORE Products",
                "display": "CORE Products (NODE_2)",
                "depth": 1,
                "is_leaf": false
            },
            ...
        ]
    """
    use_case = db.query(UseCase).filter(
        UseCase.use_case_id == use_case_id
    ).first()
    
    if not use_case:
        raise HTTPException(404, "Use case not found")
    
    nodes = db.query(DimHierarchy).filter(
        DimHierarchy.atlas_source == use_case.atlas_structure_id
    ).order_by(DimHierarchy.depth, DimHierarchy.node_name).all()
    
    return [
        {
            "node_id": node.node_id,
            "node_name": node.node_name,
            "display": f"{node.node_name} ({node.node_id})",
            "depth": node.depth,
            "is_leaf": node.is_leaf
        }
        for node in nodes
    ]
```

---

## Frontend Component Design

### Component: NodeAutoComplete

```typescript
// NodeAutoComplete.tsx
import React, { useState, useEffect } from 'react';
import { Autocomplete, TextField } from '@mui/material';
import axios from 'axios';

interface NodeOption {
  node_id: string;
  node_name: string;
  display: string;
  depth: number;
  is_leaf: boolean;
}

interface NodeAutoCompleteProps {
  value: string;  // node_id (stored value)
  onChange: (nodeId: string) => void;
  useCaseId: string;
  label?: string;
  placeholder?: string;
}

const NodeAutoComplete: React.FC<NodeAutoCompleteProps> = ({
  value,
  onChange,
  useCaseId,
  label = "Node",
  placeholder = "Type node name..."
}) => {
  const [query, setQuery] = useState('');
  const [options, setOptions] = useState<NodeOption[]>([]);
  const [selectedNode, setSelectedNode] = useState<NodeOption | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Load node name for selected node_id
  useEffect(() => {
    if (value && useCaseId) {
      setLoading(true);
      axios.get(`/api/v1/hierarchy/nodes/${value}`, {
        params: { use_case_id: useCaseId }
      })
        .then(res => {
          setSelectedNode(res.data);
          setLoading(false);
        })
        .catch(err => {
          console.error('Failed to load node:', err);
          setLoading(false);
        });
    } else {
      setSelectedNode(null);
    }
  }, [value, useCaseId]);
  
  // Search as user types
  useEffect(() => {
    if (query.length >= 2 && useCaseId) {
      setLoading(true);
      axios.get(`/api/v1/hierarchy/nodes/search`, {
        params: { 
          use_case_id: useCaseId, 
          query,
          limit: 10
        }
      })
        .then(res => {
          setOptions(res.data);
          setLoading(false);
        })
        .catch(err => {
          console.error('Failed to search nodes:', err);
          setLoading(false);
        });
    } else {
      setOptions([]);
    }
  }, [query, useCaseId]);
  
  return (
    <Autocomplete
      value={selectedNode}
      inputValue={query}
      onInputChange={(e, newValue) => setQuery(newValue)}
      options={options}
      getOptionLabel={(option) => option.display}
      loading={loading}
      onChange={(e, option) => {
        if (option) {
          onChange(option.node_id);  // Store node_id internally
          setSelectedNode(option);
          setQuery('');  // Clear query
        } else {
          onChange('');  // Clear selection
          setSelectedNode(null);
        }
      }}
      renderInput={(params) => (
        <TextField 
          {...params} 
          label={label}
          placeholder={placeholder}
          InputProps={{
            ...params.InputProps,
            endAdornment: (
              <>
                {loading ? <CircularProgress size={20} /> : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}
      renderOption={(props, option) => (
        <li {...props}>
          <div>
            <div style={{ fontWeight: 'bold' }}>{option.node_name}</div>
            <div style={{ fontSize: '0.8em', color: '#666' }}>
              {option.node_id} • Depth: {option.depth} • {option.is_leaf ? 'Leaf' : 'Parent'}
            </div>
          </div>
        </li>
      )}
    />
  );
};

export default NodeAutoComplete;
```

### Component: Type3RuleBuilder

```typescript
// Type3RuleBuilder.tsx
import React, { useState } from 'react';
import { Button, TextField, Box, Typography } from '@mui/material';
import NodeAutoComplete from './NodeAutoComplete';

interface ExpressionNode {
  type: 'node' | 'operator';
  nodeId?: string;
  operator?: '+' | '-' | '*' | '/';
}

interface Type3RuleBuilderProps {
  useCaseId: string;
  nodeId: string;  // Node this rule applies to
  onSave: (expression: string, dependencies: string[]) => void;
}

const Type3RuleBuilder: React.FC<Type3RuleBuilderProps> = ({
  useCaseId,
  nodeId,
  onSave
}) => {
  const [expression, setExpression] = useState<ExpressionNode[]>([]);
  const [nodeNames, setNodeNames] = useState<Map<string, string>>(new Map());
  
  // Load node names for display
  useEffect(() => {
    axios.get(`/api/v1/hierarchy/nodes`, {
      params: { use_case_id: useCaseId }
    })
      .then(res => {
        const names = new Map();
        res.data.forEach((node: any) => {
          names.set(node.node_id, node.node_name);
        });
        setNodeNames(names);
      });
  }, [useCaseId]);
  
  const addNode = () => {
    setExpression([...expression, { type: 'node', nodeId: undefined }]);
  };
  
  const addOperator = (op: '+' | '-' | '*' | '/') => {
    setExpression([...expression, { type: 'operator', operator: op }]);
  };
  
  const updateNode = (index: number, nodeId: string) => {
    const newExpr = [...expression];
    newExpr[index] = { ...newExpr[index], nodeId };
    setExpression(newExpr);
  };
  
  const removeItem = (index: number) => {
    setExpression(expression.filter((_, i) => i !== index));
  };
  
  const buildExpression = (): string => {
    return expression
      .map(item => {
        if (item.type === 'node') {
          return item.nodeId || '';
        } else {
          return item.operator || '';
        }
      })
      .join(' ');
  };
  
  const getDependencies = (): string[] => {
    return expression
      .filter(item => item.type === 'node' && item.nodeId)
      .map(item => item.nodeId!)
      .filter((id, index, self) => self.indexOf(id) === index);  // Unique
  };
  
  const handleSave = () => {
    const expr = buildExpression();
    const deps = getDependencies();
    
    // Validate
    if (!expr || deps.length === 0) {
      alert('Please complete the expression');
      return;
    }
    
    onSave(expr, deps);
  };
  
  return (
    <Box>
      <Typography variant="h6">Type 3: Node Arithmetic Rule</Typography>
      
      <Box sx={{ mt: 2 }}>
        {expression.map((item, idx) => (
          <Box key={idx} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
            {item.type === 'node' ? (
              <>
                <NodeAutoComplete
                  value={item.nodeId || ''}
                  onChange={(nodeId) => updateNode(idx, nodeId)}
                  useCaseId={useCaseId}
                  label={`Node ${idx + 1}`}
                />
                <Button onClick={() => removeItem(idx)}>Remove</Button>
              </>
            ) : (
              <>
                <TextField 
                  value={item.operator} 
                  disabled 
                  sx={{ width: 60 }}
                />
                <Button onClick={() => removeItem(idx)}>Remove</Button>
              </>
            )}
          </Box>
        ))}
      </Box>
      
      <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
        <Button variant="outlined" onClick={addNode}>Add Node</Button>
        <Button variant="outlined" onClick={() => addOperator('+')}>+</Button>
        <Button variant="outlined" onClick={() => addOperator('-')}>-</Button>
        <Button variant="outlined" onClick={() => addOperator('*')}>*</Button>
        <Button variant="outlined" onClick={() => addOperator('/')}>/</Button>
      </Box>
      
      <Box sx={{ mt: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
        <Typography variant="subtitle2">Expression Preview:</Typography>
        <Typography variant="body2" fontFamily="monospace">
          {expression.map(item => {
            if (item.type === 'node') {
              return item.nodeId ? nodeNames.get(item.nodeId) || item.nodeId : '?';
            } else {
              return ` ${item.operator} `;
            }
          }).join('') || 'No expression yet'}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Stored as: {buildExpression() || 'N/A'}
        </Typography>
      </Box>
      
      <Box sx={{ mt: 2 }}>
        <Typography variant="subtitle2">Dependencies:</Typography>
        <ul>
          {getDependencies().map(dep => (
            <li key={dep}>
              {nodeNames.get(dep) || dep} ({dep})
            </li>
          ))}
        </ul>
      </Box>
      
      <Box sx={{ mt: 2 }}>
        <Button variant="contained" onClick={handleSave}>Save Rule</Button>
      </Box>
    </Box>
  );
};

export default Type3RuleBuilder;
```

---

## Implementation Phases

### Phase 5.7 (Week 8-9): Name-Based Auto-Complete

**Tasks:**
1. Create node search API endpoint
2. Create node lookup API endpoint
3. Create NodeAutoComplete component
4. Integrate into Type 3 rule builder
5. Test with Use Case 3

**Deliverables:**
- API endpoints
- UI components
- Test results

**Testing:**
- ✅ Auto-complete works
- ✅ Name-to-ID mapping correct
- ✅ Expression building works
- ✅ Dependencies extracted correctly

---

## Summary

**User Experience:**
- ✅ Users type node names (e.g., "Core Ex CRB")
- ✅ System suggests matching nodes
- ✅ System stores node IDs internally
- ✅ UI displays node names
- ✅ Expression shows: "Core Ex CRB - Commissions"
- ✅ System stores: "NODE_3 - NODE_4"

**Result:** Excellent UX, users never see node IDs.

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-01  
**Status:** Design Complete - Ready for Implementation

