// Note: Using manual tree implementation - no Enterprise required
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridApi, ColumnApi } from 'ag-grid-community'
import axios from 'axios'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import './DiscoveryScreen.css'

interface HierarchyNode {
  node_id: string
  node_name: string
  parent_node_id: string | null
  depth: number
  is_leaf: boolean
  daily_pnl: string
  mtd_pnl: string
  ytd_pnl: string
  pytd_pnl?: string
  region?: string | null
  product?: string | null
  desk?: string | null
  strategy?: string | null
  official_gl_baseline?: string | null
  path?: string[] | null
  children: HierarchyNode[]
}

interface Structure {
  structure_id: string
  name: string
  node_count: number
}

interface ReconciliationData {
  fact_table_sum: {
    daily: string
    mtd: string
    ytd: string
  }
  leaf_nodes_sum: {
    daily: string
    mtd: string
    ytd: string
  }
}

interface DiscoveryResponse {
  structure_id: string
  hierarchy: HierarchyNode[]
  reconciliation?: ReconciliationData
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const DiscoveryScreen: React.FC = () => {
  const [structureId, setStructureId] = useState<string>('')
  const [availableStructures, setAvailableStructures] = useState<Structure[]>([])
  const [useCases, setUseCases] = useState<any[]>([])
  const [selectedUseCaseId, setSelectedUseCaseId] = useState<string>('')
  const [selectedUseCase, setSelectedUseCase] = useState<any>(null)
  const [selectedReport, setSelectedReport] = useState<any>(null) // For scope data only
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [rowData, setRowData] = useState<any[]>([])
  const [gridApi, setGridApi] = useState<GridApi | null>(null)
  const [columnApi, setColumnApi] = useState<ColumnApi | null>(null)
  const [searchText, setSearchText] = useState<string>('')
  const [density, setDensity] = useState<'comfortable' | 'compact'>('comfortable')
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set()) // Track expanded nodes
  const [selectedRow, setSelectedRow] = useState<any>(null) // Selected row for breadcrumbs
  const [reconciliation, setReconciliation] = useState<ReconciliationData | null>(null) // Reconciliation data
  const gridRef = useRef<AgGridReact>(null)
  
  // Shared tree state key (for Tab 2 & 3 unification)
  const getTreeStateKey = (id: string) => `finance_insight_tree_state_${id}`
  
  // Load persisted state from localStorage
  useEffect(() => {
    const savedUseCaseId = localStorage.getItem('finance_insight_selected_use_case_id')
    if (savedUseCaseId) {
      setSelectedUseCaseId(savedUseCaseId)
    }
  }, [])
  
  // Load shared tree state when structure changes (Tab 2 & 3 unification)
  useEffect(() => {
    if (structureId) {
      const stateKey = getTreeStateKey(structureId)
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
    }
  }, [structureId])
  
  // Persist selected use case to localStorage
  useEffect(() => {
    if (selectedUseCaseId) {
      localStorage.setItem('finance_insight_selected_use_case_id', selectedUseCaseId)
    }
  }, [selectedUseCaseId])
  
  // Persist shared tree state to localStorage (Tab 2 & 3 unification)
  useEffect(() => {
    if (structureId && expandedNodes.size >= 0) {
      const stateKey = getTreeStateKey(structureId)
      const state = {
        expandedNodes: Array.from(expandedNodes),
        lastUpdated: new Date().toISOString()
      }
      localStorage.setItem(stateKey, JSON.stringify(state))
    }
  }, [expandedNodes, structureId])

  // Convert nested hierarchy to flat structure for AG-Grid tree data with path arrays
  const flattenHierarchy = useCallback((nodes: HierarchyNode[]): any[] => {
    const flat: any[] = []
    
    const processNode = (node: HierarchyNode, parentAttrs: any = {}) => {
      // Use path from API (from SQL CTE)
      const nodePath = node.path || [node.node_name]
      
      // Inherit attributes from parent if not present
      const region = node.region || parentAttrs.region || null
      const product = node.product || parentAttrs.product || null
      const desk = node.desk || parentAttrs.desk || null
      const strategy = node.strategy || parentAttrs.strategy || null
      
      const flatNode: any = {
        node_id: node.node_id,
        node_name: node.node_name,
        parent_node_id: node.parent_node_id,
        depth: node.depth,
        is_leaf: node.is_leaf,
        daily_pnl: parseFloat(node.daily_pnl) || 0,
        mtd_pnl: parseFloat(node.mtd_pnl) || 0,
        ytd_pnl: parseFloat(node.ytd_pnl) || 0,
        pytd_pnl: node.pytd_pnl ? parseFloat(node.pytd_pnl) : null,
        region: region,
        product: product,
        desk: desk,
        strategy: strategy,
        official_gl_baseline: node.official_gl_baseline ? parseFloat(node.official_gl_baseline) : parseFloat(node.daily_pnl) || 0,
        // AG-Grid tree data: path array for getDataPath (must be array of node_names, not IDs)
        path: Array.isArray(nodePath) ? nodePath : (nodePath ? [nodePath] : [node.node_name]),
      }
      
      // Validation: Ensure path is never null or empty
      if (!flatNode.path || flatNode.path.length === 0) {
        console.warn(`Node ${node.node_id} has empty path, using node_name as fallback`)
        flatNode.path = [node.node_name]
      }
      
      flat.push(flatNode)
      
      // Process children recursively (pass current attributes for inheritance)
      const currentAttrs = { region, product, desk, strategy }
      if (node.children && node.children.length > 0) {
        node.children.forEach(child => processNode(child, currentAttrs))
      }
    }
    
    nodes.forEach(node => processNode(node))
    return flat
  }, [])

  // Load available structures from API
  const loadStructures = useCallback(async () => {
    try {
      console.log('Tab 2: Loading structures from:', `${API_BASE_URL}/api/v1/structures`)
      const response = await axios.get<{ structures: Structure[] }>(
        `${API_BASE_URL}/api/v1/structures`
      )
      console.log('Tab 2: Structures API response:', response.data)
      const structures = response.data?.structures || []
      console.log('Tab 2: Found', structures.length, 'structures')
      setAvailableStructures(structures)
      
      // Auto-select first structure if none selected
      if (structures.length > 0 && !structureId) {
        const firstStructure = structures[0]
        console.log('Tab 2: Auto-selecting first structure:', firstStructure.structure_id)
        setStructureId(firstStructure.structure_id)
      } else if (structures.length === 0) {
        console.warn('Tab 2: No structures found')
        setError('No structures available. Please ensure mock data has been generated.')
      }
    } catch (err: any) {
      console.error('Tab 2: Failed to load structures:', err)
      console.error('Tab 2: Error details:', err.response?.data || err.message)
      setError(`Failed to load available structures: ${err.response?.data?.detail || err.message}`)
    }
  }, [structureId])

  // Load use cases (unified data source for all tabs)
  const loadUseCases = useCallback(async () => {
    try {
      console.log('Tab 2: Loading use cases from:', `${API_BASE_URL}/api/v1/use-cases`)
      const response = await axios.get<{ use_cases: any[] }>(
        `${API_BASE_URL}/api/v1/use-cases`
      )
      console.log('Tab 2: Use Cases API response:', response.data)
      const useCasesList = response.data.use_cases || []
      console.log('Tab 2: Found', useCasesList.length, 'use cases')
      setUseCases(useCasesList)
      
      // Auto-select first use case if available and none selected
      const savedUseCaseId = localStorage.getItem('finance_insight_selected_use_case_id')
      if (savedUseCaseId && useCasesList.find((uc: any) => uc.use_case_id === savedUseCaseId)) {
        setSelectedUseCaseId(savedUseCaseId)
      } else if (useCasesList.length > 0 && !selectedUseCaseId) {
        setSelectedUseCaseId(useCasesList[0].use_case_id)
      }
    } catch (err: any) {
      console.error('Tab 2: Failed to load use cases:', err)
      console.error('Tab 2: Error details:', err.response?.data || err.message)
      // Don't set error for use cases - it's okay if there are no use cases yet
    }
  }, [selectedUseCaseId])

