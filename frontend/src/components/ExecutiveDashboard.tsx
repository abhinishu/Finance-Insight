import React, { useState, useEffect, useRef, useCallback } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridApi, ColumnApi } from 'ag-grid-community'
import axios from 'axios'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import './ExecutiveDashboard.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface UseCase {
  use_case_id: string
  name: string
  atlas_structure_id: string
}

interface ResultsNode {
  node_id: string
  node_name: string
  parent_node_id: string | null
  depth: number
  is_leaf: boolean
  natural_value: { daily: string; mtd: string; ytd: string; pytd: string }
  adjusted_value: { daily: string; mtd: string; ytd: string; pytd: string }
  plug: { daily: string; mtd: string; ytd: string; pytd: string }
  is_override: boolean
  is_reconciled: boolean
  rule?: {
    rule_id: number | null
    logic_en: string | null
    sql_where: string | null
  } | null
  path?: string[] | null
  children: ResultsNode[]
}

interface UseCaseRun {
  run_id: string
  version_tag: string
  run_timestamp: string
}

interface ResultsResponse {
  run_id: string
  use_case_id: string
  version_tag: string
  run_timestamp: string
  hierarchy: ResultsNode[]
}

const ExecutiveDashboard: React.FC = () => {
  // Use Case Management
  const [useCases, setUseCases] = useState<UseCase[]>([])
  const [selectedUseCaseId, setSelectedUseCaseId] = useState<string>('')
  const [selectedUseCase, setSelectedUseCase] = useState<UseCase | null>(null)

  // Run Management
  const [runs, setRuns] = useState<UseCaseRun[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string>('')

  // Data
  const [rowData, setRowData] = useState<any[]>([])
  const [gridApi, setGridApi] = useState<GridApi | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // Side Drawer
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false)
  const [selectedRule, setSelectedRule] = useState<ResultsNode | null>(null)

  // View Mode
  const [viewMode, setViewMode] = useState<'standard' | 'delta' | 'drilldown'>('standard')
  const [traceNode, setTraceNode] = useState<ResultsNode | null>(null)
  const [traceOpen, setTraceOpen] = useState<boolean>(false)

  // Freshness & Outdated Warning
  const [lastCalculated, setLastCalculated] = useState<string | null>(null)
  const [rulesLastModified, setRulesLastModified] = useState<string | null>(null)
  const [isCalculationOutdated, setIsCalculationOutdated] = useState<boolean>(false)

  const gridRef = useRef<AgGridReact>(null)

  // Load use cases
  useEffect(() => {
    loadUseCases()
  }, [])

  // Load runs when use case changes
  useEffect(() => {
    if (selectedUseCaseId) {
      loadRuns(selectedUseCaseId)
      checkCalculationFreshness(selectedUseCaseId)
    }
  }, [selectedUseCaseId])

  // Load results when run is selected
  useEffect(() => {
    if (selectedUseCaseId && selectedRunId) {
      loadResults(selectedUseCaseId, selectedRunId)
    }
  }, [selectedUseCaseId, selectedRunId])

  const loadUseCases = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/use-cases`)
      const useCasesList = response.data.use_cases || []
      setUseCases(useCasesList)
      
      if (useCasesList.length > 0 && !selectedUseCaseId) {
        setSelectedUseCaseId(useCasesList[0].use_case_id)
        setSelectedUseCase(useCasesList[0])
      }
    } catch (err: any) {
      console.error('Failed to load use cases:', err)
      setError('Failed to load use cases.')
    }
  }

  const loadRuns = async (useCaseId: string) => {
    try {
      // Get use case details to find runs
      const response = await axios.get(`${API_BASE_URL}/api/v1/use-cases/${useCaseId}`)
      // Note: We'll need to add a runs endpoint or get runs from results
      // For now, we'll load the most recent run when loading results
      setRuns([])
    } catch (err: any) {
      console.error('Failed to load runs:', err)
    }
  }

  const loadResults = async (useCaseId: string, runId?: string) => {
    setLoading(true)
    setError(null)

    try {
      const url = runId
        ? `${API_BASE_URL}/api/v1/use-cases/${useCaseId}/results?run_id=${runId}`
        : `${API_BASE_URL}/api/v1/use-cases/${useCaseId}/results`
      
      const response = await axios.get<ResultsResponse>(url)
      
      // Store last calculated timestamp
      if (response.data.run_timestamp) {
        setLastCalculated(response.data.run_timestamp)
      }
      
      const hierarchy = response.data.hierarchy || []
      if (hierarchy.length === 0) {
        setError('No results found. Please run a calculation first.')
        setRowData([])
        setLoading(false)
        return
      }

      // Flatten hierarchy for AG-Grid
      const flatData = flattenHierarchy(hierarchy)
      setRowData(flatData)
      
      // Check if calculation is outdated (compare with rules last modified)
      await checkCalculationFreshness(useCaseId)
    } catch (err: any) {
      console.error('Failed to load results:', err)
      setError(err.response?.data?.detail || 'Failed to load results.')
    } finally {
      setLoading(false)
    }
  }

  // Check if calculation is outdated
  const checkCalculationFreshness = async (useCaseId: string) => {
    try {
      // Get latest rule modification time
      const rulesResponse = await axios.get(
        `${API_BASE_URL}/api/v1/use-cases/${useCaseId}/rules`
      )
      const rules = rulesResponse.data || []
      
      if (rules.length > 0) {
        // Find most recent rule modification
        const latestRule = rules.reduce((latest: any, rule: any) => {
          if (!latest) return rule
          return new Date(rule.last_modified_at) > new Date(latest.last_modified_at) ? rule : latest
        }, null)
        
        if (latestRule && latestRule.last_modified_at) {
          setRulesLastModified(latestRule.last_modified_at)
          
          // Compare with last calculated time
          if (lastCalculated && new Date(latestRule.last_modified_at) > new Date(lastCalculated)) {
            setIsCalculationOutdated(true)
          } else {
            setIsCalculationOutdated(false)
          }
        }
      }
    } catch (err: any) {
      console.error('Failed to check calculation freshness:', err)
    }
  }

  // Load calculation trace for a node
  const loadCalculationTrace = async (node: ResultsNode) => {
    setTraceNode(node)
    setTraceOpen(true)
    // TODO: Implement trace API endpoint to get exact math steps
    // For now, we'll show the node's calculation path
  }

  const flattenHierarchy = (nodes: ResultsNode[], parentPath: string[] = []): any[] => {
    const result: any[] = []
    
    for (const node of nodes) {
      const path = node.path || parentPath.concat([node.node_name])
      
      // Calculate if node has a plug (non-zero)
      const hasPlug = Math.abs(parseFloat(node.plug.daily)) > 0.01 ||
                     Math.abs(parseFloat(node.plug.mtd)) > 0.01 ||
                     Math.abs(parseFloat(node.plug.ytd)) > 0.01

      const row = {
        ...node,
        path,
        // AG-Grid tree data
        group: !node.is_leaf,
        // Helper for conditional formatting
        hasPlug,
      }
      result.push(row)
      
      if (node.children && node.children.length > 0) {
        result.push(...flattenHierarchy(node.children, path))
      }
    }
    
    return result
  }

  // AG-Grid Column Definitions (dynamic based on view mode)
  const getColumnDefs = (): ColDef[] => {
    const baseColumns: ColDef[] = [
      {
        field: 'node_name',
        headerName: 'Dimension Node',
        flex: 2,
        cellRenderer: 'agGroupCellRenderer',
      },
    ]

    if (viewMode === 'standard') {
      // Standard: Show Natural, Adjusted, Plug
      return [
        ...baseColumns,
        {
          field: 'natural_value',
          headerName: 'Natural GL',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.natural_value?.daily || 0),
          valueFormatter: (params) => {
            if (!params.value) return '$0.00'
            return `$${params.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
          },
          cellStyle: { textAlign: 'right', cursor: 'pointer' },
          onCellClicked: (params) => {
            if (viewMode === 'drilldown') {
              loadCalculationTrace(params.data)
            }
          },
        },
        {
          field: 'adjusted_value',
          headerName: 'Adjusted P&L',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.adjusted_value?.daily || 0),
          valueFormatter: (params) => {
            if (!params.value) return '$0.00'
            return `$${params.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
          },
          cellStyle: { textAlign: 'right', cursor: 'pointer' },
          onCellClicked: (params) => {
            if (viewMode === 'drilldown') {
              loadCalculationTrace(params.data)
            }
          },
        },
        {
          field: 'plug',
          headerName: 'Reconciliation Plug',
          headerTooltip: 'Plug = Natural GL - Adjusted P&L (Golden Equation: Natural = Adjusted + Plug)',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.plug?.daily || 0),
          valueFormatter: (params) => {
            if (!params.value) return '$0.00'
            const value = params.value
            const formatted = `$${Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            return value < 0 ? `(${formatted})` : formatted
          },
          cellStyle: (params) => {
            const value = parseFloat(params.data?.plug?.daily || 0)
            const baseStyle: any = { textAlign: 'right', cursor: 'pointer' }
            if (Math.abs(value) > 0.01) {
              baseStyle.color = '#d97706' // Amber color
              baseStyle.fontWeight = '600'
            }
            return baseStyle
          },
          onCellClicked: (params) => {
            if (viewMode === 'drilldown') {
              loadCalculationTrace(params.data)
            } else if (params.data?.rule && Math.abs(parseFloat(params.data.plug?.daily || 0)) > 0.01) {
              setSelectedRule(params.data)
              setDrawerOpen(true)
            }
          },
        },
        {
          field: 'rule',
          headerName: 'Rule Reference',
          flex: 1,
          cellRenderer: (params: any) => {
            if (!params.data?.rule?.logic_en) {
              return '<span style="color: #999;">—</span>'
            }
            return `<span class="rule-badge">Rule #${params.data.rule.rule_id || 'N/A'}</span>`
          },
          cellStyle: { textAlign: 'center' },
        },
      ]
    } else if (viewMode === 'delta') {
      // Delta Mode: Only show Plug and Variance %
      return [
        ...baseColumns,
        {
          field: 'plug',
          headerName: 'Reconciliation Plug',
          flex: 1.5,
          valueGetter: (params) => parseFloat(params.data?.plug?.daily || 0),
          valueFormatter: (params) => {
            if (!params.value) return '$0.00'
            const value = params.value
            const formatted = `$${Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            return value < 0 ? `(${formatted})` : formatted
          },
          cellStyle: (params) => {
            const value = parseFloat(params.data?.plug?.daily || 0)
            const baseStyle: any = { textAlign: 'right', cursor: 'pointer' }
            if (Math.abs(value) > 0.01) {
              baseStyle.color = '#d97706'
              baseStyle.fontWeight = '600'
            }
            return baseStyle
          },
          onCellClicked: (params) => {
            if (params.data?.rule && Math.abs(parseFloat(params.data.plug?.daily || 0)) > 0.01) {
              setSelectedRule(params.data)
              setDrawerOpen(true)
            }
          },
        },
        {
          field: 'variance',
          headerName: 'Variance %',
          flex: 1,
          valueGetter: (params) => {
            const natural = parseFloat(params.data?.natural_value?.daily || 0)
            const adjusted = parseFloat(params.data?.adjusted_value?.daily || 0)
            if (Math.abs(natural) < 0.01) return 0
            return ((adjusted - natural) / Math.abs(natural)) * 100
          },
          valueFormatter: (params) => {
            if (params.value === null || params.value === undefined) return '0.00%'
            return `${params.value.toFixed(2)}%`
          },
          cellStyle: (params) => {
            const value = params.value || 0
            const baseStyle: any = { textAlign: 'right' }
            if (Math.abs(value) > 0.01) {
              baseStyle.color = value < 0 ? '#dc2626' : '#059669'
              baseStyle.fontWeight = '600'
            }
            return baseStyle
          },
        },
      ]
    } else {
      // Drill-Down mode: Same as standard but cells are clickable for trace
      const standardCols = [
        ...baseColumns,
        {
          field: 'natural_value',
          headerName: 'Natural GL',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.natural_value?.daily || 0),
          valueFormatter: (params) => {
            if (!params.value) return '$0.00'
            return `$${params.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
          },
          cellStyle: { textAlign: 'right', cursor: 'pointer' },
          onCellClicked: (params) => loadCalculationTrace(params.data),
        },
        {
          field: 'adjusted_value',
          headerName: 'Adjusted P&L',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.adjusted_value?.daily || 0),
          valueFormatter: (params) => {
            if (!params.value) return '$0.00'
            return `$${params.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
          },
          cellStyle: { textAlign: 'right', cursor: 'pointer' },
          onCellClicked: (params) => loadCalculationTrace(params.data),
        },
        {
          field: 'plug',
          headerName: 'Reconciliation Plug',
          headerTooltip: 'Plug = Natural GL - Adjusted P&L (Golden Equation: Natural = Adjusted + Plug)',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.plug?.daily || 0),
          valueFormatter: (params) => {
            if (!params.value) return '$0.00'
            const value = params.value
            const formatted = `$${Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            return value < 0 ? `(${formatted})` : formatted
          },
          cellStyle: (params) => {
            const value = parseFloat(params.data?.plug?.daily || 0)
            const baseStyle: any = { textAlign: 'right', cursor: 'pointer' }
            if (Math.abs(value) > 0.01) {
              baseStyle.color = '#d97706'
              baseStyle.fontWeight = '600'
            }
            return baseStyle
          },
          onCellClicked: (params) => loadCalculationTrace(params.data),
        },
        {
          field: 'rule',
          headerName: 'Rule Reference',
          flex: 1,
          cellRenderer: (params: any) => {
            if (!params.data?.rule?.logic_en) {
              return '<span style="color: #999;">—</span>'
            }
            return `<span class="rule-badge">Rule #${params.data.rule.rule_id || 'N/A'}</span>`
          },
          cellStyle: { textAlign: 'center' },
        },
      ]
      return standardCols
    }
  }

  const columnDefs = getColumnDefs()

  const defaultColDef: ColDef = {
    sortable: true,
    filter: true,
    resizable: true,
  }

  const onGridReady = (params: { api: GridApi; columnApi: ColumnApi }) => {
    setGridApi(params.api)
  }

  // Row style for conditional formatting (amber highlight for plugs)
  const getRowStyle = (params: any) => {
    if (params.data?.hasPlug) {
      return { backgroundColor: '#fef3c7' } // Amber background
    }
    return {}
  }

  // Export Reconciliation CSV
  const handleExportReconciliation = () => {
    if (!gridApi) return

    const rowsWithPlug: any[] = []
    gridApi.forEachNode((node) => {
      if (node.data) {
        const plugDaily = parseFloat(node.data.plug?.daily || 0)
        const plugMtd = parseFloat(node.data.plug?.mtd || 0)
        const plugYtd = parseFloat(node.data.plug?.ytd || 0)
        
        if (Math.abs(plugDaily) > 0.01 || Math.abs(plugMtd) > 0.01 || Math.abs(plugYtd) > 0.01) {
          rowsWithPlug.push({
            'Node ID': node.data.node_id,
            'Node Name': node.data.node_name,
            'Natural GL (Daily)': node.data.natural_value?.daily || '0',
            'Adjusted P&L (Daily)': node.data.adjusted_value?.daily || '0',
            'Plug (Daily)': node.data.plug?.daily || '0',
            'Natural GL (MTD)': node.data.natural_value?.mtd || '0',
            'Adjusted P&L (MTD)': node.data.adjusted_value?.mtd || '0',
            'Plug (MTD)': node.data.plug?.mtd || '0',
            'Natural GL (YTD)': node.data.natural_value?.ytd || '0',
            'Adjusted P&L (YTD)': node.data.adjusted_value?.ytd || '0',
            'Plug (YTD)': node.data.plug?.ytd || '0',
            'Rule ID': node.data.rule?.rule_id || '',
            'Rule Description': node.data.rule?.logic_en || '',
            'SQL WHERE': node.data.rule?.sql_where || '',
          })
        }
      }
    })

    if (rowsWithPlug.length === 0) {
      alert('No reconciliation plugs found to export.')
      return
    }

    // Convert to CSV
    const headers = Object.keys(rowsWithPlug[0])
    const csvRows = [
      headers.join(','),
      ...rowsWithPlug.map(row =>
        headers.map(header => {
          const value = row[header]
          // Escape quotes and wrap in quotes if contains comma
          if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
            return `"${value.replace(/"/g, '""')}"`
          }
          return value
        }).join(',')
      ),
    ]

    const csvContent = csvRows.join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    link.setAttribute('href', url)
    link.setAttribute('download', `reconciliation_export_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleUseCaseChange = (useCaseId: string) => {
    const useCase = useCases.find(uc => uc.use_case_id === useCaseId)
    setSelectedUseCaseId(useCaseId)
    setSelectedUseCase(useCase || null)
    setSelectedRunId('')
    setRowData([])
  }

  return (
    <div className="executive-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-left">
          <label htmlFor="use-case-select">Use Case:</label>
          <select
            id="use-case-select"
            className="use-case-select"
            value={selectedUseCaseId}
            onChange={(e) => handleUseCaseChange(e.target.value)}
          >
            <option value="">Select a use case...</option>
            {useCases.map(uc => (
              <option key={uc.use_case_id} value={uc.use_case_id}>
                {uc.name}
              </option>
            ))}
          </select>
          
          {/* View Controller */}
          <div style={{ marginLeft: '16px', display: 'flex', gap: '8px', alignItems: 'center' }}>
            <label style={{ fontSize: '12px', fontWeight: '500' }}>View:</label>
            <button
              onClick={() => setViewMode('standard')}
              style={{
                padding: '4px 12px',
                fontSize: '12px',
                backgroundColor: viewMode === 'standard' ? '#0ea5e9' : '#e5e7eb',
                color: viewMode === 'standard' ? 'white' : '#374151',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Standard
            </button>
            <button
              onClick={() => setViewMode('delta')}
              style={{
                padding: '4px 12px',
                fontSize: '12px',
                backgroundColor: viewMode === 'delta' ? '#0ea5e9' : '#e5e7eb',
                color: viewMode === 'delta' ? 'white' : '#374151',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Delta Mode
            </button>
            <button
              onClick={() => setViewMode('drilldown')}
              style={{
                padding: '4px 12px',
                fontSize: '12px',
                backgroundColor: viewMode === 'drilldown' ? '#0ea5e9' : '#e5e7eb',
                color: viewMode === 'drilldown' ? 'white' : '#374151',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Drill-Down
            </button>
          </div>
        </div>
        <div className="header-right">
          {/* Freshness Indicator */}
          {lastCalculated && (
            <div style={{ marginRight: '12px', fontSize: '12px', color: '#6b7280' }}>
              Last Calculated: {new Date(lastCalculated).toLocaleString()}
            </div>
          )}
          <button
            className="export-button"
            onClick={handleExportReconciliation}
            disabled={!selectedUseCaseId || rowData.length === 0}
          >
            Export Reconciliation
          </button>
        </div>
      </div>

      {/* Calculation Outdated Warning */}
      {isCalculationOutdated && (
        <div style={{
          backgroundColor: '#fef2f2',
          border: '1px solid #dc2626',
          borderRadius: '4px',
          padding: '12px',
          margin: '12px 0',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span style={{ fontSize: '18px' }}>⚠️</span>
          <div>
            <strong style={{ color: '#dc2626' }}>Calculation Outdated</strong>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#6b7280' }}>
              Rules have been updated since the last calculation. Please re-run the waterfall to see updated results.
            </p>
          </div>
        </div>
      )}

      {/* Golden Equation Indicator */}
      <div className="golden-equation-banner" style={{
        backgroundColor: '#f0f9ff',
        border: '1px solid #0ea5e9',
        borderRadius: '4px',
        padding: '8px 12px',
        margin: '12px 0',
        fontSize: '13px',
        color: '#0c4a6e'
      }}>
        <strong>Golden Equation:</strong> Natural GL Baseline = Adjusted P&L + Reconciliation Plug
        <span style={{ marginLeft: '12px', fontSize: '12px', color: '#64748b' }}>
          (All calculations verified using Decimal precision)
        </span>
      </div>

      {/* Error Message */}
      {error && (
        <div className="message error-message">
          {error}
        </div>
      )}

      {/* AG-Grid */}
      <div className="dashboard-grid">
        <div className="ag-theme-alpine" style={{ height: '100%', width: '100%' }}>
          <AgGridReact
            ref={gridRef}
            rowData={rowData}
            columnDefs={columnDefs}
            defaultColDef={defaultColDef}
            onGridReady={onGridReady}
            treeData={true}
            getDataPath={(data) => data.path || []}
            groupDefaultExpanded={1}
            animateRows={true}
            loading={loading}
            getRowStyle={getRowStyle}
            rowSelection="single"
          />
        </div>
      </div>

      {/* Side Drawer for Rule Details */}
      {drawerOpen && selectedRule && (
        <div className="drawer-overlay" onClick={() => setDrawerOpen(false)}>
          <div className="drawer-content" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <h3>Rule Details</h3>
              <button className="drawer-close" onClick={() => setDrawerOpen(false)}>
                ×
              </button>
            </div>
            <div className="drawer-body">
              <div className="rule-section">
                <strong>Node:</strong>
                <p>{selectedRule.node_name} ({selectedRule.node_id})</p>
              </div>
              
              {selectedRule.rule?.logic_en && (
                <div className="rule-section">
                  <strong>English Prompt:</strong>
                  <p className="rule-prompt">{selectedRule.rule.logic_en}</p>
                </div>
              )}
              
              {selectedRule.rule?.sql_where && (
                <div className="rule-section">
                  <strong>Generated SQL:</strong>
                  <code className="rule-sql">{selectedRule.rule.sql_where}</code>
                </div>
              )}
              
              <div className="rule-section">
                <strong>Reconciliation Plug:</strong>
                <p className="plug-value">
                  Daily: ${parseFloat(selectedRule.plug.daily).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  <br />
                  MTD: ${parseFloat(selectedRule.plug.mtd).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  <br />
                  YTD: ${parseFloat(selectedRule.plug.ytd).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Calculation Trace Drawer */}
      {traceOpen && traceNode && (
        <div className="drawer-overlay" onClick={() => setTraceOpen(false)}>
          <div className="drawer-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className="drawer-header">
              <h3>Calculation Trace</h3>
              <button className="drawer-close" onClick={() => setTraceOpen(false)}>
                ×
              </button>
            </div>
            <div className="drawer-body">
              <div className="rule-section">
                <strong>Node:</strong>
                <p>{traceNode.node_name} ({traceNode.node_id})</p>
              </div>
              
              <div className="rule-section">
                <strong>Calculation Steps (Leaf to Parent):</strong>
                <div style={{ marginTop: '8px', padding: '12px', backgroundColor: '#f9fafb', borderRadius: '4px' }}>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>1. Natural GL Baseline:</strong>
                    <div style={{ marginLeft: '16px', fontSize: '13px', color: '#6b7280' }}>
                      Daily: ${parseFloat(traceNode.natural_value.daily).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      <br />
                      MTD: ${parseFloat(traceNode.natural_value.mtd).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      <br />
                      YTD: ${parseFloat(traceNode.natural_value.ytd).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                  
                  {traceNode.is_override && (
                    <div style={{ marginBottom: '8px' }}>
                      <strong>2. Rule Applied:</strong>
                      <div style={{ marginLeft: '16px', fontSize: '13px', color: '#6b7280' }}>
                        {traceNode.rule?.logic_en || 'N/A'}
                      </div>
                    </div>
                  )}
                  
                  <div style={{ marginBottom: '8px' }}>
                    <strong>3. Adjusted P&L:</strong>
                    <div style={{ marginLeft: '16px', fontSize: '13px', color: '#6b7280' }}>
                      Daily: ${parseFloat(traceNode.adjusted_value.daily).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      <br />
                      MTD: ${parseFloat(traceNode.adjusted_value.mtd).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      <br />
                      YTD: ${parseFloat(traceNode.adjusted_value.ytd).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                  
                  <div>
                    <strong>4. Reconciliation Plug:</strong>
                    <div style={{ marginLeft: '16px', fontSize: '13px', color: '#6b7280' }}>
                      Plug = Natural - Adjusted
                      <br />
                      Daily: ${parseFloat(traceNode.plug.daily).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      <br />
                      MTD: ${parseFloat(traceNode.plug.mtd).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      <br />
                      YTD: ${parseFloat(traceNode.plug.ytd).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ExecutiveDashboard

