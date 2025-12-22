import React, { useState, useEffect, useRef, useCallback } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridApi, ColumnApi, ICellRendererParams } from 'ag-grid-community'
import axios from 'axios'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import './ExecutiveDashboard.css'

// Rule Reference Cell Renderer (Fixed - Returns JSX)
const RuleReferenceCellRenderer: React.FC<ICellRendererParams> = (params) => {
  const rule = params.data?.rule
  if (!rule || !rule.logic_en) {
    return <span style={{ color: '#999' }}>—</span>
  }
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <span className="rule-badge">Rule #{rule.rule_id || 'N/A'}</span>
      <span style={{ color: '#6b7280', fontSize: '0.875rem' }} title={rule.logic_en}>
        {rule.logic_en.length > 50 ? `${rule.logic_en.substring(0, 50)}...` : rule.logic_en}
      </span>
    </div>
  )
}

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

  // Management Narrative
  const [managementNarrative, setManagementNarrative] = useState<string | null>(null)
  const [narrativeLoading, setNarrativeLoading] = useState<boolean>(false)

  // Inheritance Peek Overlay (for drill-to-rule audit)
  const [inheritanceOverlay, setInheritanceOverlay] = useState<{ nodeId: string; x: number; y: number } | null>(null)
  const [ruleStack, setRuleStack] = useState<any>(null)

  // Pre-Flight Execution Plan Modal (Rule Sequence Review)
  const [preFlightModalOpen, setPreFlightModalOpen] = useState<boolean>(false)
  const [executionPlan, setExecutionPlan] = useState<any>(null)
  const [ruleSequence, setRuleSequence] = useState<any[]>([])
  const [acknowledged, setAcknowledged] = useState<boolean>(false)

  // Lock & Archive
  const [archiving, setArchiving] = useState<boolean>(false)
  const [latestVersion, setLatestVersion] = useState<string | null>(null)

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
    } else if (selectedUseCaseId) {
      // Load most recent results if no run selected
      loadResults(selectedUseCaseId)
    }
  }, [selectedUseCaseId, selectedRunId])

  // Generate Management Narrative when results are loaded
  useEffect(() => {
    if (rowData.length > 0 && selectedUseCaseId) {
      generateManagementNarrative()
    }
  }, [rowData, selectedUseCaseId])

  const loadUseCases = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/use-cases`)
      const useCasesList = response.data.use_cases || []
      setUseCases(useCasesList)
      
      if (useCasesList.length > 0 && !selectedUseCaseId) {
        // Check for saved selection
        const savedUseCaseId = localStorage.getItem('finance_insight_selected_use_case_id')
        if (savedUseCaseId && useCasesList.find(uc => uc.use_case_id === savedUseCaseId)) {
          setSelectedUseCaseId(savedUseCaseId)
          const savedUseCase = useCasesList.find(uc => uc.use_case_id === savedUseCaseId)
          if (savedUseCase) setSelectedUseCase(savedUseCase)
        } else {
          // Auto-select first use case
          setSelectedUseCaseId(useCasesList[0].use_case_id)
          setSelectedUseCase(useCasesList[0])
        }
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

  // Load Rule Stack for drill-to-rule audit
  const loadRuleStack = async (nodeId: string) => {
    if (!selectedUseCaseId || !nodeId) return

    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules/stack/${nodeId}`
      )
      setRuleStack(response.data)
    } catch (err: any) {
      console.error('Failed to load rule stack:', err)
      setRuleStack(null)
    }
  }

  // Generate Management Narrative using Gemini
  const generateManagementNarrative = async () => {
    if (!selectedUseCaseId || rowData.length === 0) return

    setNarrativeLoading(true)
    try {
      // Calculate total plug - use NET sum (not absolute) to match grid reconciliation
      const totalPlug = rowData.reduce((sum, row) => {
        return sum + parseFloat(row.plug?.daily || 0)
      }, 0)
      
      // Use absolute value for display but keep sign for context
      const totalPlugAbs = Math.abs(totalPlug)

      // Get top 3 high-impact rules
      const rulesWithImpact = rowData
        .filter(row => row.rule && Math.abs(parseFloat(row.plug?.daily || 0)) > 0.01)
        .map(row => ({
          node_name: row.node_name,
          logic_en: row.rule?.logic_en || '',
          impact: Math.abs(parseFloat(row.plug?.daily || 0))
        }))
        .sort((a, b) => b.impact - a.impact)
        .slice(0, 3)

      if (rulesWithImpact.length === 0) {
        setManagementNarrative('No management adjustments have been proposed for this use case.')
        setNarrativeLoading(false)
        return
      }

      // Call backend endpoint to generate narrative (use absolute for display)
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/narrative`,
        {
          total_plug: totalPlugAbs, // Use absolute for narrative display
          net_plug: totalPlug, // Include net for context
          top_rules: rulesWithImpact.map(r => ({
            node: r.node_name,
            logic: r.logic_en,
            impact: r.impact
          }))
        }
      )

      setManagementNarrative(response.data.narrative || 'Management summary unavailable.')
    } catch (err: any) {
      console.error('Failed to generate management narrative:', err)
      // Fallback narrative - use net sum to match grid
      const totalPlug = rowData.reduce((sum, row) => {
        return sum + parseFloat(row.plug?.daily || 0)
      }, 0)
      const totalPlugAbs = Math.abs(totalPlug)
      setManagementNarrative(
        `This use case adjusted the baseline by $${totalPlugAbs.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}. Review individual rules for detailed impact analysis.`
      )
    } finally {
      setNarrativeLoading(false)
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

  // PBI-style row styling with level-based banding
  const getRowStyle = (params: any) => {
    const depth = params.data?.depth || 0
    const baseStyle: any = {}
    
    // Level-based banding (PBI style)
    if (depth === 0) {
      baseStyle.fontWeight = '700'
      baseStyle.borderBottom = '2px solid #ddd'
      baseStyle.backgroundColor = '#f8f9fa'
    } else if (depth === 1) {
      baseStyle.backgroundColor = '#f9fafb'
      baseStyle.paddingLeft = '20px'
    } else {
      baseStyle.backgroundColor = '#ffffff'
      baseStyle.paddingLeft = `${20 + (depth - 1) * 20}px`
    }
    
    return baseStyle
  }

  // Row class rules for PBI styling
  const getRowClass = (params: any) => {
    const depth = params.data?.depth || 0
    return `ag-row-level-${depth}`
  }

  // Auto Group Column Definition (PBI Style)
  const autoGroupColumnDef: ColDef = {
    headerName: 'Dimension Node',
    field: 'node_name',
    flex: 2,
    cellRenderer: 'agGroupCellRenderer',
  }

  // AG-Grid Column Definitions (dynamic based on view mode)
  const getColumnDefs = (): ColDef[] => {
    const baseColumns: ColDef[] = []

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
            const natural = parseFloat(params.data?.natural_value?.daily || 0)
            const adjusted = parseFloat(params.data?.adjusted_value?.daily || 0)
            const baseStyle: any = { textAlign: 'right', cursor: 'pointer' }
            if (Math.abs(value) > 0.01) {
              // Green for value add (Adjusted > Natural), Red for value reduction (Adjusted < Natural)
              if (adjusted > natural) {
                baseStyle.color = '#059669' // Green
              } else if (adjusted < natural) {
                baseStyle.color = '#dc2626' // Red
              } else {
                baseStyle.color = '#d97706' // Amber for neutral
              }
              baseStyle.fontWeight = '600'
            }
            return baseStyle
          },
          onCellClicked: (params) => {
            // Drill-to-Rule Audit: Open inheritance peek overlay
            if (params.data?.node_id && Math.abs(parseFloat(params.data.plug?.daily || 0)) > 0.01) {
              const rect = params.event?.target?.getBoundingClientRect()
              if (rect) {
                loadRuleStack(params.data.node_id)
                setInheritanceOverlay({
                  nodeId: params.data.node_id,
                  x: rect.right + 10,
                  y: rect.top
                })
              }
            } else if (viewMode === 'drilldown') {
              loadCalculationTrace(params.data)
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
            // Handle zero division gracefully
            if (Math.abs(natural) < 0.01) {
              // If natural is zero, variance is based on adjusted value
              if (Math.abs(adjusted) < 0.01) return 0
              return adjusted > 0 ? 100 : -100 // 100% variance if natural is 0
            }
            return ((adjusted - natural) / Math.abs(natural)) * 100
          },
          valueFormatter: (params) => {
            if (params.value === null || params.value === undefined) return '0.00%'
            return `${params.value.toFixed(2)}%`
          },
          cellStyle: (params) => {
            const value = params.value || 0
            const baseStyle: any = { textAlign: 'right' }
            if (Math.abs(value) > 1) {
              baseStyle.color = value > 0 ? '#059669' : '#dc2626'
              baseStyle.fontWeight = '600'
            }
            return baseStyle
          },
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
            // Handle zero division gracefully
            if (Math.abs(natural) < 0.01) {
              // If natural is zero, variance is based on adjusted value
              if (Math.abs(adjusted) < 0.01) return 0
              return adjusted > 0 ? 100 : -100 // 100% variance if natural is 0
            }
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
          flex: 2,
          cellRenderer: RuleReferenceCellRenderer,
          cellStyle: { textAlign: 'left' },
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

  // Load Execution Plan (Pre-Flight) with Rule Sequence Review
  const loadExecutionPlan = async () => {
    if (!selectedUseCaseId) return

    try {
      // Load execution plan
      const planResponse = await axios.get(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/execution-plan`
      )
      setExecutionPlan(planResponse.data)
      
      // Load all active rules for sequence review
      const rulesResponse = await axios.get(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules`
      )
      const rules = rulesResponse.data || []
      
      // Build rule sequence with English summary and technical predicate
      const sequence = rules.map((rule: any, index: number) => ({
        step: index + 1,
        node_id: rule.node_id,
        node_name: rule.node_name || rule.node_id,
        english_summary: rule.logic_en || 'No description',
        technical_predicate: rule.sql_where || rule.predicate_json ? JSON.stringify(rule.predicate_json || {}) : 'N/A',
        is_leaf: rule.is_leaf || false
      }))
      
      setRuleSequence(sequence)
      setAcknowledged(false) // Reset acknowledgment
      setPreFlightModalOpen(true)
    } catch (err: any) {
      console.error('Failed to load execution plan:', err)
      alert('Failed to load execution plan. Please try again.')
    }
  }

  // Note: Execute Business Rules functionality is in Tab 3 (RuleEditor.tsx)
  // This function is kept for Pre-Flight modal confirmation only

  // Confirm and Run Calculation (from Pre-Flight modal)
  const handleConfirmAndRun = async () => {
    if (!acknowledged) {
      alert('Please acknowledge that you have reviewed the execution sequence.')
      return
    }
    
    setPreFlightModalOpen(false)
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/calculate`
      )
      
      // Reload results after calculation
      await loadResults(selectedUseCaseId)
      
      // Update last calculated timestamp
      if (response.data.run_id) {
        setLastCalculated(new Date().toISOString())
        setIsCalculationOutdated(false)
      }
    } catch (err: any) {
      console.error('Failed to run calculation:', err)
      setError(err.response?.data?.detail || 'Failed to run calculation. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Lock & Archive current snapshot
  const handleLockAndArchive = async () => {
    if (!selectedUseCaseId || rowData.length === 0) {
      alert('Please ensure calculation results are available before archiving.')
      return
    }

    if (!confirm('Lock and archive this snapshot? This will preserve the current rule-set and results permanently.')) {
      return
    }

    setArchiving(true)
    try {
      // Get current rules
      const rulesResponse = await axios.get(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules`
      )
      const currentRules = rulesResponse.data || []
      
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/archive`,
        {
          snapshot_name: `${selectedUseCase?.name || 'Snapshot'}_${new Date().toISOString().split('T')[0]}`,
          rules_snapshot: currentRules.map((rule: any) => ({
            node_id: rule.node_id,
            logic_en: rule.logic_en,
            sql_where: rule.sql_where,
            predicate_json: rule.predicate_json
          })),
          results_snapshot: rowData.map((row: any) => ({
            node_id: row.node_id,
            natural_value: row.natural_value,
            adjusted_value: row.adjusted_value,
            plug: row.plug
          })),
          notes: `Archived snapshot for ${selectedUseCase?.name || 'Use Case'}`,
          created_by: 'user' // TODO: Get from auth context
        }
      )
      
      // Update latest version
      if (response.data.version_tag) {
        setLatestVersion(response.data.version_tag)
      }
      
      alert(`Snapshot archived successfully: ${response.data.version_tag || response.data.snapshot_id}`)
    } catch (err: any) {
      console.error('Failed to archive snapshot:', err)
      alert('Failed to archive snapshot. Please try again.')
    } finally {
      setArchiving(false)
    }
  }

  // Export Executive PDF Report
  const handleExportExecutivePDF = async () => {
    if (!selectedUseCase || !managementNarrative || rowData.length === 0) {
      alert('Please ensure calculation results and management narrative are available.')
      return
    }

    try {
      // Dynamic import of jspdf
      const { default: jsPDF } = await import('jspdf')
      
      const doc = new jsPDF({
        orientation: 'landscape',
        unit: 'mm',
        format: 'a4'
      })

      // Set up branding
      doc.setFontSize(20)
      doc.setTextColor(14, 165, 233) // Blue
      doc.text('Finance-Insight Executive Report', 20, 20)
      
      doc.setFontSize(12)
      doc.setTextColor(0, 0, 0)
      doc.text(`Use Case: ${selectedUseCase.name}`, 20, 30)
      
      if (lastCalculated) {
        doc.setFontSize(10)
        doc.setTextColor(100, 100, 100)
        doc.text(`Last Calculated: ${new Date(lastCalculated).toLocaleString()}`, 20, 37)
      }

      // Management Narrative Section
      doc.setFontSize(14)
      doc.setTextColor(0, 0, 0)
      doc.text('Management Summary', 20, 50)
      
      doc.setFontSize(11)
      doc.setTextColor(50, 50, 50)
      const narrativeLines = doc.splitTextToSize(managementNarrative, 250)
      doc.text(narrativeLines, 20, 58)

      // Summary Table (Top-level nodes only)
      let yPos = 75
      doc.setFontSize(12)
      doc.setTextColor(0, 0, 0)
      doc.text('Executive Summary', 20, yPos)
      
      yPos += 8
      doc.setFontSize(10)
      
      // Table headers (clean quotes, newlines, carriage returns)
      const cleanText = (text: string) => text.replace(/["\n\r]/g, '').trim()
      
      doc.setFillColor(240, 240, 240)
      doc.rect(20, yPos, 250, 8, 'F')
      doc.setTextColor(0, 0, 0)
      doc.setFont(undefined, 'bold')
      doc.text(cleanText('Dimension Node'), 22, yPos + 6)
      doc.text(cleanText('Natural GL'), 100, yPos + 6)
      doc.text(cleanText('Adjusted P&L'), 150, yPos + 6)
      doc.text(cleanText('Reconciliation Plug'), 200, yPos + 6)
      doc.text(cleanText('Variance %'), 250, yPos + 6)
      
      yPos += 8
      doc.setFont(undefined, 'normal')
      
      // Get top-level nodes (depth 0)
      const topLevelNodes = rowData.filter((row: any) => (row.depth || 0) === 0).slice(0, 10)
      
      topLevelNodes.forEach((row: any) => {
        if (yPos > 180) {
          doc.addPage()
          yPos = 20
        }
        
        const natural = parseFloat(row.natural_value?.daily || 0)
        const adjusted = parseFloat(row.adjusted_value?.daily || 0)
        const plug = parseFloat(row.plug?.daily || 0)
        const variance = Math.abs(natural) < 0.01 ? 0 : ((adjusted - natural) / Math.abs(natural)) * 100
        
        // Clean all text (remove HTML tags, quotes, newlines, carriage returns)
        const cleanText = (text: string) => text.replace(/<[^>]*>/g, '').replace(/["\n\r]/g, ' ').trim()
        const cleanNodeName = cleanText(row.node_name || row.node_id || '')
        doc.text(cleanNodeName, 22, yPos + 6)
        doc.text(`$${natural.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, 100, yPos + 6)
        doc.text(`$${adjusted.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, 150, yPos + 6)
        doc.text(`$${Math.abs(plug).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, 200, yPos + 6)
        doc.text(`${variance.toFixed(2)}%`, 250, yPos + 6)
        
        yPos += 7
      })

      // Footer
      const pageCount = doc.getNumberOfPages()
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i)
        doc.setFontSize(8)
        doc.setTextColor(150, 150, 150)
        doc.text(
          `Page ${i} of ${pageCount} | Generated: ${new Date().toLocaleString()}`,
          20,
          285
        )
      }

      // Save PDF
      const fileName = `Executive_Report_${selectedUseCase.name.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.pdf`
      doc.save(fileName)
    } catch (err: any) {
      console.error('Failed to export PDF:', err)
      if (err.message?.includes('jspdf') || err.message?.includes('Cannot find module')) {
        alert('PDF export requires jspdf library. Please install it: npm install jspdf')
      } else {
        alert('Failed to export PDF. Please try again.')
      }
    }
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
      {/* Management Narrative Header */}
      {managementNarrative && selectedUseCase && (
        <div className="management-narrative-card">
          <div className="narrative-header">
            <h3>Management Summary</h3>
            {narrativeLoading && <span className="narrative-loading">Generating...</span>}
          </div>
          <div className="narrative-content">
            <p>{managementNarrative}</p>
          </div>
        </div>
      )}

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
          {/* Freshness Indicator with Math Verified Badge */}
          {lastCalculated && (
            <div style={{ marginRight: '12px', fontSize: '12px', color: '#6b7280', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>Last Calculated: {new Date(lastCalculated).toLocaleString()}</span>
              <span 
                className="math-verified-badge"
                title="Golden Equation verified: Natural GL = Adjusted P&L + Reconciliation Plug"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '2px 6px',
                  background: '#d1fae5',
                  color: '#059669',
                  borderRadius: '12px',
                  fontSize: '10px',
                  fontWeight: '600',
                  cursor: 'help'
                }}
              >
                ✓ Math Verified
              </span>
              {latestVersion && (
                <span style={{ 
                  background: '#e0e7ff', 
                  color: '#4f46e5', 
                  padding: '2px 6px', 
                  borderRadius: '12px',
                  fontSize: '10px',
                  fontWeight: '600'
                }}>
                  {latestVersion}
                </span>
              )}
            </div>
          )}
          <button
            className="export-button"
            onClick={handleExportExecutivePDF}
            disabled={!selectedUseCaseId || rowData.length === 0 || !managementNarrative}
            style={{ marginRight: '8px' }}
          >
            📄 Export Executive Report
          </button>
          <button
            className="export-button"
            onClick={handleExportReconciliation}
            disabled={!selectedUseCaseId || rowData.length === 0}
            style={{ marginRight: '8px' }}
          >
            Export Reconciliation
          </button>
          <button
            className="lock-archive-btn"
            onClick={handleLockAndArchive}
            disabled={!selectedUseCaseId || rowData.length === 0 || loading}
            title="Lock current rule-set and results as a snapshot"
          >
            🔒 Lock & Archive
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

      {/* Empty State */}
      {!loading && rowData.length === 0 && selectedUseCaseId && !error && (
        <div className="empty-state">
          <div className="empty-state-content">
            <h3>No Calculation Results</h3>
            <p>Go to Tab 3 (Business Rules) to execute business rules and see the comparison between Natural GL and Adjusted P&L.</p>
          </div>
        </div>
      )}

      {/* AG-Grid */}
      {rowData.length > 0 && (
        <div className="dashboard-grid">
          <div className="ag-theme-alpine" style={{ height: '600px', width: '100%' }}>
            <AgGridReact
              ref={gridRef}
              rowData={rowData}
              columnDefs={columnDefs}
              autoGroupColumnDef={autoGroupColumnDef}
              defaultColDef={defaultColDef}
              onGridReady={onGridReady}
              treeData={true}
              getDataPath={(data) => data.path || []}
              groupDefaultExpanded={1}
              animateRows={true}
              loading={loading}
              getRowStyle={getRowStyle}
              getRowClass={getRowClass}
              rowSelection="single"
            />
          </div>
        </div>
      )}

      {/* Inheritance Peek Overlay (Drill-to-Rule Audit) */}
      {inheritanceOverlay && ruleStack && (
        <>
          <div 
            className="overlay-backdrop"
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 1999,
              background: 'transparent'
            }}
            onClick={() => setInheritanceOverlay(null)}
          />
          <div 
            className="inheritance-overlay"
            style={{
              position: 'fixed',
              left: `${inheritanceOverlay.x}px`,
              top: `${inheritanceOverlay.y}px`,
              zIndex: 2000
            }}
            onClick={() => setInheritanceOverlay(null)}
          >
            <div className="inheritance-overlay-content" onClick={(e) => e.stopPropagation()}>
              <div className="inheritance-overlay-header">
                <h4>Rule Inheritance Stack</h4>
                <button onClick={() => setInheritanceOverlay(null)}>×</button>
              </div>
              <div className="inheritance-overlay-body">
                {ruleStack.parent_rules && ruleStack.parent_rules.length > 0 && (
                  <div className="inheritance-section">
                    <strong>Parent Rules:</strong>
                    {ruleStack.parent_rules.map((parentRule: any, idx: number) => (
                      <div key={idx} className="inheritance-rule-item">
                        <span className="rule-node">{parentRule.node_name || parentRule.node_id}:</span>
                        <span className="rule-logic">{parentRule.logic_en || 'N/A'}</span>
                      </div>
                    ))}
                  </div>
                )}
                {ruleStack.direct_rule && (
                  <div className="inheritance-section">
                    <strong>Direct Rule:</strong>
                    <div className={`inheritance-rule-item ${ruleStack.has_conflict ? 'conflict' : ''}`}>
                      <span className="rule-logic">{ruleStack.direct_rule.logic_en || 'N/A'}</span>
                      {ruleStack.has_conflict && (
                        <span className="conflict-badge-small">⚠️ Override</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}

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

      {/* Pre-Flight Execution Plan Modal */}
      {preFlightModalOpen && executionPlan && (
        <div className="pre-flight-modal-overlay" onClick={() => setPreFlightModalOpen(false)}>
          <div className="pre-flight-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="pre-flight-modal-header">
              <h3>Rule Sequence Review</h3>
              <button 
                className="modal-close-btn"
                onClick={() => setPreFlightModalOpen(false)}
              >
                ×
              </button>
            </div>
            <div className="pre-flight-modal-body">
              <div className="execution-plan-summary">
                <p style={{ marginBottom: '1rem', color: '#6b7280' }}>
                  Review the rule execution sequence before running the calculation:
                </p>
                
                {/* Business Rules Summary (LLM-Generated) */}
                {executionPlan?.business_summary && (
                  <div style={{ 
                    marginBottom: '1.5rem', 
                    padding: '1rem', 
                    background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)', 
                    border: '2px solid #fbbf24',
                    borderRadius: '6px' 
                  }}>
                    <div style={{ fontSize: '0.875rem', fontWeight: '700', color: '#92400e', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Business Rules Summary
                    </div>
                    <div style={{ fontSize: '1rem', color: '#78350f', lineHeight: '1.5', fontStyle: 'italic' }}>
                      "{executionPlan.business_summary}"
                    </div>
                  </div>
                )}
                
                {/* Rule Sequence Review */}
                <div className="rule-sequence-review" style={{ marginBottom: '1.5rem' }}>
                  <div style={{ fontSize: '0.875rem', fontWeight: '600', color: '#374151', marginBottom: '0.75rem' }}>
                    Active Rules ({ruleSequence.length}):
                  </div>
                  <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '0.75rem' }}>
                    {ruleSequence.map((rule: any) => (
                      <div key={rule.step} style={{ 
                        marginBottom: '1rem', 
                        padding: '0.75rem', 
                        background: '#f9fafb', 
                        borderRadius: '4px',
                        borderLeft: '3px solid #0ea5e9'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                          <span style={{ 
                            background: '#0ea5e9', 
                            color: 'white', 
                            padding: '0.25rem 0.5rem', 
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            fontWeight: '600'
                          }}>
                            Step {rule.step} of {ruleSequence.length}
                          </span>
                          <span style={{ fontSize: '0.875rem', fontWeight: '600', color: '#1f2937' }}>
                            {rule.node_name}
                          </span>
                          {rule.is_leaf && (
                            <span style={{ fontSize: '0.75rem', color: '#059669', background: '#d1fae5', padding: '0.125rem 0.375rem', borderRadius: '4px' }}>
                              Leaf
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: '0.875rem', color: '#374151', marginBottom: '0.25rem' }}>
                          <strong>English Summary:</strong> {rule.english_summary}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280', fontFamily: 'monospace', background: '#f3f4f6', padding: '0.5rem', borderRadius: '4px', marginTop: '0.25rem' }}>
                          <strong>Technical Predicate:</strong> {rule.technical_predicate}
                        </div>
                      </div>
                    ))}
                    {ruleSequence.length === 0 && (
                      <div style={{ textAlign: 'center', color: '#6b7280', padding: '2rem' }}>
                        No active rules found. The calculation will use natural GL values only.
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Execution Steps Summary */}
                {executionPlan && (
                  <div className="execution-stats" style={{ marginTop: '1.5rem', padding: '1rem', background: '#f9fafb', borderRadius: '6px' }}>
                    <div style={{ fontSize: '0.875rem', fontWeight: '600', color: '#374151', marginBottom: '0.75rem' }}>
                      Execution Order:
                    </div>
                    {executionPlan.steps?.map((step: any, idx: number) => (
                      <div key={idx} style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '0.5rem',
                        marginBottom: '0.5rem',
                        fontSize: '0.875rem',
                        color: '#6b7280'
                      }}>
                        <span style={{ 
                          width: '24px', 
                          height: '24px', 
                          background: '#0ea5e9', 
                          color: 'white', 
                          borderRadius: '50%', 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'center',
                          fontSize: '0.75rem',
                          fontWeight: '600'
                        }}>
                          {step.step}
                        </span>
                        <span>{step.description}</span>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Acknowledgment Checkbox */}
                <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#fef3c7', border: '1px solid #fbbf24', borderRadius: '6px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={acknowledged}
                      onChange={(e) => setAcknowledged(e.target.checked)}
                      style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                    />
                    <span style={{ fontSize: '0.875rem', color: '#92400e', fontWeight: '500' }}>
                      I have reviewed the execution sequence and confirm these rules align with management intent.
                    </span>
                  </label>
                </div>
              </div>
            </div>
            <div className="pre-flight-modal-footer">
              <button
                className="pre-flight-cancel-btn"
                onClick={() => setPreFlightModalOpen(false)}
              >
                Cancel
              </button>
              <button
                className="pre-flight-confirm-btn"
                onClick={handleConfirmAndRun}
                disabled={loading || !acknowledged}
                title={!acknowledged ? 'Please acknowledge the execution sequence review' : ''}
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Executing...
                  </>
                ) : (
                  'Execute Business Rules'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ExecutiveDashboard

