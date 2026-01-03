# Expansion State Analysis: Tab 2 vs Tab 3 vs Tab 4

## Problem Statement

**Issue:** 
- Tab 2 (Discovery) shows hierarchy **expanded by default** ✅
- Tab 3 (Business Rules) shows hierarchy **collapsed by default** ❌
- Tab 4 (Executive View) shows hierarchy **collapsed by default** ❌

**User Expectation:** All tabs should launch in **expanded mode** like Tab 2.

---

## Root Cause Analysis

### Tab 2 (DiscoveryScreen.tsx) - ✅ EXPANDED

**Location:** `frontend/src/components/DiscoveryScreen.tsx:440-447`

**Logic:**
```typescript
// Initialize expandedNodes: expand first 4 levels by default
const defaultExpanded = new Set<string>()
flatData.forEach(row => {
  if (row.depth < 4 && !row.is_leaf) {
    defaultExpanded.add(row.node_id)
  }
})
setExpandedNodes(defaultExpanded)
```

**Behavior:**
- Expands **all nodes with depth < 4** (first 4 levels)
- No localStorage override (loads saved state, but initializes with depth < 4 if no saved state)
- Result: **Expanded by default** ✅

---

### Tab 3 (RuleEditor.tsx) - ❌ COLLAPSED

**Location:** `frontend/src/components/RuleEditor.tsx`

**Multiple Initialization Points:**

#### 1. Sidebar Expansion (Line 975-988)
```typescript
// Expand all nodes by default in sidebar
const expandAllNodes = (nodes: HierarchyNode[]): Set<string> => {
  const expanded = new Set<string>()
  const traverse = (nodeList: HierarchyNode[]) => {
    for (const node of nodeList) {
      if (node.children && node.children.length > 0) {
        expanded.add(node.node_id)
        traverse(node.children)
      }
    }
  }
  traverse(nodes)
  return expanded
}
setExpandedNodes(expandAllNodes(hierarchy))  // Line 988: Expands ALL nodes
```

#### 2. Grid Initialization (Line 1014-1021) - **OVERWRITES ABOVE**
```typescript
// Initialize expandedNodes: expand root nodes (depth 0) by default
const defaultExpanded = new Set<string>()
flatData.forEach(row => {
  if (row.depth === 0 && !row.is_leaf) {
    defaultExpanded.add(row.node_id)
  }
})
setExpandedNodes(defaultExpanded)  // Line 1021: OVERWRITES with only root nodes
```

#### 3. localStorage Override (Line 683-695)
```typescript
// Load shared tree state (Tab 2 & 3 unification)
const stateKey = getTreeStateKey(selectedUseCase.atlas_structure_id)
const savedState = localStorage.getItem(stateKey)
if (savedState) {
  try {
    const state = JSON.parse(savedState)
    if (state.expandedNodes) {
      setExpandedNodes(new Set(state.expandedNodes))  // OVERRIDES default expansion
    }
  } catch (e) {
    console.warn('Failed to load shared tree state:', e)
  }
}
```

**Execution Order:**
1. Line 988: Expands ALL nodes (for sidebar)
2. Line 1021: **OVERWRITES** with only root nodes (for grid) ❌
3. Line 690: **POTENTIALLY OVERWRITES** with localStorage saved state (if exists) ❌

**Result:** 
- If localStorage has saved state → Uses saved state (likely collapsed)
- If no localStorage → Only root nodes expanded (collapsed) ❌

---

### Tab 4 (ExecutiveDashboard.tsx) - ❌ COLLAPSED

**Location:** `frontend/src/components/ExecutiveDashboard.tsx:412-420`

**Logic:**
```typescript
// Initialize expandedNodes: expand root nodes (depth 0) by default
const defaultExpanded = new Set<string>()
flatData.forEach(row => {
  const hasChildren = row.children && Array.isArray(row.children) && row.children.length > 0
  if (row.depth === 0 && hasChildren) {
    defaultExpanded.add(row.node_id)
  }
})
setExpandedNodes(defaultExpanded)
```

**Behavior:**
- Only expands **root nodes (depth 0)**
- No localStorage logic
- Result: **Collapsed by default** ❌

---

## The Problem

### Issue 1: Inconsistent Default Expansion Logic

