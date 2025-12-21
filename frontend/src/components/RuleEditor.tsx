import React, { useState, useEffect, useCallback, useRef } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridApi, ColumnApi, ICellRendererParams } from 'ag-grid-community'
import axios from 'axios'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import './RuleEditor.css'

// Custom Cell Renderer Component for Node Name with Rule Icons (Fixed - Returns JSX)
const NodeNameCellRenderer: React.FC<ICellRendererParams> = (params) => {
  const hasRule = params.data?.hasRule
  // Get node name from value, data.node_name, or params.value
  const nodeName = params.value || params.data?.node_name || ''
  const hasConflict = params.data?.hasConflict || false
  const ruleImpact = params.data?.ruleImpact || 0
  const depth = params.data?.depth || 0
  
  // Calculate intensity for heatmap (0-1 scale)
  const getIntensity = (impact: number) => {
    const absImpact = Math.abs(impact)
    if (absImpact === 0) return 0
    if (absImpact < 10000) return 0.3
    if (absImpact < 100000) return 0.6
    if (absImpact < 1000000) return 0.8
    return 1.0
  }
  
  const intensity = getIntensity(ruleImpact)
  const bgOpacity = hasRule ? 0.1 + (intensity * 0.15) : 0
  
  return (
    <div 
      style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '6px',
        backgroundColor: hasRule ? `rgba(59, 130, 246, ${bgOpacity})` : 'transparent',
        padding: '2px 4px',
        borderRadius: '4px',
        transition: 'background-color 0.2s'
      }}
    >
      {hasRule && (
        <span 
          className="fx-icon-badge"
          data-fx-icon="true"
          style={{
            background: `linear-gradient(135deg, #fef3c7 ${intensity * 100}%, #fbbf24)`,
            color: '#d97706',
            borderRadius: '3px',
            padding: '2px 6px',
            fontSize: '11px',
            fontWeight: '600',
            fontFamily: 'monospace',
            boxShadow: intensity > 0.5 ? '0 0 4px rgba(217, 119, 6, 0.4)' : 'none',
            cursor: 'pointer'
          }}
          onClick={(e) => {
            e.stopPropagation()
            // Trigger parent cell click handler
            if (params.onCellClicked) {
              params.onCellClicked({
                ...params,
                event: e.nativeEvent
              } as any)
            }
          }}
        >
          fx
        </span>
      )}
      {hasConflict && (
        <span 
          style={{
            color: '#dc2626',
            fontSize: '14px',
            cursor: 'help'
          }}
          title="Specific override detected: Parent rule is being ignored for this node"
        >
          ⚠️
        </span>
      )}
      <span style={{ flex: 1 }}>{nodeName || params.value || ''}</span>
    </div>
  )
}