  // Load use case details when selected
  useEffect(() => {
    if (selectedUseCaseId) {
      const useCase = useCases.find(uc => uc.use_case_id === selectedUseCaseId)
      if (useCase) {
        setSelectedUseCase(useCase)
        setStructureId(useCase.atlas_structure_id)
        
        // Also load ReportRegistration data for scope information (if exists)
        const loadReportData = async () => {
          try {
            const response = await axios.get<any[]>(`${API_BASE_URL}/api/v1/reports`)
            const report = response.data.find((r: any) => r.report_name === useCase.name)
            if (report) {
              setSelectedReport(report)
            } else {
              setSelectedReport(null)
            }
          } catch (err) {
            // If reports endpoint fails, continue without scope data
            setSelectedReport(null)
          }
        }
        loadReportData()
      }
    }
  }, [selectedUseCaseId, useCases])

  const loadDiscoveryData = useCallback(async () => {
    if (!structureId) return

    setLoading(true)
    setError(null)
    
    try {
      console.log(`Tab 2: Loading discovery data for structure: ${structureId}`)
      const response = await axios.get<DiscoveryResponse>(
        `${API_BASE_URL}/api/v1/discovery`,
        { params: { structure_id: structureId } }
      )
      
      // Debug: Log full API response
      console.log('Tab 2: Full API Response:', response.data)
      console.log('Tab 2: Hierarchy array length:', response.data?.hierarchy?.length || 0)
      
      // Ensure hierarchy exists, default to empty array
      const hierarchy = response.data?.hierarchy || []
      if (hierarchy.length === 0) {
        console.warn('Tab 2: WARNING - Empty hierarchy array received from API')
        setError('No hierarchy data found. Please ensure mock data has been generated.')
        setRowData([])
        setLoading(false)
        return
      }
      
      // Convert nested hierarchy to flat structure with path arrays from SQL CTE
      const flatData = flattenHierarchy(hierarchy)
      
      // Store reconciliation data (optional)
      if (response.data && response.data.reconciliation) {
        setReconciliation(response.data.reconciliation)
      } else {
        setReconciliation(null)
      }
      
      // CRITICAL: Data Contract Validation - Log ALL rowData
      console.log('=== COMPLETE rowData Validation ===')
      console.log('Total rows:', flatData.length)
      console.log('Full rowData:', JSON.stringify(flatData, null, 2))
      
      // Verify every row has a path property that is an array of strings
      const invalidRows = flatData.filter(row => {
        const hasPath = row.hasOwnProperty('path')
        const isArray = Array.isArray(row.path)
        const isStringArray = isArray && row.path.every((item: any) => typeof item === 'string')
        return !hasPath || !isArray || !isStringArray
      })
      
      if (invalidRows.length > 0) {
        console.error('❌ INVALID ROWS (missing or invalid path):', invalidRows)
        console.error('Rows without path:', invalidRows.map(r => ({ node_id: r.node_id, node_name: r.node_name, path: r.path })))
      } else {
        console.log('✅ ALL ROWS HAVE VALID PATH ARRAYS')
      }
      
      // Log sample paths to verify hierarchy structure
      console.log('=== Path Sample (First 10 rows) ===')
      flatData.slice(0, 10).forEach((row, idx) => {
        console.log(`${idx + 1}. ${row.node_name}:`, row.path, `(length: ${row.path.length})`)
      })
      
      // Verify parent nodes are included (not just leaf nodes)
      const parentNodes = flatData.filter(row => !row.is_leaf)
      const leafNodes = flatData.filter(row => row.is_leaf)
      console.log(`Parent nodes: ${parentNodes.length}, Leaf nodes: ${leafNodes.length}`)
      
      if (parentNodes.length === 0) {
        console.error('❌ CRITICAL: No parent nodes found! Tree will be flat.')
      }
      
      // CRITICAL: Check if paths form a proper hierarchy
      console.log('=== Path Hierarchy Check ===')
      const pathMap = new Map<string, string[]>()
      flatData.forEach(row => {
        pathMap.set(row.node_name, row.path)
      })
      
      // Check if all parent paths exist
      let missingParents = 0
      flatData.forEach(row => {
        if (row.path.length > 1) {
          // Check if parent path exists
          const parentPath = row.path.slice(0, -1)
          const parentName = parentPath[parentPath.length - 1]
          const parentExists = flatData.some(r => r.node_name === parentName && JSON.stringify(r.path) === JSON.stringify(parentPath))
          if (!parentExists) {
            missingParents++
            console.warn(`Missing parent for ${row.node_name}:`, parentPath)
          }
        }
      })
      
      if (missingParents > 0) {
        console.error(`❌ CRITICAL: ${missingParents} nodes have missing parent paths! Tree will be flat.`)
      } else {
        console.log('✅ All parent paths exist')
      }
      
      setRowData(flatData)
      
      // Initialize expandedNodes: expand first 4 levels by default
      const defaultExpanded = new Set<string>()
      flatData.forEach(row => {
        if (row.depth < 4 && !row.is_leaf) {
          defaultExpanded.add(row.node_id)
        }
      })
      setExpandedNodes(defaultExpanded)
      
      // Refresh grid after data loads
      setTimeout(() => {
        if (gridApi) {
          console.log('Refreshing grid with', flatData.length, 'rows')
          gridApi.setGridOption('rowData', flatData)
          gridApi.onFilterChanged() // Trigger external filter
        }
      }, 300)
    } catch (err: any) {
      console.error('Discovery data load error:', err)
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load discovery data'
      setError(errorMessage)
      setRowData([])
      setReconciliation(null) // Clear reconciliation on error
    } finally {
      setLoading(false)
    }
  }, [structureId, flattenHierarchy, gridApi])