| Tab | Default Expansion | Result |
|-----|------------------|--------|
| **Tab 2** | `depth < 4` (first 4 levels) | ✅ Expanded |
| **Tab 3** | `depth === 0` (root only) | ❌ Collapsed |
| **Tab 4** | `depth === 0` (root only) | ❌ Collapsed |

### Issue 2: localStorage Override in Tab 3

Tab 3 loads saved expansion state from localStorage, which might be:
- Empty (first visit) → Falls back to `depth === 0` (collapsed)
- Saved collapsed state → Uses collapsed state
- Saved expanded state → Uses expanded state (but only if user previously expanded)

**Problem:** If user visits Tab 3 first (before Tab 2), localStorage might be empty, so it defaults to collapsed.

### Issue 3: Conflicting Initialization in Tab 3

Tab 3 has **TWO** initialization points:
1. Line 988: Expands ALL nodes (for sidebar)
2. Line 1021: Overwrites with only root nodes (for grid)

The second one **wins**, causing the grid to be collapsed.

---

## Recommended Solutions

### Option 1: Match Tab 2 Logic (Recommended) ⭐

**Make Tab 3 and Tab 4 use the same expansion logic as Tab 2.**

**Change in Tab 3 (RuleEditor.tsx:1014-1021):**
```typescript
// BEFORE:
// Initialize expandedNodes: expand root nodes (depth 0) by default
const defaultExpanded = new Set<string>()
flatData.forEach(row => {
  if (row.depth === 0 && !row.is_leaf) {
    defaultExpanded.add(row.node_id)
  }
})

// AFTER:
// Initialize expandedNodes: expand first 4 levels by default (matches Tab 2)
const defaultExpanded = new Set<string>()
flatData.forEach(row => {
  if (row.depth < 4 && !row.is_leaf) {
    defaultExpanded.add(row.node_id)
  }
})
```

**Change in Tab 4 (ExecutiveDashboard.tsx:412-420):**
```typescript
// BEFORE:
// Initialize expandedNodes: expand root nodes (depth 0) by default
const defaultExpanded = new Set<string>()
flatData.forEach(row => {
  const hasChildren = row.children && Array.isArray(row.children) && row.children.length > 0
  if (row.depth === 0 && hasChildren) {
    defaultExpanded.add(row.node_id)
  }
})

// AFTER:
// Initialize expandedNodes: expand first 4 levels by default (matches Tab 2)
const defaultExpanded = new Set<string>()
flatData.forEach(row => {
  if (row.depth < 4 && !row.is_leaf) {
    defaultExpanded.add(row.node_id)
  }
})
```

**Pros:**
- ✅ Consistent behavior across all tabs
- ✅ Simple change (copy Tab 2 logic)
- ✅ Matches user expectation

**Cons:**
- ⚠️ localStorage in Tab 3 might still override (need to handle this)

---

### Option 2: Expand All Nodes (Most Aggressive)

**Expand ALL nodes by default in all tabs.**

**Change in Tab 3 (RuleEditor.tsx:1014-1021):**
```typescript
// Initialize expandedNodes: expand all nodes by default
const defaultExpanded = new Set<string>()
flatData.forEach(row => {
  if (!row.is_leaf) {
    defaultExpanded.add(row.node_id)
  }
})
```

**Change in Tab 4 (ExecutiveDashboard.tsx:412-420):**
```typescript
// Initialize expandedNodes: expand all nodes by default
const defaultExpanded = new Set<string>()
flatData.forEach(row => {
  if (!row.is_leaf) {
    defaultExpanded.add(row.node_id)
  }
})
```

**Pros:**
- ✅ Maximum visibility (all nodes expanded)
- ✅ Simple logic

**Cons:**
- ⚠️ Might be overwhelming for deep hierarchies
- ⚠️ Performance impact for very large trees

---

### Option 3: Fix localStorage Override in Tab 3

**Only load localStorage if it exists AND has meaningful data. Otherwise, use default expansion.**

**Change in Tab 3 (RuleEditor.tsx:683-695):**
```typescript
// BEFORE:
const savedState = localStorage.getItem(stateKey)
if (savedState) {
  try {
    const state = JSON.parse(savedState)
    if (state.expandedNodes) {
      setExpandedNodes(new Set(state.expandedNodes))
    }
  } catch (e) {
    console.warn('Failed to load shared tree state:', e)
  }
}

// AFTER:
const savedState = localStorage.getItem(stateKey)
if (savedState) {
  try {
    const state = JSON.parse(savedState)
    // Only use saved state if it has meaningful expansion (more than just root)
    if (state.expandedNodes && state.expandedNodes.length > 1) {
      setExpandedNodes(new Set(state.expandedNodes))
    } else {
      // Use default expansion (first 4 levels) if saved state is minimal
      const defaultExpanded = new Set<string>()
      flatData.forEach(row => {
        if (row.depth < 4 && !row.is_leaf) {
          defaultExpanded.add(row.node_id)
        }
      })
      setExpandedNodes(defaultExpanded)
    }
  } catch (e) {
    console.warn('Failed to load shared tree state:', e)
    // Fallback to default expansion
    const defaultExpanded = new Set<string>()
    flatData.forEach(row => {
      if (row.depth < 4 && !row.is_leaf) {
        defaultExpanded.add(row.node_id)
      }
    })
    setExpandedNodes(defaultExpanded)
  }
} else {
  // No saved state - use default expansion
  const defaultExpanded = new Set<string>()
  flatData.forEach(row => {
    if (row.depth < 4 && !row.is_leaf) {
      defaultExpanded.add(row.node_id)
    }
  })
  setExpandedNodes(defaultExpanded)
}
```

**Pros:**
- ✅ Preserves user's expansion state if meaningful
- ✅ Falls back to default expansion if no saved state

**Cons:**
- ⚠️ More complex logic
- ⚠️ Still need to fix the default expansion logic

---

### Option 4: Remove Conflicting Initialization in Tab 3

**Remove the second initialization (line 1021) that overwrites the sidebar expansion.**

**Change in Tab 3 (RuleEditor.tsx:1014-1021):**
```typescript
// REMOVE THIS BLOCK (lines 1014-1021):
// Initialize expandedNodes: expand root nodes (depth 0) by default
const defaultExpanded = new Set<string>()
flatData.forEach(row => {
  if (row.depth === 0 && !row.is_leaf) {
    defaultExpanded.add(row.node_id)
  }
})
setExpandedNodes(defaultExpanded)
```

**But also update line 988 to use depth < 4 instead of ALL:**
```typescript
// BEFORE (line 975-988):
const expandAllNodes = (nodes: HierarchyNode[]): Set<string> => {
  // Expands ALL nodes
}

// AFTER:
const expandDefaultNodes = (flatData: any[]): Set<string> => {
  const expanded = new Set<string>()
  flatData.forEach(row => {
    if (row.depth < 4 && !row.is_leaf) {
      expanded.add(row.node_id)
    }
  })
  return expanded
}
setExpandedNodes(expandDefaultNodes(flatData))
```

**Pros:**
- ✅ Removes conflicting initialization
- ✅ Consistent expansion logic

**Cons:**
- ⚠️ Need to refactor sidebar expansion logic

---

## Recommendation

**Recommended: Option 1 + Option 3 (Combined)**

1. **Change Tab 3 default expansion** to `depth < 4` (matches Tab 2)
2. **Change Tab 4 default expansion** to `depth < 4` (matches Tab 2)
3. **Fix Tab 3 localStorage override** to only use saved state if meaningful, otherwise use default expansion

**Why:**
- ✅ Consistent behavior across all tabs
- ✅ Preserves user's expansion state if meaningful
- ✅ Falls back to sensible default (first 4 levels) if no saved state
- ✅ Simple and maintainable

---

## Implementation Summary

### Files to Change:

1. **`frontend/src/components/RuleEditor.tsx`**
   - Line 1014-1021: Change default expansion from `depth === 0` to `depth < 4`
   - Line 683-695: Fix localStorage override to check if saved state is meaningful

2. **`frontend/src/components/ExecutiveDashboard.tsx`**
   - Line 412-420: Change default expansion from `depth === 0` to `depth < 4`

### Testing Checklist:

- [ ] Tab 2: Still expands first 4 levels ✅
- [ ] Tab 3: Expands first 4 levels on first visit ✅
- [ ] Tab 3: Preserves meaningful saved expansion state ✅
- [ ] Tab 3: Falls back to first 4 levels if saved state is minimal ✅
- [ ] Tab 4: Expands first 4 levels on first visit ✅
- [ ] All tabs: Consistent expansion behavior ✅