// Impact Sparkline Cell Renderer
const ImpactSparklineRenderer: React.FC<ICellRendererParams> = (params) => {
  const natural = parseFloat(params.data?.daily_pnl || 0)
  const rule = params.data?.rule
  const adjusted = rule?.estimatedImpact || 0
  const delta = adjusted !== 0 ? adjusted : 0
  
  // Simple sparkline visualization
  const width = 60
  const height = 20
  const midY = height / 2
  
  // Normalize delta for visualization (scale to fit in 20px height)
  const maxDelta = Math.max(Math.abs(delta), 1000) // Prevent division by zero
  const normalizedDelta = Math.min(Math.max((delta / maxDelta) * 10, -8), 8)
  
  // Create a simple line chart
  const points = [
    `M 0 ${midY}`,
    `L ${width / 2} ${midY - normalizedDelta}`,
    `L ${width} ${midY}`
  ].join(' ')
  
  const color = delta > 0 ? '#28a745' : delta < 0 ? '#dc3545' : '#6c757d'
  
  if (!rule) {
    return <span style={{ color: '#9ca3af', fontSize: '0.75rem' }}>—</span>
  }
  
  return (
    <svg width={width} height={height} style={{ display: 'block' }}>
      <path
        d={points}
        stroke={color}
        strokeWidth="2"
        fill="none"
      />
      <circle
        cx={width / 2}
        cy={midY - normalizedDelta}
        r="2.5"
        fill={color}
      />
    </svg>
  )
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface HierarchyNode {
  node_id: string
  node_name: string
  parent_node_id: string | null
  depth: number
  is_leaf: boolean
  daily_pnl: string
  mtd_pnl: string
  ytd_pnl: string
  path?: string[] | null
  children: HierarchyNode[]
}

interface DiscoveryResponse {
  structure_id: string
  hierarchy: HierarchyNode[]
}

interface UseCase {
  use_case_id: string
  name: string
  atlas_structure_id: string
}

interface RuleCondition {
  field: string
  operator: string
  value: string | string[]
}

interface RulePreview {
  logic_en?: string
  sql_where?: string
  predicate_json?: any
  affected_rows?: number
  total_rows?: number
  percentage?: number
  translation_successful?: boolean
  errors?: string[]
}

const RuleEditor: React.FC = () => {
  // Use Case Management
  const [useCases, setUseCases] = useState<UseCase[]>([])
  const [selectedUseCaseId, setSelectedUseCaseId] = useState<string>('')
  const [selectedUseCase, setSelectedUseCase] = useState<UseCase | null>(null)

  // Hierarchy Tree
  const [rowData, setRowData] = useState<any[]>([])
  const [gridApi, setGridApi] = useState<GridApi | null>(null)
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [selectedNodes, setSelectedNodes] = useState<any[]>([]) // Multi-node selection
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set()) // Track expanded nodes for Tab 2 & 3 unification

  // Rules State
  const [rules, setRules] = useState<Map<string, any>>(new Map()) // Map of node_id -> rule
  const [rulesLoading, setRulesLoading] = useState<boolean>(false)
  
  // Rule Stack State
  const [ruleStack, setRuleStack] = useState<any>(null)
  const [ruleStackLoading, setRuleStackLoading] = useState<boolean>(false)
  const [ruleStackOpen, setRuleStackOpen] = useState<boolean>(false)
  
  // Grid-Hero State
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [filteredRowData, setFilteredRowData] = useState<any[]>([])
  const [modalOpen, setModalOpen] = useState<boolean>(false)
  const [libraryDrawerOpen, setLibraryDrawerOpen] = useState<boolean>(false)
  const [inheritanceOverlay, setInheritanceOverlay] = useState<{ nodeId: string; x: number; y: number } | null>(null)
  const [conflictCount, setConflictCount] = useState<number>(0)
  const [lastCalculated, setLastCalculated] = useState<string | null>(null)
  const [rulesLastModified, setRulesLastModified] = useState<string | null>(null)
  const [isCalculationOutdated, setIsCalculationOutdated] = useState<boolean>(false)
  
  // Shared tree state key (for Tab 2 & 3 unification)
  const getTreeStateKey = (structureId: string) => `finance_insight_tree_state_${structureId}`

  // Editor Mode
  const [editorMode, setEditorMode] = useState<'ai' | 'standard'>('ai')

  // AI Mode State
  const [aiPrompt, setAiPrompt] = useState<string>('')
  const aiPromptRef = useRef<HTMLTextAreaElement>(null)
  const [generating, setGenerating] = useState<boolean>(false)
  const [lastGenerateTime, setLastGenerateTime] = useState<number>(0)
  const [generateCooldown, setGenerateCooldown] = useState<number>(0) // Seconds remaining

  // Standard Mode State
  const [conditions, setConditions] = useState<RuleCondition[]>([
    { field: '', operator: 'equals', value: '' }
  ])

  // Rule Preview
  const [rulePreview, setRulePreview] = useState<RulePreview | null>(null)
  const [previewLoading, setPreviewLoading] = useState<boolean>(false)

  // Calculation
  const [calculating, setCalculating] = useState<boolean>(false)
  const [calculationResult, setCalculationResult] = useState<string | null>(null)

  // Loading & Error States
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const gridRef = useRef<AgGridReact>(null)

  // Available fields for Standard Mode
  const availableFields = [
    { value: 'account_id', label: 'Account ID' },
    { value: 'cc_id', label: 'Cost Center ID' },
    { value: 'book_id', label: 'Book ID' },
    { value: 'strategy_id', label: 'Strategy ID' },
    { value: 'trade_date', label: 'Trade Date' },
  ]

  const availableOperators = [
    { value: 'equals', label: 'Equals' },
    { value: 'not_equals', label: 'Not Equals' },
    { value: 'in', label: 'In (list)' },
    { value: 'not_in', label: 'Not In (list)' },
    { value: 'greater_than', label: 'Greater Than' },
    { value: 'less_than', label: 'Less Than' },
  ]

  // Load use cases
  useEffect(() => {
    loadUseCases()
  }, [])

  // Load hierarchy and rules when use case is selected
  useEffect(() => {
    if (selectedUseCase) {
      loadHierarchy(selectedUseCase.atlas_structure_id)
      loadRules(selectedUseCaseId)
      
      // Load shared tree state (Tab 2 & 3 unification)
      const stateKey = getTreeStateKey(selectedUseCase.atlas_structure_id)
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
  }, [selectedUseCase, selectedUseCaseId])

  // Persist shared tree state to localStorage (Tab 2 & 3 unification)
  useEffect(() => {
    if (selectedUseCase && expandedNodes.size >= 0) {
      const stateKey = getTreeStateKey(selectedUseCase.atlas_structure_id)
      const state = {
        expandedNodes: Array.from(expandedNodes),
        lastUpdated: new Date().toISOString()
      }
      localStorage.setItem(stateKey, JSON.stringify(state))
    }
  }, [expandedNodes, selectedUseCase])

  // Flatten hierarchy for AG-Grid tree data (with safe rules access)
  // Defined early so it can be used by loadHierarchy
  const flattenHierarchy = useCallback((nodes: HierarchyNode[], parentPath: string[] = []): any[] => {
    const result: any[] = []
    
    for (const node of nodes) {
      const path = node.path || parentPath.concat([node.node_name])
      
      // Check if this node has an active rule (safe access with null check)
      const hasRule = rules && rules instanceof Map && rules.has(node.node_id)
      const rule = hasRule && rules instanceof Map ? rules.get(node.node_id) : null
      
      const row = {
        ...node,
        path, // AG-Grid treeData uses getDataPath to extract this
        hasRule: !!hasRule, // Flag for conditional rendering (ensure boolean)
        rule: rule || null, // Store rule data for recall
        ruleImpact: rule?.estimatedImpact || 0, // Dollar impact for heatmap
        hasConflict: false, // Will be set when rule stack is loaded
      }
      result.push(row)
      
      // Recursively add children if they exist
      if (node.children && node.children.length > 0) {
        result.push(...flattenHierarchy(node.children, path))
      }
    }
    
    return result
  }, [rules]) // Include rules in dependencies so it updates when rules change

  // Re-flatten hierarchy when rules change (to update rule icons)
  useEffect(() => {
    if (selectedUseCase && rules.size >= 0 && rowData.length > 0) {
      // Reload hierarchy to refresh rule icons
      // Only reload if rules actually changed (not on initial load)
      loadHierarchy(selectedUseCase.atlas_structure_id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rules.size]) // Only trigger when rules count changes (avoid infinite loop)

  // Audit Summary State
  const [auditSummary, setAuditSummary] = useState<{
    totalRules: number
    affectedRows: number
    totalRows: number
    totalAdjustment: number
  } | null>(null)

  // Load rules for the selected use case with impact calculations
  const loadRules = async (useCaseId: string) => {
    if (!useCaseId) return

    setRulesLoading(true)
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/use-cases/${useCaseId}/rules`
      )
      const rulesList = response.data || []
      
      // Create a Map for quick lookup: node_id -> rule with impact
      const rulesMap = new Map<string, any>()
      let totalAffectedRows = 0
      let totalRows = 0
      let totalAdjustment = 0
      
      // Load impact for each rule
      for (const rule of rulesList) {
        if (rule.node_id && rule.sql_where) {
          try {
            // Get impact preview
            const previewResponse = await axios.post(
              `${API_BASE_URL}/api/v1/rules/preview`,
              { sql_where: rule.sql_where }
            )
            
            // Estimate P&L impact (simplified: use affected_rows * average daily_pnl)
            // In production, this would query actual SUM(daily_pnl) for affected rows
            const estimatedImpact = previewResponse.data.affected_rows * 100 // Placeholder calculation
            
            rulesMap.set(rule.node_id, {
              ...rule,
              affected_rows: previewResponse.data.affected_rows,
              total_rows: previewResponse.data.total_rows,
              percentage: previewResponse.data.percentage,
              estimatedImpact: estimatedImpact
            })
            
            totalAffectedRows += previewResponse.data.affected_rows
            totalRows = previewResponse.data.total_rows
            totalAdjustment += estimatedImpact
          } catch (e) {
            // If preview fails, still add rule without impact
            rulesMap.set(rule.node_id, {
              ...rule,
              affected_rows: 0,
              total_rows: 0,
              percentage: 0,
              estimatedImpact: 0
            })
          }
        }
      }
      
      setRules(rulesMap)
      
      // Update audit summary
      setAuditSummary({
        totalRules: rulesMap.size,
        affectedRows: totalAffectedRows,
        totalRows: totalRows,
        totalAdjustment: totalAdjustment
      })
    } catch (err: any) {
      console.error('Failed to load rules:', err)
      setRules(new Map())
      setAuditSummary(null)
    } finally {
      setRulesLoading(false)
    }
  }

  const loadUseCases = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/use-cases`)
      const useCasesList = response.data.use_cases || []
      setUseCases(useCasesList)
      
      // Auto-select first use case if available
      if (useCasesList.length > 0 && !selectedUseCaseId) {
        setSelectedUseCaseId(useCasesList[0].use_case_id)
        setSelectedUseCase(useCasesList[0])
      }
    } catch (err: any) {
      console.error('Failed to load use cases:', err)
      setError('Failed to load use cases. Please ensure the backend is running.')
    }
  }

  const loadHierarchy = useCallback(async (structureId: string) => {
    if (!structureId) return

    setLoading(true)
    setError(null)

    try {
      const response = await axios.get<DiscoveryResponse>(
        `${API_BASE_URL}/api/v1/discovery`,
        { params: { structure_id: structureId } }
      )

      const hierarchy = response.data?.hierarchy || []
      if (hierarchy.length === 0) {
        setError('No hierarchy data found.')
        setRowData([])
        setLoading(false)
        return
      }

      // Flatten hierarchy for AG-Grid (with rule information)
      // Safe call - flattenHierarchy handles null/undefined rules
      try {
        const flatData = flattenHierarchy(hierarchy)
        setRowData(flatData)
      } catch (flattenError: any) {
        console.error('Failed to flatten hierarchy:', flattenError)
        // Fallback: flatten without rules if there's an error
        const fallbackData: any[] = []
        const processNode = (node: HierarchyNode, parentPath: string[] = []) => {
          const path = node.path || parentPath.concat([node.node_name])
          fallbackData.push({
            ...node,
            path,
            hasRule: false,
            rule: null
          })
          if (node.children && node.children.length > 0) {
            node.children.forEach(child => processNode(child, path))
          }
        }
        hierarchy.forEach(node => processNode(node))
        setRowData(fallbackData)
      }
    } catch (err: any) {
      console.error('Failed to load hierarchy:', err)
      setError('Failed to load hierarchy data.')
    } finally {
      setLoading(false)
    }
  }, [flattenHierarchy]) // Include flattenHierarchy in dependencies

  // Tree-preserving search filter
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredRowData(rowData)
      return
    }
    
    const query = searchQuery.toLowerCase()
    const filtered: any[] = []
    const matchedNodeIds = new Set<string>()
    
    // First pass: find all matching nodes
    rowData.forEach((row: any) => {
      const nodeName = (row.node_name || '').toLowerCase()
      const nodeId = (row.node_id || '').toLowerCase()
      if (nodeName.includes(query) || nodeId.includes(query)) {
        matchedNodeIds.add(row.node_id)
      }
    })
    
    // Second pass: include matched nodes and their parents
    const parentIds = new Set<string>()
    rowData.forEach((row: any) => {
      if (matchedNodeIds.has(row.node_id)) {
        // Include this node
        filtered.push(row)
        // Track parent for inclusion
        if (row.parent_node_id) {
          parentIds.add(row.parent_node_id)
        }
      }
    })
    
    // Third pass: include parents of matched nodes
    rowData.forEach((row: any) => {
      if (parentIds.has(row.node_id) && !matchedNodeIds.has(row.node_id)) {
        filtered.push(row)
        if (row.parent_node_id) {
          parentIds.add(row.parent_node_id)
        }
      }
    })
    
    // Sort to maintain hierarchy order
    filtered.sort((a, b) => {
      const pathA = a.path || []
      const pathB = b.path || []
      return pathA.join('/').localeCompare(pathB.join('/'))
    })
    
    setFilteredRowData(filtered)
  }, [searchQuery, rowData])

  // Check for conflicts and calculate conflict count
  useEffect(() => {
    if (!selectedUseCaseId || rules.size === 0) {
      setConflictCount(0)
      return
    }
    
    let conflicts = 0
    rules.forEach((rule: any, nodeId: string) => {
      if (ruleStack && ruleStack.node_id === nodeId && ruleStack.has_conflict) {
        conflicts++
      }
    })
    
    setConflictCount(conflicts)
  }, [rules, ruleStack, selectedUseCaseId])

  // Check calculation freshness
  useEffect(() => {
    if (!selectedUseCaseId || !lastCalculated) return
    
    const checkFreshness = async () => {
      try {
        const rulesResponse = await axios.get(
          `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules`
        )
        const rulesList = rulesResponse.data || []
        
        if (rulesList.length > 0) {
          const latestRule = rulesList.reduce((latest: any, rule: any) => {
            if (!latest) return rule
            return new Date(rule.last_modified_at) > new Date(latest.last_modified_at) ? rule : latest
          }, null)
          
          if (latestRule && latestRule.last_modified_at) {
            setRulesLastModified(latestRule.last_modified_at)
            if (new Date(latestRule.last_modified_at) > new Date(lastCalculated)) {
              setIsCalculationOutdated(true)
            } else {
              setIsCalculationOutdated(false)
            }
          }
        }
      } catch (err) {
        console.error('Failed to check freshness:', err)
      }
    }
    
    checkFreshness()
  }, [selectedUseCaseId, lastCalculated])

  // Load last calculated timestamp
  useEffect(() => {
    if (!selectedUseCaseId) return
    
    const loadLastRun = async () => {
      try {
        const response = await axios.get(
          `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/results`
        )
        if (response.data?.run_timestamp) {
          setLastCalculated(response.data.run_timestamp)
        }
      } catch (err) {
        // No runs yet
        setLastCalculated(null)
      }
    }
    
    loadLastRun()
  }, [selectedUseCaseId])

  // Available schema fields for Field Helper Tag Cloud
  const availableFieldsForHelper = [
    { field: 'book_id', label: 'Book ID', type: 'String' },
    { field: 'strategy_id', label: 'Strategy ID', type: 'String' },
    { field: 'account_id', label: 'Account ID', type: 'String' },
    { field: 'cc_id', label: 'Cost Center ID', type: 'String' },
    { field: 'trade_date', label: 'Trade Date', type: 'Date' },
    { field: 'daily_pnl', label: 'Daily P&L', type: 'Numeric' },
    { field: 'mtd_pnl', label: 'MTD P&L', type: 'Numeric' },
    { field: 'ytd_pnl', label: 'YTD P&L', type: 'Numeric' },
  ]

  // Status Pill Renderer for Business Rule column
  const BusinessRuleCellRenderer: React.FC<ICellRendererParams> = (params) => {
    const rule = params.data?.rule
    if (!rule || !rule.logic_en) {
      return <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>—</span>
    }
    
    // Determine rule type: AI-Generated, Manual Override, or Inherited
    const isAI = rule.logic_en && !rule.predicate_json // AI-generated if no predicate_json
    const isManual = rule.predicate_json && rule.predicate_json.conditions // Manual if has conditions
    const isInherited = params.data?.hasRule && !params.data?.rule?.node_id // Inherited if rule exists but not for this node
    
    let pillClass = 'rule-pill-inherited'
    let pillText = 'Inherited'
    
    if (isAI) {
      pillClass = 'rule-pill-ai'
      pillText = 'AI-Generated'
    } else if (isManual) {
      pillClass = 'rule-pill-manual'
      pillText = 'Manual Override'
    }
    
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span className={pillClass}>{pillText}</span>
        <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>{rule.logic_en}</span>
      </div>
    )
  }

  // AG-Grid Column Definitions (Institutional Layout)
  const columnDefs: ColDef[] = [
    {
      field: 'business_rule',
      headerName: 'Business Rule',
      flex: 2,
      cellRenderer: BusinessRuleCellRenderer,
    },
    {
      field: 'impact',
      headerName: 'Impact',
      flex: 1,
      cellRenderer: ImpactSparklineRenderer,
      cellStyle: { textAlign: 'center' },
      tooltipValueGetter: (params) => {
        const natural = parseFloat(params.data?.daily_pnl || 0)
        const rule = params.data?.rule
        const adjusted = rule?.estimatedImpact || 0
        const delta = adjusted - natural
        
        if (!rule) return 'No rule applied'
        
        return `Natural: $${natural.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} → Adjusted: $${adjusted.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} (Delta: $${delta.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })})`
      },
    },
    {
      field: 'created_by',
      headerName: 'Created By',
      flex: 1.2,
      valueGetter: (params) => {
        return params.data?.rule?.last_modified_by || '—'
      },
      cellStyle: { color: '#6b7280' },
    },
    {
      field: 'daily_pnl',
      headerName: 'Daily P&L',
      flex: 1.2,
      valueFormatter: (params) => {
        if (!params.value) return '$0.00'
        const num = parseFloat(params.value)
        return `$${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
      },
      cellStyle: { textAlign: 'right' },
    },
  ]

  // Auto Group Column Definition (PBI Style)
  const autoGroupColumnDef: ColDef = {
    headerName: 'Node Name',
    field: 'node_name',
    flex: 2.5,
    checkboxSelection: true,
    headerCheckboxSelection: true,
    cellRenderer: 'agGroupCellRenderer',
    cellRendererParams: {
      innerRenderer: (params: ICellRendererParams) => {
        // Pass the node_name value explicitly to the inner renderer
        return <NodeNameCellRenderer {...params} value={params.value || params.data?.node_name || ''} />
      },
    },
    onCellClicked: (params) => {
      const target = params.event?.target as HTMLElement
      if (target?.closest('.fx-icon-badge') || target?.dataset?.fxIcon === 'true') {
        // Open inheritance overlay
        const rect = target.getBoundingClientRect()
        if (rect && params.data) {
          loadRuleStack(params.data.node_id)
          setInheritanceOverlay({
            nodeId: params.data.node_id,
            x: rect.right + 10,
            y: rect.top
          })
        }
      }
    },
  }

  const defaultColDef: ColDef = {
    sortable: true,
    filter: true,
    resizable: true,
  }

  // PBI-style row styling with level-based banding and conflict detection
  const getRowStyle = (params: any) => {
    const depth = params.data?.depth || 0
    const hasConflict = params.data?.hasConflict || false
    const baseStyle: any = {}
    
    // Conflict row: Faded red background
    if (hasConflict) {
      baseStyle.backgroundColor = '#fff5f5'
      baseStyle.borderLeft = '3px solid #dc2626'
    }
    
    // Level-based banding (PBI style)
    if (depth === 0) {
      baseStyle.fontWeight = '700'
      baseStyle.borderBottom = '2px solid #ddd'
      if (!hasConflict) {
        baseStyle.backgroundColor = '#f8f9fa'
      }
    } else if (depth === 1) {
      if (!hasConflict) {
        baseStyle.backgroundColor = '#ffffff'
      }
      baseStyle.paddingLeft = '20px'
      if (!hasConflict) {
        baseStyle.borderLeft = '3px solid #007bff'
      }
    } else {
      if (!hasConflict) {
        baseStyle.backgroundColor = '#ffffff'
      }
      baseStyle.paddingLeft = `${20 + (depth - 1) * 20}px`
    }
    
    // Status glow for nodes with rules (only if no conflict)
    if (params.data?.hasRule && !hasConflict) {
      baseStyle.borderLeft = baseStyle.borderLeft || '3px solid #28a745'
    }
    
    return baseStyle
  }

  // Row class rules for PBI styling
  const getRowClass = (params: any) => {
    const depth = params.data?.depth || 0
    const hasConflict = params.data?.hasConflict || false
    const classes = [`ag-row-level-${depth}`]
    if (hasConflict) {
      classes.push('conflict-row')
    }
    return classes.join(' ')
  }

  const onGridReady = (params: { api: GridApi; columnApi: ColumnApi }) => {
    setGridApi(params.api)
    
    // Tree Unification: Track expansion changes and sync to shared state
    params.api.addEventListener('rowGroupOpened', (event: any) => {
      if (event.node && event.node.data) {
        const nodeId = event.node.data.node_id
        setExpandedNodes(prev => {
          const next = new Set(prev)
          next.add(nodeId)
          return next
        })
      }
    })
    
    params.api.addEventListener('rowGroupClosed', (event: any) => {
      if (event.node && event.node.data) {
        const nodeId = event.node.data.node_id
        setExpandedNodes(prev => {
          const next = new Set(prev)
          next.delete(nodeId)
          return next
        })
      }
    })
    
    // Apply saved expansion state after grid is ready (Tab 2 & 3 unification)
    setTimeout(() => {
      if (expandedNodes.size > 0 && params.api) {
        params.api.forEachNode((node: any) => {
          if (node.data && expandedNodes.has(node.data.node_id)) {
            node.setExpanded(true)
          }
        })
      }
    }, 200)
  }

  // Load Rule Stack for selected node
  const loadRuleStack = async (nodeId: string) => {
    if (!selectedUseCaseId || !nodeId) return

    setRuleStackLoading(true)
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules/stack/${nodeId}`
      )
      setRuleStack(response.data)
      setRuleStackOpen(true)
    } catch (err: any) {
      console.error('Failed to load rule stack:', err)
      // Don't show error - rule stack might not be available
      setRuleStack(null)
    } finally {
      setRuleStackLoading(false)
    }
  }

  const onSelectionChanged = () => {
    if (gridApi) {
      const selectedRows = gridApi.getSelectedRows()
      
      // Multi-node selection support
      setSelectedNodes(selectedRows)
      
      if (selectedRows.length > 0) {
        const firstNode = selectedRows[0]
        setSelectedNode(firstNode)
        
        // Load rule stack for first selected node
        loadRuleStack(firstNode.node_id)
        
        // Rule Recall: Auto-load existing rule when node is selected
        if (firstNode.hasRule && firstNode.rule) {
          const rule = firstNode.rule
          
          // Load rule into editor
          if (rule.logic_en) {
            setAiPrompt(rule.logic_en)
            setEditorMode('ai')
          }
          
          if (rule.predicate_json) {
            // Convert predicate_json to conditions for Standard Mode
            const conditions: RuleCondition[] = []
            if (rule.predicate_json.conditions) {
              rule.predicate_json.conditions.forEach((cond: any) => {
                conditions.push({
                  field: cond.field || '',
                  operator: cond.operator || 'equals',
                  value: cond.value || ''
                })
              })
            }
            if (conditions.length > 0) {
              setConditions(conditions)
            }
          }
          
          // Load preview if available
          if (rule.sql_where) {
            setRulePreview({
              logic_en: rule.logic_en,
              sql_where: rule.sql_where,
              predicate_json: rule.predicate_json,
              translation_successful: true
            })
          }
        } else {
          // Clear preview when node without rule is selected
          setRulePreview(null)
          setAiPrompt('')
          setConditions([{ field: '', operator: 'equals', value: '' }])
        }
      } else {
        setSelectedNode(null)
        setSelectedNodes([])
        setRulePreview(null)
        setRuleStack(null)
        setRuleStackOpen(false)
      }
    }
  }

  // Handle Use Case Selection
  const handleUseCaseChange = (useCaseId: string) => {
    const useCase = useCases.find(uc => uc.use_case_id === useCaseId)
    setSelectedUseCaseId(useCaseId)
    setSelectedUseCase(useCase || null)
    setSelectedNode(null)
    setRulePreview(null)
  }

  // Client-side throttling: 3 second cooldown to prevent double-taps
  useEffect(() => {
    if (generateCooldown > 0) {
      const timer = setInterval(() => {
        setGenerateCooldown(prev => {
          if (prev <= 1) {
            clearInterval(timer)
            return 0
          }
          return prev - 1
        })
      }, 1000)
      return () => clearInterval(timer)
    }
  }, [generateCooldown])

  // AI Mode: Generate Rule
  const handleGenerateRule = async () => {
    if (selectedNodes.length === 0 || !selectedUseCaseId || !aiPrompt.trim()) {
      setError('Please select at least one node and enter a natural language prompt.')
      return
    }

    // Client-side throttling: prevent double-taps
    const now = Date.now()
    const timeSinceLastGenerate = (now - lastGenerateTime) / 1000
    if (timeSinceLastGenerate < 3) {
      const remaining = Math.ceil(3 - timeSinceLastGenerate)
      setGenerateCooldown(remaining)
      setError(`Please wait ${remaining} second${remaining > 1 ? 's' : ''} before generating again.`)
      return
    }

    setLastGenerateTime(now)
    setGenerating(true)
    setError(null)

    try {
      // Use first selected node for preview (rule will be same for all)
      const previewNode = selectedNodes[0]
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules/genai`,
        {
          node_id: previewNode.node_id,
          logic_en: aiPrompt,
          last_modified_by: 'user123', // TODO: Get from auth context
        }
      )

      const preview: RulePreview = {
        logic_en: response.data.logic_en,
        sql_where: response.data.sql_where,
        predicate_json: response.data.predicate_json,
        translation_successful: response.data.translation_successful,
        errors: response.data.errors || [],
      }

      setRulePreview(preview)

      // If translation successful, automatically fetch preview impact
      if (response.data.translation_successful && response.data.sql_where) {
        await fetchRulePreview(response.data.sql_where)
      }
    } catch (err: any) {
      console.error('Failed to generate rule:', err)
      setError(err.response?.data?.detail || 'Failed to generate rule. Please try again.')
      setRulePreview({
        translation_successful: false,
        errors: [err.response?.data?.detail || 'Translation failed'],
      })
    } finally {
      setGenerating(false)
    }
  }

  // Standard Mode: Add Condition
  const handleAddCondition = () => {
    setConditions([...conditions, { field: '', operator: 'equals', value: '' }])
  }

  // Standard Mode: Remove Condition
  const handleRemoveCondition = (index: number) => {
    setConditions(conditions.filter((_, i) => i !== index))
  }

  // Standard Mode: Update Condition
  const handleConditionChange = (index: number, field: keyof RuleCondition, value: any) => {
    const updated = [...conditions]
    updated[index] = { ...updated[index], [field]: value }
    setConditions(updated)
    // Clear preview when conditions change
    setRulePreview(null)
  }

  // Standard Mode: Generate Rule from Conditions
  const handleGenerateFromConditions = async () => {
    if (selectedNodes.length === 0 || !selectedUseCaseId) {
      setError('Please select at least one node.')
      return
    }

    // Validate conditions
    const validConditions = conditions.filter(c => c.field && c.value)
    if (validConditions.length === 0) {
      setError('Please add at least one valid condition.')
      return
    }

    // Convert conditions to API format
    const formattedConditions = validConditions.map(c => ({
      field: c.field,
      operator: c.operator,
      value: c.operator === 'in' || c.operator === 'not_in' 
        ? (typeof c.value === 'string' ? c.value.split(',').map(v => v.trim()) : c.value)
        : c.value,
    }))

    setPreviewLoading(true)
    setError(null)

    try {
      // Use first selected node for preview (rule will be same for all)
      const previewNode = selectedNodes[0]
      // Create rule to get SQL
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules`,
        {
          node_id: previewNode.node_id,
          conditions: formattedConditions,
          last_modified_by: 'user123', // TODO: Get from auth context
        }
      )

      const preview: RulePreview = {
        logic_en: response.data.logic_en,
        sql_where: response.data.sql_where,
        predicate_json: response.data.predicate_json,
        translation_successful: true,
      }

      setRulePreview(preview)

      // Fetch preview impact
      if (response.data.sql_where) {
        await fetchRulePreview(response.data.sql_where)
      }
    } catch (err: any) {
      console.error('Failed to generate rule from conditions:', err)
      setError(err.response?.data?.detail || 'Failed to generate rule. Please try again.')
    } finally {
      setPreviewLoading(false)
    }
  }

  // Fetch Rule Preview Impact
  const fetchRulePreview = async (sqlWhere: string) => {
    if (!sqlWhere) return

    setPreviewLoading(true)

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/rules/preview`,
        { sql_where: sqlWhere }
      )

      setRulePreview(prev => ({
        ...prev,
        affected_rows: response.data.affected_rows,
        total_rows: response.data.total_rows,
        percentage: response.data.percentage,
      }))
    } catch (err: any) {
      console.error('Failed to fetch rule preview:', err)
    } finally {
      setPreviewLoading(false)
    }
  }

  // Save & Apply Rule (single or batch)
  const handleSaveRule = async () => {
    if (!selectedUseCaseId || !rulePreview?.sql_where) {
      setError('No rule to save. Please generate a rule first.')
      return
    }

    // Determine if batch save (multiple nodes selected)
    const nodesToSave = selectedNodes.length > 1 ? selectedNodes : (selectedNode ? [selectedNode] : [])
    
    if (nodesToSave.length === 0) {
      setError('Please select at least one node.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const nodeIds = nodesToSave.map((n: any) => n.node_id)
      
      if (nodesToSave.length > 1) {
        // Batch save to multiple nodes
        if (editorMode === 'ai' && rulePreview.logic_en) {
          await axios.post(
            `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules/bulk`,
            {
              node_ids: nodeIds,
              logic_en: rulePreview.logic_en,
              last_modified_by: 'user123', // TODO: Get from auth context
            }
          )
        } else if (editorMode === 'standard' && conditions.length > 0) {
          const formattedConditions = conditions
            .filter(c => c.field && c.value)
            .map(c => ({
              field: c.field,
              operator: c.operator,
              value: c.operator === 'in' || c.operator === 'not_in' 
                ? (typeof c.value === 'string' ? c.value.split(',').map(v => v.trim()) : c.value)
                : c.value,
            }))

          await axios.post(
            `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules/bulk`,
            {
              node_ids: nodeIds,
              conditions: formattedConditions,
              last_modified_by: 'user123', // TODO: Get from auth context
            }
          )
        }
        
        setCalculationResult(`Rule saved successfully to ${nodeIds.length} node(s)!`)
      } else {
        // Single node save (existing logic)
        if (editorMode === 'ai' && rulePreview.logic_en) {
          await axios.post(
            `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules`,
            {
              node_id: nodeIds[0],
              logic_en: rulePreview.logic_en,
              last_modified_by: 'user123', // TODO: Get from auth context
            }
          )
        } else if (editorMode === 'standard' && conditions.length > 0) {
          const formattedConditions = conditions
            .filter(c => c.field && c.value)
            .map(c => ({
              field: c.field,
              operator: c.operator,
              value: c.operator === 'in' || c.operator === 'not_in' 
                ? (typeof c.value === 'string' ? c.value.split(',').map(v => v.trim()) : c.value)
                : c.value,
            }))

          await axios.post(
            `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules`,
            {
              node_id: nodeIds[0],
              conditions: formattedConditions,
              last_modified_by: 'user123', // TODO: Get from auth context
            }
          )
        }
        
        setCalculationResult('Rule saved successfully!')
      }

      // Refresh rules and hierarchy to update icons
      if (selectedUseCaseId) {
        await loadRules(selectedUseCaseId)
        if (selectedUseCase) {
          await loadHierarchy(selectedUseCase.atlas_structure_id)
        }
      }

      // Refresh impact preview
      if (rulePreview.sql_where) {
        await fetchRulePreview(rulePreview.sql_where)
      }

      // Success - clear form, close modal, and show message
      setRulePreview(null)
      setAiPrompt('')
      setConditions([{ field: '', operator: 'equals', value: '' }])
      setModalOpen(false)
      setCalculationResult('Rule saved successfully!')
      setTimeout(() => setCalculationResult(null), 3000)
    } catch (err: any) {
      console.error('Failed to save rule:', err)
      setError(err.response?.data?.detail || 'Failed to save rule. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Bulk Delete Rules
  const handleBulkDeleteRules = async () => {
    if (selectedNodes.length === 0) {
      setError('Please select at least one node to clear rules.')
      return
    }

    if (!selectedUseCaseId) {
      setError('Please select a use case first.')
      return
    }

    if (!confirm(`Are you sure you want to delete rules for ${selectedNodes.length} selected node(s)?`)) {
      return
    }

    setLoading(true)
    setError(null)

    try {
      const nodeIds = selectedNodes.map((n: any) => n.node_id)
      
      await axios.delete(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules/bulk`,
        { data: { node_ids: nodeIds } }
      )

      // Refresh rules and hierarchy
      await loadRules(selectedUseCaseId)
      if (selectedUseCase) {
        await loadHierarchy(selectedUseCase.atlas_structure_id)
      }

      setCalculationResult(`Rules deleted successfully for ${nodeIds.length} node(s)!`)
      setTimeout(() => setCalculationResult(null), 3000)
      
      // Clear selection
      if (gridApi) {
        gridApi.deselectAll()
      }
      
      // Update freshness check
      if (selectedUseCaseId) {
        const rulesResponse = await axios.get(
          `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules`
        )
        const rulesList = rulesResponse.data || []
        if (rulesList.length > 0) {
          const latestRule = rulesList.reduce((latest: any, rule: any) => {
            if (!latest) return rule
            return new Date(rule.last_modified_at) > new Date(latest.last_modified_at) ? rule : latest
          }, null)
          if (latestRule) {
            setRulesLastModified(latestRule.last_modified_at)
            if (lastCalculated && new Date(latestRule.last_modified_at) > new Date(lastCalculated)) {
              setIsCalculationOutdated(true)
            }
          }
        }
      }
    } catch (err: any) {
      console.error('Failed to delete rules:', err)
      setError(err.response?.data?.detail || 'Failed to delete rules. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Run Waterfall Calculation
  const handleRunCalculation = async () => {
    if (!selectedUseCaseId) {
      setError('Please select a use case first.')
      return
    }

    setCalculating(true)
    setError(null)
    setCalculationResult(null)

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/calculate`
      )

      const message = response.data.message || 
        `Calculation complete. ${response.data.rules_applied} rules applied. Total Plug: $${response.data.total_plug?.daily || '0.00'}`
      
      setCalculationResult(message)
      
      // Update last calculated timestamp
      if (response.data.run_timestamp) {
        setLastCalculated(response.data.run_timestamp)
        setIsCalculationOutdated(false)
      }
      
      // Reload rules after calculation to refresh icons
      if (selectedUseCaseId) {
        loadRules(selectedUseCaseId)
      }
    } catch (err: any) {
      console.error('Failed to run calculation:', err)
      setError(err.response?.data?.detail || 'Failed to run calculation. Please try again.')
    } finally {
      setCalculating(false)
    }
  }

  // Pre-Calculation Audit: Show all active rules before calculation
  const [auditDrawerOpen, setAuditDrawerOpen] = useState<boolean>(false)
  const [auditRules, setAuditRules] = useState<any[]>([])

  const handleOpenAuditDrawer = async () => {
    if (!selectedUseCaseId) {
      setError('Please select a use case first.')
      return
    }

    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules`
      )
      const rulesList = response.data || []
      
      // Filter only active rules (with sql_where)
      const activeRules = rulesList.filter((rule: any) => rule.sql_where)
      
      if (activeRules.length === 0) {
        setError('No active rules found. Please create rules before calculating.')
        return
      }
      
      // Get preview impact for each rule
      const rulesWithPreview = await Promise.all(
        activeRules.map(async (rule: any) => {
          try {
            const previewResponse = await axios.post(
              `${API_BASE_URL}/api/v1/rules/preview`,
              { sql_where: rule.sql_where }
            )
            return {
              ...rule,
              affected_rows: previewResponse.data.affected_rows,
              total_rows: previewResponse.data.total_rows,
              percentage: previewResponse.data.percentage
            }
          } catch (e) {
            return { ...rule, affected_rows: 0, total_rows: 0, percentage: 0 }
          }
        })
      )
      
      setAuditRules(rulesWithPreview)
      setAuditDrawerOpen(true)
    } catch (err: any) {
      console.error('Failed to load audit rules:', err)
      setError('Failed to load rules for audit.')
    }
  }

  const handleConfirmCalculation = () => {
    setAuditDrawerOpen(false)
    handleRunCalculation()
  }

  return (
    <div className="rule-editor">
      {/* Header with Use Case Selector and Calculation Button */}
      <div className="rule-editor-header">
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
        </div>
        <div className="header-right">
          <button
            className="calculate-button"
            onClick={handleRunCalculation}
            disabled={calculating || !selectedUseCaseId}
          >
            {calculating ? (
              <>
                <span className="spinner"></span>
                Calculating Waterfall...
              </>
            ) : (
              'Run Waterfall Calculation'
            )}
          </button>
        </div>
      </div>

      {/* Audit Summary Header */}
      {auditSummary && selectedUseCase && (
        <div className="audit-summary-header">
          <div className="audit-summary-content">
            <strong>Use Case '{selectedUseCase.name}'</strong> has{' '}
            <strong>{auditSummary.totalRules}</strong> active rule{auditSummary.totalRules !== 1 ? 's' : ''} affecting{' '}
            <strong>{auditSummary.affectedRows.toLocaleString()}</strong> row{auditSummary.affectedRows !== 1 ? 's' : ''} 
            {auditSummary.totalRows > 0 && (
              <> out of <strong>{auditSummary.totalRows.toLocaleString()}</strong> total rows</>
            )}
            {' '}with a total adjustment of{' '}
            <strong style={{ color: auditSummary.totalAdjustment < 0 ? '#dc2626' : '#059669' }}>
              {auditSummary.totalAdjustment < 0 ? '-' : '+'}${Math.abs(auditSummary.totalAdjustment).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}k
            </strong>
          </div>
        </div>
      )}

      {/* Error/Success Messages */}
      {error && (
        <div className="message error-message">
          {error}
        </div>
      )}
      {calculationResult && (
        <div className="message success-message">
          {calculationResult}
        </div>
      )}

      {/* Command Bar */}
      <div className="command-bar">
        <div className="command-bar-left">
          <input
            type="text"
            className="search-input"
            placeholder="Search nodes (preserves hierarchy)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {conflictCount > 0 && (
            <div className="conflict-alert">
              ⚠️ <strong>{conflictCount}</strong> Conflict Override{conflictCount !== 1 ? 's' : ''} Detected
            </div>
          )}
        </div>
        <div className="command-bar-right">
          {lastCalculated && (
            <span className="freshness-indicator">
              Last Calculated: {new Date(lastCalculated).toLocaleString()}
            </span>
          )}
          <button
            className="command-btn secondary"
            onClick={() => setLibraryDrawerOpen(true)}
          >
            View Library
          </button>
          <button
            className="command-btn primary"
            onClick={() => setModalOpen(true)}
            disabled={selectedNodes.length === 0}
          >
            Manage Rule
          </button>
          <button
            className="command-btn danger"
            onClick={handleBulkDeleteRules}
            disabled={selectedNodes.length === 0 || loading}
          >
            Clear Rules
          </button>
          <button
            className="calculate-button"
            onClick={handleRunCalculation}
            disabled={calculating || !selectedUseCaseId || isCalculationOutdated}
            title={isCalculationOutdated ? 'Rules have changed. Re-run calculation required.' : ''}
          >
            {calculating ? (
              <>
                <span className="spinner"></span>
                Calculating...
              </>
            ) : (
              'Run Waterfall'
            )}
          </button>
        </div>
      </div>

      {/* Grid-Hero Layout - 100% Width */}
      <div className="grid-hero-container">
        <div className="ag-theme-alpine grid-hero" style={{ height: 'calc(100vh - 300px)', width: '100%' }}>
          <AgGridReact
            ref={gridRef}
            rowData={searchQuery ? filteredRowData : rowData}
            columnDefs={columnDefs}
            autoGroupColumnDef={autoGroupColumnDef}
            defaultColDef={defaultColDef}
            onGridReady={onGridReady}
            onSelectionChanged={onSelectionChanged}
            onRowGroupOpened={(params) => {
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
              if (params.node && params.node.data) {
                const nodeId = params.node.data.node_id
                setExpandedNodes(prev => {
                  const next = new Set(prev)
                  next.delete(nodeId)
                  return next
                })
              }
            }}
            rowSelection="multiple"
            treeData={true}
            getDataPath={(data) => data.path || []}
            groupDefaultExpanded={1}
            animateRows={true}
            loading={loading}
            getRowStyle={getRowStyle}
            getRowClass={getRowClass}
            suppressRowClickSelection={false}
            enableRangeSelection={false}
          />
        </div>
      </div>

      {/* Inheritance Peek Overlay */}
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

      {/* Rule Editor Modal */}
      {modalOpen && (
        <div className="rule-editor-modal-overlay" onClick={() => setModalOpen(false)}>
          <div className="rule-editor-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="rule-editor-modal-header">
              <h3>
                {selectedNodes.length === 1 
                  ? `Manage Rule - ${selectedNodes[0].node_name}`
                  : `Manage Rule - ${selectedNodes.length} Nodes`}
              </h3>
              <button 
                className="modal-close-btn"
                onClick={() => setModalOpen(false)}
              >
                ×
              </button>
            </div>
            <div className="rule-editor-modal-body">
              <div className="rule-editor-content">
              {/* Mode Toggle */}
              <div className="mode-toggle">
                <label className="toggle-label">
                  <input
                    type="checkbox"
                    checked={editorMode === 'ai'}
                    onChange={(e) => {
                      setEditorMode(e.target.checked ? 'ai' : 'standard')
                      setRulePreview(null)
                    }}
                  />
                  <span className="toggle-slider"></span>
                  <span className="toggle-text">
                    {editorMode === 'ai' ? 'AI Mode' : 'Standard Mode'}
                  </span>
                </label>
              </div>

              {/* AI Mode Editor */}
              {editorMode === 'ai' && (
                <div className="editor-section">
                  <label htmlFor="ai-prompt">Natural Language Prompt</label>
                  
                  {/* Field Helper Tag Cloud */}
                  <div className="field-helper">
                    <div className="field-helper-label">Available Fields:</div>
                    <div className="field-tag-cloud">
                      {availableFieldsForHelper.map((field) => (
                        <span
                          key={field.field}
                          className="field-tag"
                          onClick={() => {
                            const textarea = aiPromptRef.current
                            if (textarea) {
                              const start = textarea.selectionStart || 0
                              const end = textarea.selectionEnd || 0
                              const currentPrompt = aiPrompt || ''
                              const before = currentPrompt.substring(0, start)
                              const after = currentPrompt.substring(end)
                              const newPrompt = `${before}${field.field}${after}`
                              setAiPrompt(newPrompt)
                              // Restore cursor position after field name
                              setTimeout(() => {
                                textarea.focus()
                                const newCursorPos = start + field.field.length
                                textarea.setSelectionRange(newCursorPos, newCursorPos)
                              }, 0)
                            } else {
                              // Fallback if ref not available
                              const currentPrompt = aiPrompt || ''
                              const newPrompt = currentPrompt ? `${currentPrompt} ${field.field}` : field.field
                              setAiPrompt(newPrompt)
                            }
                          }}
                          title={`${field.label} (${field.type}) - Click to insert`}
                        >
                          {field.label}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <textarea
                    ref={aiPromptRef}
                    id="ai-prompt"
                    className="ai-prompt-input"
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    placeholder="e.g., 'Exclude internal books B01 and B02' or 'Include only EQUITY strategy trades'"
                    rows={6}
                  />
                  <button
                    className="generate-button"
                    onClick={handleGenerateRule}
                    disabled={generating || !aiPrompt.trim() || generateCooldown > 0}
                  >
                    {generating 
                      ? 'Generating...' 
                      : generateCooldown > 0 
                        ? `Wait ${generateCooldown}s...` 
                        : 'Generate Rule'}
                  </button>
                </div>
              )}

              {/* Standard Mode Editor */}
              {editorMode === 'standard' && (
                <div className="editor-section">
                  <label>Rule Conditions</label>
                  {conditions.map((condition, index) => (
                    <div key={index} className="condition-row">
                      <select
                        className="condition-field"
                        value={condition.field}
                        onChange={(e) => handleConditionChange(index, 'field', e.target.value)}
                      >
                        <option value="">Select Field...</option>
                        {availableFields.map(field => (
                          <option key={field.value} value={field.value}>
                            {field.label}
                          </option>
                        ))}
                      </select>
                      <select
                        className="condition-operator"
                        value={condition.operator}
                        onChange={(e) => handleConditionChange(index, 'operator', e.target.value)}
                      >
                        {availableOperators.map(op => (
                          <option key={op.value} value={op.value}>
                            {op.label}
                          </option>
                        ))}
                      </select>
                      <input
                        type="text"
                        className="condition-value"
                        value={typeof condition.value === 'string' ? condition.value : condition.value.join(', ')}
                        onChange={(e) => {
                          const value = (condition.operator === 'in' || condition.operator === 'not_in')
                            ? e.target.value
                            : e.target.value
                          handleConditionChange(index, 'value', value)
                        }}
                        placeholder={
                          condition.operator === 'in' || condition.operator === 'not_in'
                            ? 'Comma-separated values (e.g., B01, B02)'
                            : 'Enter value...'
                        }
                      />
                      {conditions.length > 1 && (
                        <button
                          className="remove-condition-button"
                          onClick={() => handleRemoveCondition(index)}
                        >
                          ×
                        </button>
                      )}
                    </div>
                  ))}
                  <div className="condition-actions">
                    <button
                      className="add-condition-button"
                      onClick={handleAddCondition}
                    >
                      + Add Condition
                    </button>
                    <button
                      className="generate-button"
                      onClick={handleGenerateFromConditions}
                      disabled={previewLoading || conditions.every(c => !c.field || !c.value)}
                    >
                      {previewLoading ? 'Generating...' : 'Generate Rule'}
                    </button>
                  </div>
                </div>
              )}

              {/* Glass Box Preview */}
              {rulePreview && (
                <div className="rule-preview-card">
                  <h4>Rule Preview</h4>
                  
                  {rulePreview.translation_successful === false && (
                    <div className="preview-error">
                      <strong>Translation Failed:</strong>
                      <ul>
                        {rulePreview.errors?.map((err, i) => (
                          <li key={i}>{err}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {rulePreview.logic_en && (
                    <div className="preview-section">
                      <strong>Logic Summary:</strong>
                      <p>{rulePreview.logic_en}</p>
                    </div>
                  )}

                  {rulePreview.sql_where && (
                    <div className="preview-section">
                      <strong>Generated SQL:</strong>
                      <code className="sql-preview">{rulePreview.sql_where}</code>
                    </div>
                  )}

                  {rulePreview.affected_rows !== undefined && (
                    <div className="preview-section">
                      <strong>Impact Counter:</strong>
                      <p className="impact-text">
                        This rule will affect <strong>{rulePreview.affected_rows.toLocaleString()}</strong> rows
                        {rulePreview.total_rows && (
                          <> out of <strong>{rulePreview.total_rows.toLocaleString()}</strong> total rows
                          {rulePreview.percentage && (
                            <> (<strong>{rulePreview.percentage.toFixed(2)}%</strong>)</>
                          )}</>
                        )}
                      </p>
                    </div>
                  )}

                  {previewLoading && (
                    <div className="preview-loading">Loading preview...</div>
                  )}

                  <button
                    className="save-button"
                    onClick={handleSaveRule}
                    disabled={loading || !rulePreview.translation_successful || !rulePreview.sql_where}
                  >
                    {loading ? 'Saving...' : 'Save & Apply'}
                  </button>
                </div>
              )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Rule Library Drawer */}
      {libraryDrawerOpen && (
        <div className="library-drawer-overlay" onClick={() => setLibraryDrawerOpen(false)}>
          <div className="library-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="library-drawer-header">
              <h3>Rule Library</h3>
              <button onClick={() => setLibraryDrawerOpen(false)}>×</button>
            </div>
            <div className="library-drawer-body">
              <div className="library-counter">
                Showing <strong>{rules.size}</strong> Active Rule{rules.size !== 1 ? 's' : ''}
              </div>
              <div className="library-drawer-actions">
                <input
                  type="text"
                  className="library-search"
                  placeholder="Search by node or user..."
                />
                <div className="audit-export-buttons">
                  <button
                    className="export-btn"
                    onClick={async () => {
                      // Export to Excel
                      try {
                        const rulesArray = Array.from(rules.values())
                        const csv = [
                          ['Node Name', 'Rule Logic', 'Created By', 'Impact', 'Affected Rows', 'Total Rows', 'Percentage'].join(','),
                          ...rulesArray.map((rule: any) => [
                            rule.node_name || rule.node_id,
                            `"${(rule.logic_en || '').replace(/"/g, '""')}"`,
                            rule.last_modified_by || 'Unknown',
                            rule.estimatedImpact || 0,
                            rule.affected_rows || 0,
                            rule.total_rows || 0,
                            rule.percentage || 0
                          ].join(','))
                        ].join('\n')
                        
                        const blob = new Blob([csv], { type: 'text/csv' })
                        const url = window.URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = `rule-audit-${new Date().toISOString().split('T')[0]}.csv`
                        document.body.appendChild(a)
                        a.click()
                        document.body.removeChild(a)
                        window.URL.revokeObjectURL(url)
                      } catch (err) {
                        console.error('Failed to export audit:', err)
                        alert('Failed to export audit. Please try again.')
                      }
                    }}
                  >
                    📊 Export Excel
                  </button>
                  <button
                    className="export-btn"
                    onClick={async () => {
                      // Export to PDF (simplified - opens print dialog)
                      window.print()
                    }}
                  >
                    📄 Export PDF
                  </button>
                </div>
              </div>
              <div className="library-rules-list">
                {rules.size > 0 ? (
                  Array.from(rules.values()).map((rule: any) => (
                    <div key={rule.rule_id} className="library-rule-card">
                      <div className="library-rule-header">
                        <strong>{rule.node_name || rule.node_id}</strong>
                        <span className="rule-badge-small">fx</span>
                      </div>
                      <div className="library-rule-body">
                        <p className="rule-logic">{rule.logic_en || 'N/A'}</p>
                        <div className="library-rule-meta">
                          <span>By: {rule.last_modified_by || 'Unknown'}</span>
                          <span className={`impact-badge ${rule.estimatedImpact < 0 ? 'negative' : 'positive'}`}>
                            {rule.estimatedImpact < 0 ? '-' : '+'}${Math.abs(rule.estimatedImpact).toLocaleString()}k
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="no-rules-message">
                    <p>No active rules yet.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pre-Calculation Audit Drawer */}
      {auditDrawerOpen && (
        <div className="audit-drawer-overlay" onClick={() => setAuditDrawerOpen(false)}>
          <div className="audit-drawer-content" onClick={(e) => e.stopPropagation()}>
            <div className="audit-drawer-header">
              <h3>Pre-Calculation Audit</h3>
              <button className="audit-drawer-close" onClick={() => setAuditDrawerOpen(false)}>
                ×
              </button>
            </div>
            <div className="audit-drawer-body">
              <p style={{ marginBottom: '16px', color: '#666' }}>
                Review all active rules and their estimated impact before running the calculation:
              </p>
              
              <div className="audit-rules-list">
                {auditRules.map((rule, index) => (
                  <div key={rule.rule_id || index} className="audit-rule-item">
                    <div className="audit-rule-header">
                      <strong>{rule.node_name || rule.node_id}</strong>
                      <span className="audit-rule-badge">Rule #{rule.rule_id}</span>
                    </div>
                    <div className="audit-rule-details">
                      <div className="audit-rule-logic">
                        <strong>Logic:</strong> {rule.logic_en || 'N/A'}
                      </div>
                      <div className="audit-rule-impact">
                        <strong>Impact:</strong> {rule.affected_rows?.toLocaleString() || 0} of {rule.total_rows?.toLocaleString() || 0} rows ({rule.percentage?.toFixed(2) || 0}%)
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="audit-drawer-footer">
                <button
                  className="audit-button-cancel"
                  onClick={() => setAuditDrawerOpen(false)}
                >
                  Cancel
                </button>
                <button
                  className="audit-button-confirm"
                  onClick={handleConfirmCalculation}
                >
                  Confirm & Calculate
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default RuleEditor

