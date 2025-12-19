import React, { useState, useEffect } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef } from 'ag-grid-community'
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
  children: HierarchyNode[]
}

interface Structure {
  structure_id: string
  name: string
  node_count: number
}

interface DiscoveryResponse {
  structure_id: string
  hierarchy: HierarchyNode[]
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const DiscoveryScreen: React.FC = () => {
  const [structureId, setStructureId] = useState<string>('')
  const [availableStructures, setAvailableStructures] = useState<Structure[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [rowData, setRowData] = useState<any[]>([])
  const [showUseCaseModal, setShowUseCaseModal] = useState<boolean>(false)
  const [useCaseName, setUseCaseName] = useState<string>('')
  const [useCaseDescription, setUseCaseDescription] = useState<string>('')

  // Load available structures from API
  const loadStructures = async () => {
    try {
      const response = await axios.get<{ structures: Structure[] }>(
        `${API_BASE_URL}/api/v1/structures`
      )
      setAvailableStructures(response.data.structures)
      if (response.data.structures.length > 0 && !structureId) {
        setStructureId(response.data.structures[0].structure_id)
      }
    } catch (err: any) {
      console.error('Failed to load structures:', err)
      setError('Failed to load available structures')
    }
  }

  // Convert nested hierarchy to flat structure for AG-Grid tree data
  const flattenHierarchy = (nodes: HierarchyNode[]): any[] => {
    const flat: any[] = []
    
    const processNode = (node: HierarchyNode, parentPath: string[] = [], parentAttrs: any = {}) => {
      const currentPath = [...parentPath, node.node_id]
      
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
        // AG-Grid tree data: path array
        path: currentPath,
      }
      flat.push(flatNode)
      
      // Process children recursively (pass current attributes for inheritance)
      const currentAttrs = { region, product, desk, strategy }
      if (node.children && node.children.length > 0) {
        node.children.forEach(child => processNode(child, currentPath, currentAttrs))
      }
    }
    
    nodes.forEach(node => processNode(node))
    return flat
  }

  const loadDiscoveryData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await axios.get<DiscoveryResponse>(
        `${API_BASE_URL}/api/v1/discovery`,
        { params: { structure_id: structureId } }
      )
      
      // Convert nested hierarchy to flat structure
      const flatData = flattenHierarchy(response.data.hierarchy)
      setRowData(flatData)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load discovery data')
      setRowData([])
    } finally {
      setLoading(false)
    }
  }

  // Load structures on mount
  useEffect(() => {
    loadStructures()
  }, [])

  useEffect(() => {
    if (structureId) {
      loadDiscoveryData()
    }
  }, [structureId])

  // Save as new use case
  const saveAsUseCase = async () => {
    if (!useCaseName.trim()) {
      alert('Please enter a use case name')
      return
    }

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/use-cases`,
        null,
        {
          params: {
            name: useCaseName,
            description: useCaseDescription,
            owner_id: 'current_user', // TODO: Get from auth context
            atlas_structure_id: structureId
          }
        }
      )
      alert(`Use case "${useCaseName}" created successfully!`)
      setShowUseCaseModal(false)
      setUseCaseName('')
      setUseCaseDescription('')
    } catch (err: any) {
      alert(`Failed to create use case: ${err.response?.data?.detail || err.message}`)
    }
  }

  const currencyFormatter = (params: any) => {
    if (params.value == null) return ''
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(params.value)
  }

  const columnDefs: ColDef[] = [
    {
      field: 'node_name',
      headerName: 'Node Name',
      width: 250,
      cellRenderer: 'agGroupCellRenderer',
      pinned: 'left',
    },
    {
      field: 'region',
      headerName: 'Region',
      width: 120,
      valueGetter: (params) => params.data?.region || '',
    },
    {
      field: 'product',
      headerName: 'Product',
      width: 150,
      valueGetter: (params) => params.data?.product || '',
    },
    {
      field: 'desk',
      headerName: 'Desk',
      width: 150,
      valueGetter: (params) => params.data?.desk || '',
    },
    {
      field: 'strategy',
      headerName: 'Strategy',
      width: 200,
      valueGetter: (params) => params.data?.strategy || '',
    },
    {
      field: 'official_gl_baseline',
      headerName: 'Official GL Baseline',
      width: 180,
      valueFormatter: currencyFormatter,
      cellStyle: { backgroundColor: '#f0f8ff' }, // Light blue background
    },
    {
      field: 'daily_pnl',
      headerName: 'Daily P&L',
      width: 150,
      valueFormatter: currencyFormatter,
    },
    {
      field: 'mtd_pnl',
      headerName: 'MTD P&L',
      width: 150,
      valueFormatter: currencyFormatter,
    },
    {
      field: 'ytd_pnl',
      headerName: 'YTD P&L',
      width: 150,
      valueFormatter: currencyFormatter,
    },
  ]

  const getDataPath = (data: any): string[] => {
    return data.path || []
  }

  return (
    <div className="discovery-screen">
      <div className="discovery-controls">
        <div className="control-group">
          <label htmlFor="structure-select">Atlas Structure:</label>
          <select
            id="structure-select"
            value={structureId}
            onChange={(e) => setStructureId(e.target.value)}
            disabled={loading || availableStructures.length === 0}
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
          <button onClick={loadDiscoveryData} disabled={loading || !structureId}>
            {loading ? 'Loading...' : 'Refresh'}
          </button>
          <button 
            onClick={() => setShowUseCaseModal(true)} 
            disabled={!structureId || loading}
            style={{ marginLeft: '10px', backgroundColor: '#4CAF50', color: 'white' }}
          >
            Save as New Use Case
          </button>
        </div>
      </div>

      {showUseCaseModal && (
        <div className="modal-overlay" onClick={() => setShowUseCaseModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Create New Use Case</h3>
            <div className="form-group">
              <label>Use Case Name:</label>
              <input
                type="text"
                value={useCaseName}
                onChange={(e) => setUseCaseName(e.target.value)}
                placeholder="e.g., America Trading P&L"
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
              />
            </div>
            <div className="form-group" style={{ marginTop: '15px' }}>
              <label>Description (optional):</label>
              <textarea
                value={useCaseDescription}
                onChange={(e) => setUseCaseDescription(e.target.value)}
                placeholder="Describe this use case..."
                style={{ width: '100%', padding: '8px', marginTop: '5px', minHeight: '60px' }}
              />
            </div>
            <div style={{ marginTop: '20px', display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowUseCaseModal(false)}>Cancel</button>
              <button onClick={saveAsUseCase} style={{ backgroundColor: '#4CAF50', color: 'white' }}>
                Create Use Case
              </button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          Error: {error}
        </div>
      )}

      <div className="discovery-grid">
        <div className="ag-theme-alpine" style={{ height: '600px', width: '100%' }}>
          <AgGridReact
            rowData={rowData}
            columnDefs={columnDefs}
            treeData={true}
            getDataPath={getDataPath}
            groupDefaultExpanded={1}
            animateRows={true}
            enableCellTextSelection={true}
            suppressRowClickSelection={true}
          />
        </div>
      </div>

      <div className="discovery-info">
        <p>
          <strong>Natural Values:</strong> These are the initial rollups calculated from fact data.
          No business rules have been applied yet.
        </p>
        <p>
          <strong>Measures:</strong> Daily P&L, MTD (Month-to-Date), YTD (Year-to-Date)
        </p>
      </div>
    </div>
  )
}

export default DiscoveryScreen

