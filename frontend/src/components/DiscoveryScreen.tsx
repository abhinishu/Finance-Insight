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
  const [registeredReports, setRegisteredReports] = useState<any[]>([])
  const [selectedReportId, setSelectedReportId] = useState<string>('')
  const [selectedReport, setSelectedReport] = useState<any>(null)
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
  
  // Load persisted state from localStorage
  useEffect(() => {
    const savedReportId = localStorage.getItem('finance_insight_selected_report_id')
    const savedExpandedNodes = localStorage.getItem('finance_insight_expanded_nodes')
    if (savedReportId) {
      setSelectedReportId(savedReportId)
    }
    if (savedExpandedNodes) {
      try {
        const nodes = JSON.parse(savedExpandedNodes)
        setExpandedNodes(new Set(nodes))
      } catch (e) {
        console.warn('Failed to load expanded nodes from localStorage:', e)
      }
    }
  }, [])
  
  // Persist selected report to localStorage
  useEffect(() => {
    if (selectedReportId) {
      localStorage.setItem('finance_insight_selected_report_id', selectedReportId)
    }
  }, [selectedReportId])
  
  // Persist expanded nodes to localStorage
  useEffect(() => {
    if (expandedNodes.size > 0) {
      localStorage.setItem('finance_insight_expanded_nodes', JSON.stringify(Array.from(expandedNodes)))
    }
  }, [expandedNodes])

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
      const response = await axios.get<{ structures: Structure[] }>(
        `${API_BASE_URL}/api/v1/structures`
      )
      setAvailableStructures(response.data.structures)
    } catch (err: any) {
      console.error('Failed to load structures:', err)
      setError('Failed to load available structures')
    }
  }, [])

  // Load registered reports
  const loadReports = useCallback(async () => {
    try {
      const response = await axios.get<any[]>(
        `${API_BASE_URL}/api/v1/reports`
      )
      setRegisteredReports(response.data)
    } catch (err: any) {
      console.error('Failed to load reports:', err)
    }
  }, [])

  // Load report details when selected
  useEffect(() => {
    if (selectedReportId) {
      const report = registeredReports.find(r => r.report_id === selectedReportId)
      if (report) {
        setSelectedReport(report)
        setStructureId(report.atlas_structure_id)
      }
    }
  }, [selectedReportId, registeredReports])

  const loadDiscoveryData = useCallback(async () => {
    if (!structureId) return

    setLoading(true)
    setError(null)
    
    try {
      const response = await axios.get<DiscoveryResponse>(
        `${API_BASE_URL}/api/v1/discovery`,
        { params: { structure_id: structureId } }
      )
      
      // Convert nested hierarchy to flat structure with path arrays from SQL CTE
      const flatData = flattenHierarchy(response.data.hierarchy)
      
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
    loadStructures()
    loadReports()
  }, [loadStructures, loadReports])

  useEffect(() => {
    if (structureId) {
      loadDiscoveryData()
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
  }, [selectedReport, financialFormatter, cellClassRules, nodeNameCellRenderer])

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
          <label htmlFor="report-select">Select Report:</label>
          <select
            id="report-select"
            value={selectedReportId}
            onChange={(e) => setSelectedReportId(e.target.value)}
            disabled={loading || registeredReports.length === 0}
            className="report-select"
          >
            <option value="">-- Select a Report --</option>
            {registeredReports.map((report) => (
              <option key={report.report_id} value={report.report_id}>
                {report.report_name}
              </option>
            ))}
          </select>
          <label htmlFor="structure-select">Atlas Structure:</label>
          <select
            id="structure-select"
            value={structureId}
            onChange={(e) => setStructureId(e.target.value)}
            disabled={loading || availableStructures.length === 0}
            className="structure-select"
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
