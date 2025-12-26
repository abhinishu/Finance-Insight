// Note: Using manual tree implementation - no Enterprise required
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridApi, ColumnApi } from 'ag-grid-community'
import axios from 'axios'
import { useReportingContext } from '../contexts/ReportingContext'
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
  debug_info?: {
    source_table?: string
    row_count?: number
    use_case_id?: string
    use_case_name?: string
    [key: string]: any
  }
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const DiscoveryScreen: React.FC = () => {
  // Use ReportingContext for globalTotal
  const { setGlobalTotal } = useReportingContext()
  
  const [structureId, setStructureId] = useState<string>('')
  const [availableStructures, setAvailableStructures] = useState<Structure[]>([])
  const [useCases, setUseCases] = useState<any[]>([])
  const [selectedUseCaseId, setSelectedUseCaseId] = useState<string>('')
  const [selectedUseCase, setSelectedUseCase] = useState<any>(null)
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
  // FIX: Remove structureId from dependencies to prevent infinite loop
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
      
      // Auto-select first structure if none selected (use functional update to avoid dependency)
      setStructureId(prevStructureId => {
        if (structures.length > 0 && !prevStructureId) {
          const firstStructure = structures[0]
          console.log('Tab 2: Auto-selecting first structure:', firstStructure.structure_id)
          return firstStructure.structure_id
        }
        return prevStructureId
      })
      
      if (structures.length === 0) {
        console.warn('Tab 2: No structures found')
        setError('No structures available. Please ensure mock data has been generated.')
      }
    } catch (err: any) {
      console.error('Tab 2: Failed to load structures:', err)
      console.error('Tab 2: Error details:', err.response?.data || err.message)
      setError(`Failed to load available structures: ${err.response?.data?.detail || err.message}`)
    }
  }, []) // FIX: Empty dependency array - load once on mount

  // Load use cases
  const loadUseCases = useCallback(async () => {
    try {
      console.log('Tab 2: Loading use cases from:', `${API_BASE_URL}/api/v1/use-cases`)
      const response = await axios.get(`${API_BASE_URL}/api/v1/use-cases`)
      const useCasesList = response.data.use_cases || []
      console.log('Tab 2: Use cases API response:', useCasesList)
      console.log('Tab 2: Found', useCasesList.length, 'use cases')
      setUseCases(useCasesList)
    } catch (err: any) {
      console.error('Tab 2: Failed to load use cases:', err)
      console.error('Tab 2: Error details:', err.response?.data || err.message)
      setUseCases([])
      // Don't set error for use cases - it's okay if there are no use cases yet
    }
  }, [])

  // FIX: Use ref to prevent double-firing in React Strict Mode
  const initialized = useRef(false)
  const metadataLoaded = useRef(false)

  // Load metadata (structures and use cases) ONCE on mount
  useEffect(() => {
    if (!initialized.current) {
      initialized.current = true
      console.log('Tab 2: Component mounted, loading structures and use cases...')
      loadStructures()
      loadUseCases()
      metadataLoaded.current = true
    }
  }, []) // FIX: Empty dependency array - run once on mount

  // Listen for use case deletion events to refresh the list
  // FIX: Use ref to access current state without dependencies
  const useCasesRef = useRef<any[]>([])
  useEffect(() => {
    useCasesRef.current = useCases
  }, [useCases])

  const selectedUseCaseIdRef = useRef<string>('')
  useEffect(() => {
    selectedUseCaseIdRef.current = selectedUseCaseId
  }, [selectedUseCaseId])

  useEffect(() => {
    const handleUseCaseDeleted = async () => {
      await loadUseCases()
      // Clear selection if the deleted use case was selected
      // Use refs to access current values without dependencies
      const currentUseCaseId = selectedUseCaseIdRef.current
      const currentUseCases = useCasesRef.current
      
      if (currentUseCaseId) {
        const stillExists = currentUseCases.find(uc => uc.use_case_id === currentUseCaseId)
        if (!stillExists) {
          setSelectedUseCaseId('')
          setSelectedUseCase(null)
          setStructureId('')
        }
      }
    }

    window.addEventListener('useCaseDeleted', handleUseCaseDeleted as EventListener)
    return () => {
      window.removeEventListener('useCaseDeleted', handleUseCaseDeleted as EventListener)
    }
  }, [loadUseCases]) // Only depend on loadUseCases (which has empty deps)

  // Load use case details when selected and auto-populate Atlas Structure
  useEffect(() => {
    if (selectedUseCaseId) {
      const useCase = useCases.find(uc => uc.use_case_id === selectedUseCaseId)
      if (useCase) {
        setSelectedUseCase(useCase)
        // Auto-populate Atlas Structure from use case
        if (useCase.atlas_structure_id) {
          setStructureId(useCase.atlas_structure_id)
        }
      }
    } else {
      setSelectedUseCase(null)
      setStructureId('')
    }
  }, [selectedUseCaseId, useCases])

  // FIX: loadDiscoveryData should use current state values, not closure variables
  // Remove useCallback dependencies to ensure it always uses fresh state
  const loadDiscoveryData = useCallback(async (useCaseId?: string, structId?: string) => {
    // Use provided parameters or fall back to current state
    const currentUseCaseId = useCaseId || selectedUseCaseId
    const currentStructureId = structId || structureId
    
    // CRITICAL: Guard to prevent loading without use_case_id
    if (!currentUseCaseId) {
      console.warn('Tab 2: Cannot load discovery data - no use_case_id selected')
      return
    }
    
    if (!currentStructureId) {
      console.warn('Tab 2: Cannot load discovery data - no structure_id')
      return
    }

    setLoading(true)
    setError(null)
    
    // OPTIONAL: Clear grid immediately to show user something is happening
    setRowData([])
    
    try {
      console.log(`Tab 2: Fetching Tab 2 for Use Case: ${currentUseCaseId}, structure: ${currentStructureId}`)
      // CACHE BUSTING: Append timestamp to force fresh request and prevent "Ghost Data"
      const timestamp = Date.now()
      const params: any = { 
        structure_id: currentStructureId,
        use_case_id: currentUseCaseId,  // MANDATORY: Always pass use_case_id
        t: timestamp  // Cache busting parameter
      }
      const response = await axios.get<DiscoveryResponse>(
        `${API_BASE_URL}/api/v1/discovery`,
        { params }
      )
      
      // CRITICAL: Log RAW API response to verify backend is sending correct data
      console.log("RAW API RESPONSE:", JSON.stringify(response.data, null, 2))
      
      // Log debug_info from backend
      if (response.data?.debug_info) {
        console.log('Tab 2: Backend debug_info:', response.data.debug_info)
        console.log(`Tab 2: Source Table: ${response.data.debug_info.source_table}, Row Count: ${response.data.debug_info.row_count}, Use Case ID: ${response.data.debug_info.use_case_id}`)
      }
      
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
  }, [selectedUseCaseId, structureId, flattenHierarchy, gridApi]) // FIX: Include selectedUseCaseId in dependencies

  // REMOVED: Duplicate initialization useEffect - now handled by the ref-based useEffect above

  // SEPARATION OF CONCERNS: Data Load (Run on Use Case Change)
  // This hook specifically watches selectedUseCaseId and triggers data refresh
  useEffect(() => {
    console.log('Tab 2: useEffect [selectedUseCaseId] triggered, selectedUseCaseId:', selectedUseCaseId)
    if (selectedUseCaseId && structureId) {
      console.log('Tab 2: Use case changed, refreshing data for:', selectedUseCaseId)
      // Clear grid immediately to show user something is happening
      setRowData([])
      // Load fresh data with current use case ID (pass parameters to use fresh values)
      loadDiscoveryData(selectedUseCaseId, structureId)
    } else {
      console.warn('Tab 2: useEffect: selectedUseCaseId or structureId is empty, not loading discovery data')
    }
  }, [selectedUseCaseId, structureId, loadDiscoveryData]) // CRITICAL: Include all dependencies

  // Note: We don't need a separate structureId useEffect because the above hook already watches both
  // This prevents duplicate calls when both values change

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

  // Generate columns based on selected use case (show all columns when use case is selected)
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

    // Add measure columns (always show Daily, MTD, YTD P&L)
    cols.push(
      { field: 'daily_pnl', headerName: 'Daily P&L', width: 150, valueFormatter: financialFormatter, cellClass: 'monospace-number', cellClassRules: cellClassRules },
      { field: 'mtd_pnl', headerName: 'MTD P&L', width: 150, valueFormatter: financialFormatter, cellClass: 'monospace-number', cellClassRules: cellClassRules },
      { field: 'ytd_pnl', headerName: 'YTD P&L', width: 150, valueFormatter: financialFormatter, cellClass: 'monospace-number', cellClassRules: cellClassRules }
    )

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
            onChange={(e) => setSelectedUseCaseId(e.target.value)}
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
          <label htmlFor="structure-select">Atlas Structure:</label>
          <select
            id="structure-select"
            value={structureId}
            onChange={(e) => setStructureId(e.target.value)}
            disabled={loading || availableStructures.length === 0 || !!selectedUseCaseId}
            className="structure-select"
            style={{
              backgroundColor: selectedUseCaseId ? '#f3f4f6' : 'white',
              cursor: selectedUseCaseId ? 'not-allowed' : 'pointer'
            }}
            title={selectedUseCaseId ? 'Atlas Structure is set by the selected Use Case and cannot be changed here' : 'Select an Atlas Structure'}
          >
            {availableStructures.length === 0 ? (
              <option value="">Loading structures...</option>
            ) : (
              availableStructures.map((struct) => (
                <option key={struct.structure_id} value={struct.structure_id}>
                  {struct.name} ({struct.node_count} nodes)
                </option>
              ))
            )}
          </select>
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

// Optimize tab switching: Use React.memo to prevent unnecessary re-renders
export default React.memo(DiscoveryScreen)