  useEffect(() => {
    console.log('Tab 2: Component mounted, loading structures and reports...')
    loadStructures()
    loadUseCases()
  }, [loadStructures, loadUseCases])

  useEffect(() => {
    console.log('Tab 2: useEffect [structureId] triggered, structureId:', structureId)
    if (structureId) {
      console.log('Tab 2: Calling loadDiscoveryData for structureId:', structureId)
      loadDiscoveryData()
    } else {
      console.warn('Tab 2: useEffect: structureId is empty, not loading discovery data')
    }
  }, [structureId, loadDiscoveryData])

  // Financial formatter: Red negatives with parentheses
  const financialFormatter = (params: any) => {
    if (params.value == null || params.value === undefined) return ''
    const value = typeof params.value === 'number' ? params.value : parseFloat(params.value)
    if (isNaN(value)) return ''
    
    const isNegative = value < 0
    const absValue = Math.abs(value)
    const formatted = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(absValue)
    
    if (isNegative) {
      return `(${formatted})`
    }
    return formatted
  }

  // Cell class rules for red negatives
  const cellClassRules = {
    'negative-value': (params: any) => {
      if (params.value == null) return false
      const value = typeof params.value === 'number' ? params.value : parseFloat(params.value)
      return !isNaN(value) && value < 0
    }
  }

  // Row style for group shading based on depth
  const getRowStyle = (params: any) => {
    const depth = params.data?.depth || 0
    if (depth > 0) {
      const opacity = Math.min(0.02 * depth, 0.08)
      return { backgroundColor: `rgba(0, 0, 0, ${opacity})` }
    }
    return {}
  }

