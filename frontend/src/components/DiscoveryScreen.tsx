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
  children: HierarchyNode[]
}

interface DiscoveryResponse {
  structure_id: string
  hierarchy: HierarchyNode[]
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const DiscoveryScreen: React.FC = () => {
  const [structureId, setStructureId] = useState<string>('MOCK_ATLAS_v1')
  const [availableStructures, setAvailableStructures] = useState<string[]>(['MOCK_ATLAS_v1'])
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [rowData, setRowData] = useState<any[]>([])

  // Convert nested hierarchy to flat structure for AG-Grid tree data
  const flattenHierarchy = (nodes: HierarchyNode[]): any[] => {
    const flat: any[] = []
    
    const processNode = (node: HierarchyNode, parentPath: string[] = []) => {
      const currentPath = [...parentPath, node.node_id]
      
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
        // AG-Grid tree data: path array
        path: currentPath,
      }
      flat.push(flatNode)
      
      // Process children recursively
      if (node.children && node.children.length > 0) {
        node.children.forEach(child => processNode(child, currentPath))
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

  useEffect(() => {
    if (structureId) {
      loadDiscoveryData()
    }
  }, [structureId])

  const columnDefs: ColDef[] = [
    {
      field: 'node_name',
      headerName: 'Node Name',
      width: 300,
      cellRenderer: 'agGroupCellRenderer',
    },
    {
      field: 'node_id',
      headerName: 'Node ID',
      width: 150,
    },
    {
      field: 'depth',
      headerName: 'Depth',
      width: 100,
    },
    {
      field: 'daily_pnl',
      headerName: 'Daily P&L',
      width: 150,
      valueFormatter: (params) => {
        if (params.value == null) return ''
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 2,
        }).format(params.value)
      },
    },
    {
      field: 'mtd_pnl',
      headerName: 'MTD P&L',
      width: 150,
      valueFormatter: (params) => {
        if (params.value == null) return ''
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 2,
        }).format(params.value)
      },
    },
    {
      field: 'ytd_pnl',
      headerName: 'YTD P&L',
      width: 150,
      valueFormatter: (params) => {
        if (params.value == null) return ''
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 2,
        }).format(params.value)
      },
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
            disabled={loading}
          >
            {availableStructures.map((struct) => (
              <option key={struct} value={struct}>
                {struct}
              </option>
            ))}
          </select>
          <button onClick={loadDiscoveryData} disabled={loading}>
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

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