  // Toggle node expansion
  const toggleNodeExpansion = useCallback((nodeId: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev)
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId)
      } else {
        newSet.add(nodeId)
      }
      return newSet
    })
    // Trigger filter update
    setTimeout(() => {
      if (gridApi) {
        gridApi.onFilterChanged()
      }
    }, 0)
  }, [gridApi])

  // Custom cell renderer for Node Name with manual tree
  const nodeNameCellRenderer = useCallback((params: any) => {
    const data = params.data
    if (!data) return ''
    
    const depth = data.depth || 0
    const isLeaf = data.is_leaf || false
    const isExpanded = expandedNodes.has(data.node_id)
    const paddingLeft = depth * 20 + 8 // 20px per level + 8px base
    
    const chevron = !isLeaf ? (
      <span 
        onClick={(e) => {
          e.stopPropagation()
          toggleNodeExpansion(data.node_id)
        }}
        style={{ 
          cursor: 'pointer', 
          marginRight: '4px',
          userSelect: 'none',
          fontSize: '12px',
          color: '#3498db'
        }}
      >
        {isExpanded ? '▼' : '▶'}
      </span>
    ) : (
      <span style={{ marginRight: '8px', color: '#999' }}>•</span>
    )
    
    return (
      <div style={{ 
        paddingLeft: `${paddingLeft}px`,
        display: 'flex',
        alignItems: 'center',
        fontWeight: depth === 0 ? '600' : depth === 1 ? '500' : '400',
        color: depth === 0 ? '#2c3e50' : '#333'
      }}>
        {chevron}
        <span>{data.node_name}</span>
      </div>
    )
  }, [expandedNodes, toggleNodeExpansion])

  // External filter: Hide rows whose parents are not expanded
  const isExternalFilterPresent = useCallback(() => {
    return true // Always use external filter
  }, [])

  const doesExternalFilterPass = useCallback((node: any) => {
    const data = node.data
    if (!data) return false
    
    // Root nodes are always visible
    if (!data.parent_node_id) return true
    
    // Check if all ancestors are expanded
    const checkAncestors = (currentData: any): boolean => {
      if (!currentData.parent_node_id) return true // Reached root
      
      // Find parent in rowData
      const parent = rowData.find(r => r.node_id === currentData.parent_node_id)
      if (!parent) return true // Parent not found, show it
      
      // If parent is not expanded, hide this node
      if (!expandedNodes.has(parent.node_id)) {
        return false
      }
      
      // Recursively check parent's ancestors
      return checkAncestors(parent)
    }
    
    return checkAncestors(data)
  }, [expandedNodes, rowData])

  // Filter columns based on selected report's scopes (only show 'input' scoped columns)
  const columnDefs: ColDef[] = useMemo(() => {
    const cols: ColDef[] = []

    // Node Name column with manual tree renderer
    cols.push({
      field: 'node_name',
      headerName: 'Hierarchy',
      minWidth: 350,
      pinned: 'left',
      cellRenderer: nodeNameCellRenderer,
      cellStyle: (params: any) => {
        const depth = params.data?.depth || 0
        return {
          backgroundColor: depth === 0 ? '#f0f4f8' : depth === 1 ? '#f9f9f9' : '#ffffff',
          borderLeft: depth > 1 ? '1px solid #e0e0e0' : 'none',
        }
      },
    })

    // Add dimension columns if they have 'input' scope (removed redundant Group/Product/Desk columns)
    // Load scope data from ReportRegistration (if available)
    if (selectedReport?.dimension_scopes) {
      const dimScopes = selectedReport.dimension_scopes
      if (dimScopes.region?.includes('input')) {
        cols.push({
          field: 'region',
          headerName: 'Region',
          width: 120,
          valueGetter: (params) => params.data?.region || '',
        })
      }
      if (dimScopes.strategy?.includes('input')) {
        cols.push({
          field: 'strategy',
          headerName: 'Strategy',
          width: 200,
          valueGetter: (params) => params.data?.strategy || '',
        })
      }
    }

    // Add Official GL Baseline
    cols.push({
      field: 'official_gl_baseline',
      headerName: 'Official GL Baseline',
      width: 180,
      valueFormatter: financialFormatter,
      cellClass: 'monospace-number',
      cellClassRules: cellClassRules,
    })

    // Add measure columns if they have 'input' scope
    // Legacy scope support
    if (selectedReport?.measure_scopes) {
      const measureScopes = selectedReport.measure_scopes
      if (measureScopes.daily?.includes('input')) {
        cols.push({
          field: 'daily_pnl',
          headerName: 'Daily P&L',
          width: 150,
          valueFormatter: financialFormatter,
          cellClass: 'monospace-number',
          cellClassRules: cellClassRules,
        })
      }
      if (measureScopes.wtd?.includes('input')) {
        cols.push({
          field: 'wtd_pnl',
          headerName: 'WTD P&L',
          width: 150,
          valueFormatter: financialFormatter,
          cellClass: 'monospace-number',
          cellClassRules: cellClassRules,
        })
      }
      if (measureScopes.mtd?.includes('input')) {
        cols.push({
          field: 'mtd_pnl',
          headerName: 'MTD P&L',
          width: 150,
          valueFormatter: financialFormatter,
          cellClass: 'monospace-number',
          cellClassRules: cellClassRules,
        })
      }
      if (measureScopes.ytd?.includes('input')) {
        cols.push({
          field: 'ytd_pnl',
          headerName: 'YTD P&L',
          width: 150,
          valueFormatter: financialFormatter,
          cellClass: 'monospace-number',
          cellClassRules: cellClassRules,
        })
      }
    } else {
      // Default: show all measures if no report selected
      cols.push(
        { field: 'daily_pnl', headerName: 'Daily P&L', width: 150, valueFormatter: financialFormatter, cellClass: 'monospace-number', cellClassRules: cellClassRules },
        { field: 'mtd_pnl', headerName: 'MTD P&L', width: 150, valueFormatter: financialFormatter, cellClass: 'monospace-number', cellClassRules: cellClassRules },
        { field: 'ytd_pnl', headerName: 'YTD P&L', width: 150, valueFormatter: financialFormatter, cellClass: 'monospace-number', cellClassRules: cellClassRules }
      )
    }

    return cols
  }, [selectedUseCase, financialFormatter, cellClassRules, nodeNameCellRenderer])

  // Grid ready callback
  const onGridReady = (params: any) => {
    setGridApi(params.api)
    setColumnApi(params.columnApi)
    console.log('Grid ready, rowData count:', rowData.length)
    
    // Track row selection for breadcrumbs
    params.api.addEventListener('rowSelected', (event: any) => {
      if (event.node && event.node.selected) {
        setSelectedRow(event.node.data)
      } else {
        setSelectedRow(null)
      }
    })
    
    // Also track on row click
    params.api.addEventListener('rowClicked', (event: any) => {
      if (event.node) {
        setSelectedRow(event.node.data)
      }
    })
    
    // Tree Unification: Apply saved expansion state after grid is ready
    setTimeout(() => {
      if (expandedNodes.size > 0 && params.api) {
        params.api.forEachNode((node: any) => {
          if (node.data && expandedNodes.has(node.data.node_id)) {
            node.setExpanded(true)
          }
        })
      }
    }, 200)
    
    // Trigger external filter after grid is ready
    setTimeout(() => {
      params.api.onFilterChanged()
    }, 100)
  }
  
  // Calculate reconciliation status
  const reconciliationStatus = useMemo(() => {
    if (!reconciliation || !reconciliation.fact_table_sum || !reconciliation.leaf_nodes_sum) return null
    
    try {
      const tolerance = 0.01
      const dailyFact = parseFloat(reconciliation.fact_table_sum.daily) || 0
      const dailyLeaf = parseFloat(reconciliation.leaf_nodes_sum.daily) || 0
      const dailyDiff = Math.abs(dailyFact - dailyLeaf)
      
      const mtdFact = parseFloat(reconciliation.fact_table_sum.mtd) || 0
      const mtdLeaf = parseFloat(reconciliation.leaf_nodes_sum.mtd) || 0
      const mtdDiff = Math.abs(mtdFact - mtdLeaf)
      
      const ytdFact = parseFloat(reconciliation.fact_table_sum.ytd) || 0
      const ytdLeaf = parseFloat(reconciliation.leaf_nodes_sum.ytd) || 0
      const ytdDiff = Math.abs(ytdFact - ytdLeaf)
      
      const isBalanced = dailyDiff <= tolerance && mtdDiff <= tolerance && ytdDiff <= tolerance
      
      return {
        isBalanced,
        daily: { fact: dailyFact, leaf: dailyLeaf, diff: dailyDiff },
        mtd: { fact: mtdFact, leaf: mtdLeaf, diff: mtdDiff },
        ytd: { fact: ytdFact, leaf: ytdLeaf, diff: ytdDiff }
      }
    } catch (e) {
      console.warn('Failed to calculate reconciliation status:', e)
      return null
    }
  }, [reconciliation])
  
  // Build breadcrumb path from selected row
  const breadcrumbPath = useMemo(() => {
    if (!selectedRow) return []
    
    // Use path array if available, otherwise build from hierarchy
    if (selectedRow.path && Array.isArray(selectedRow.path)) {
      return selectedRow.path
    }
    
    // Fallback: build path from parent chain
    const path: string[] = []
    let current = selectedRow
    while (current) {
      path.unshift(current.node_name)
      if (current.parent_node_id) {
        current = rowData.find(r => r.node_id === current.parent_node_id)
      } else {
        break
      }
    }
    return path
  }, [selectedRow, rowData])

  // Global search filter - maintains parent-child visibility
  useEffect(() => {
    if (gridApi) {
      if (searchText) {
        // Use quick filter for global search
        gridApi.setGridOption('quickFilterText', searchText)
        // Expand all nodes to show filtered results
        const allNodeIds = new Set(rowData.map(r => r.node_id).filter(id => !rowData.find(r => r.node_id === id)?.is_leaf))
        setExpandedNodes(allNodeIds)
      } else {
        // Clear filter
        gridApi.setGridOption('quickFilterText', '')
        // Reset to default expansion (first 4 levels)
        const defaultExpanded = new Set<string>()
        rowData.forEach(row => {
          if (row.depth < 4 && !row.is_leaf) {
            defaultExpanded.add(row.node_id)
          }
        })
        setExpandedNodes(defaultExpanded)
      }
      // Trigger filter update
      setTimeout(() => {
        gridApi.onFilterChanged()
      }, 0)
    }
  }, [searchText, gridApi, rowData])

  // Density toggle
  const rowHeight = density === 'comfortable' ? 40 : 32

  // Note: Removed treeData, getDataPath, and autoGroupColumnDef - using manual tree instead

  return (
    <div className={`discovery-screen ${density}`}>
      <div className="discovery-controls">
        <div className="control-group">
          <label htmlFor="use-case-select">Select Use Case:</label>
          <select
            id="use-case-select"
            value={selectedUseCaseId}
            onChange={(e) => {
              setSelectedUseCaseId(e.target.value)
              // Auto-set structure from selected use case
              const selectedUseCase = useCases.find(uc => uc.use_case_id === e.target.value)
              if (selectedUseCase && selectedUseCase.atlas_structure_id) {
                setStructureId(selectedUseCase.atlas_structure_id)
              }
            }}
            disabled={loading || useCases.length === 0}
            className="use-case-select"
          >
            <option value="">-- Select a Use Case --</option>
            {useCases.map((useCase) => (
              <option key={useCase.use_case_id} value={useCase.use_case_id}>
                {useCase.name}
              </option>
            ))}
          </select>
          <label htmlFor="structure-display">Atlas Structure:</label>
          <div 
            id="structure-display"
            className="structure-display" 
            style={{ 
              padding: '0.5rem 1rem', 
              background: '#f3f4f6', 
              border: '1px solid #d1d5db', 
              borderRadius: '4px',
              color: '#374151',
              fontSize: '0.875rem',
              fontWeight: '500',
              display: 'inline-block',
              minWidth: '200px'
            }}
          >
            {structureId ? (
              `Structure: ${availableStructures.find(s => s.structure_id === structureId)?.name || structureId}`
            ) : (
              'Select a Use Case to view Structure'
            )}
          </div>
          <button 
            onClick={loadDiscoveryData} 
            disabled={loading || !structureId}
            className="refresh-button"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        <div className="control-group-right">
          <div className="search-container">
            <input
              type="text"
              placeholder="Search nodes (maintains hierarchy)..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="search-input"
            />
            {searchText && (
              <button
                onClick={() => setSearchText('')}
                className="clear-search"
                title="Clear search"
              >
                ×
              </button>
            )}
          </div>
          <div className="density-toggle">
            <button
              onClick={() => setDensity(density === 'comfortable' ? 'compact' : 'comfortable')}
              className={`density-button ${density}`}
              title={`Switch to ${density === 'comfortable' ? 'Compact' : 'Comfortable'} view`}
            >
              {density === 'comfortable' ? '⊟' : '⊞'}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* Breadcrumb Trail */}
      {breadcrumbPath.length > 0 && (
        <div className="breadcrumb-container">
          <div className="breadcrumb-trail">
            {breadcrumbPath.map((name, idx) => (
              <React.Fragment key={idx}>
                <span className="breadcrumb-item">{name}</span>
                {idx < breadcrumbPath.length - 1 && <span className="breadcrumb-separator">›</span>}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      <div className="discovery-grid-container">
        <div 
          className="ag-theme-alpine discovery-grid"
          style={{ height: '600px', width: '100%' }}
        >
          <AgGridReact
            ref={gridRef}
            rowData={rowData}
            columnDefs={columnDefs}
            suppressRowClickSelection={true}
            rowSelection="multiple"
            animateRows={true}
            getRowStyle={getRowStyle}
            rowHeight={rowHeight}
            headerHeight={density === 'comfortable' ? 45 : 35}
            onGridReady={onGridReady}
            onRowGroupOpened={(params) => {
              // Tree Unification: Sync expansion to shared state
              if (params.node && params.node.data) {
                const nodeId = params.node.data.node_id
                setExpandedNodes(prev => {
                  const next = new Set(prev)
                  next.add(nodeId)
                  return next
                })
              }
            }}
            onRowGroupClosed={(params) => {
              // Tree Unification: Sync expansion to shared state
              if (params.node && params.node.data) {
                const nodeId = params.node.data.node_id
                setExpandedNodes(prev => {
                  const next = new Set(prev)
                  next.delete(nodeId)
                  return next
                })
              }
            }}
            defaultColDef={{
              sortable: true,
              filter: true,
              resizable: true,
            }}
            suppressHorizontalScroll={false}
            suppressVerticalScroll={false}
            isExternalFilterPresent={isExternalFilterPresent}
            doesExternalFilterPass={doesExternalFilterPass}
          />
        </div>
      </div>

      {/* Reconciliation Status Bar */}
      {reconciliationStatus && (
        <div className={`reconciliation-status-bar ${reconciliationStatus.isBalanced ? 'balanced' : 'unbalanced'}`}>
          <div className="status-content">
            <div className="status-indicator">
              {reconciliationStatus.isBalanced ? (
                <span className="status-icon">✅</span>
              ) : (
                <span className="status-icon">⚠️</span>
              )}
              <span className="status-text">
                {reconciliationStatus.isBalanced 
                  ? 'Baseline Balanced ✅' 
                  : 'Baseline Unbalanced - Review Required'}
              </span>
            </div>
            <div className="reconciliation-details">
              <div className="recon-measure">
                <span className="measure-label">Daily:</span>
                <span className="measure-value">
                  Fact Table: {reconciliationStatus.daily.fact.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span className="measure-separator">vs</span>
                <span className="measure-value">
                  Leaf Nodes: {reconciliationStatus.daily.leaf.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span className="measure-diff">
                  (Diff: {reconciliationStatus.daily.diff.toFixed(2)})
                </span>
              </div>
              <div className="recon-measure">
                <span className="measure-label">MTD:</span>
                <span className="measure-value">
                  Fact Table: {reconciliationStatus.mtd.fact.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span className="measure-separator">vs</span>
                <span className="measure-value">
                  Leaf Nodes: {reconciliationStatus.mtd.leaf.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span className="measure-diff">
                  (Diff: {reconciliationStatus.mtd.diff.toFixed(2)})
                </span>
              </div>
              <div className="recon-measure">
                <span className="measure-label">YTD:</span>
                <span className="measure-value">
                  Fact Table: {reconciliationStatus.ytd.fact.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span className="measure-separator">vs</span>
                <span className="measure-value">
                  Leaf Nodes: {reconciliationStatus.ytd.leaf.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
                <span className="measure-diff">
                  (Diff: {reconciliationStatus.ytd.diff.toFixed(2)})
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DiscoveryScreen
