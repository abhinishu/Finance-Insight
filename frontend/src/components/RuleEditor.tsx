import React, { useState, useEffect, useCallback, useRef } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridApi, ColumnApi, ICellRendererParams } from 'ag-grid-community'
import axios from 'axios'
import { useReportingContext } from '../contexts/ReportingContext'
import SmartTooltip from './SmartTooltip'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import './RuleEditor.css'

// Phase 5: Measure Labels Map for Multi-Measure Rules
const MEASURE_LABELS: Record<string, string> = {
  'daily_pnl': 'Daily P&L',
  'pnl_commission': 'Commission P&L',
  'pnl_trade': 'Trade P&L',
  'ytd_pnl': 'YTD P&L'
}

// Helper function to format Math rule formulas: Replace node IDs with readable names
const formatFormula = (expression: string, hierarchyNodes: any[]): string => {
  if (!expression || !hierarchyNodes || hierarchyNodes.length === 0) {
    return expression || ''
  }
  
  // Create a map of node_id -> node_name for quick lookup
  const nodeMap = new Map<string, string>()
  hierarchyNodes.forEach(node => {
    if (node.node_id && node.node_name) {
      // Store both exact match and uppercase version (for case-insensitive matching)
      nodeMap.set(node.node_id, node.node_name)
      nodeMap.set(node.node_id.toUpperCase(), node.node_name)
    }
  })
  
  // Replace node IDs with node names in the expression
  // Use word boundaries to avoid partial matches (e.g., "NODE_5" shouldn't match "NODE_50")
  let formatted = expression
  
  // Sort node IDs by length (longest first) to avoid partial replacements
  const sortedNodeIds = Array.from(nodeMap.keys()).sort((a, b) => b.length - a.length)
  
  sortedNodeIds.forEach(nodeId => {
    const nodeName = nodeMap.get(nodeId)
    if (nodeName) {
      // Use regex with word boundaries to match whole node IDs only
      // Escape special regex characters in nodeId
      const escapedNodeId = nodeId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const regex = new RegExp(`\\b${escapedNodeId}\\b`, 'gi')
      formatted = formatted.replace(regex, nodeName)
    }
  })
  
  return formatted
}

// Rich Tooltip Component for Business Rule Badge (shared with ExecutiveDashboard)
const RichTooltip: React.FC<{ 
  ruleName: string
  ruleLogic: string | null
  impact: number
  children: React.ReactNode
}> = ({ ruleName, ruleLogic, impact, children }) => {
  const [showTooltip, setShowTooltip] = React.useState(false)
  const [tooltipPosition, setTooltipPosition] = React.useState({ x: 0, y: 0 })
  const tooltipRef = React.useRef<HTMLDivElement>(null)
  
  const formatCurrency = (value: number): string => {
    const isNegative = value < 0
    const absValue = Math.abs(value)
    const formatted = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(absValue)
    return isNegative ? `(${formatted})` : formatted
  }
  
  const handleMouseEnter = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect()
    setTooltipPosition({ x: rect.left, y: rect.top })
    setShowTooltip(true)
  }
  
  const handleMouseLeave = () => {
    setShowTooltip(false)
  }
  
  React.useEffect(() => {
    if (showTooltip && tooltipRef.current) {
      const tooltip = tooltipRef.current
      const rect = tooltip.getBoundingClientRect()
      const viewportWidth = window.innerWidth
      const viewportHeight = window.innerHeight
      
      // Adjust position if tooltip goes off screen
      let x = tooltipPosition.x
      let y = tooltipPosition.y - tooltip.offsetHeight - 8
      
      if (x + rect.width > viewportWidth) {
        x = viewportWidth - rect.width - 10
      }
      if (y < 0) {
        y = tooltipPosition.y + 30
      }
      
      tooltip.style.left = `${x}px`
      tooltip.style.top = `${y}px`
    }
  }, [showTooltip, tooltipPosition])
  
  return (
    <div
      style={{ position: 'relative', display: 'inline-block' }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      {showTooltip && (
        <div
          ref={tooltipRef}
          style={{
            position: 'fixed',
            zIndex: 10000,
            backgroundColor: '#1f2937',
            color: 'white',
            padding: '0.75rem',
            borderRadius: '6px',
            fontSize: '0.75rem',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
            pointerEvents: 'none',
            maxWidth: '300px',
            lineHeight: '1.5'
          }}
        >
          <div style={{ fontWeight: '700', marginBottom: '0.25rem', color: '#fbbf24' }}>
            {ruleName}
          </div>
          <div style={{ color: '#d1d5db', marginBottom: '0.25rem' }}>
            Logic: {ruleLogic || 'N/A'}
          </div>
          <div style={{ color: impact >= 0 ? '#10b981' : '#ef4444', fontFamily: 'monospace', fontWeight: '600' }}>
            Impact Here: ${formatCurrency(impact)}
          </div>
        </div>
      )}
    </div>
  )
}

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

// TreeNodeList Component for Sidebar
const TreeNodeList: React.FC<{
  nodes: HierarchyNode[]
  selectedNodeId: string | null
  onNodeSelect: (nodeId: string) => void
  rules: Map<string, any>
  expandedNodes: Set<string>
  onToggleExpand: (nodeId: string) => void
  depth?: number
  showAllNodes?: boolean // If true, show all nodes even if they have 0 rules
}> = ({ nodes, selectedNodeId, onNodeSelect, rules, expandedNodes, onToggleExpand, depth = 0, showAllNodes = true }) => {
  return (
    <div>
      {nodes.map((node) => {
        const hasChildren = node.children && node.children.length > 0
        const isExpanded = expandedNodes.has(node.node_id)
        const hasRule = rules.has(node.node_id)
        const isSelected = selectedNodeId === node.node_id
        
        return (
          <div key={node.node_id}>
              <div
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '6px 8px',
                paddingLeft: `${8 + depth * 20}px`,
                cursor: 'pointer',
                backgroundColor: isSelected ? '#dbeafe' : 'transparent',
                borderRadius: '4px',
                marginBottom: '1px',
                fontSize: '12px',
                transition: 'background-color 0.15s ease',
                borderLeft: depth > 0 ? `2px solid ${isSelected ? '#3b82f6' : 'transparent'}` : 'none'
              }}
              onClick={() => {
                if (hasChildren) {
                  onToggleExpand(node.node_id)
                }
                onNodeSelect(node.node_id)
              }}
              onMouseEnter={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.backgroundColor = '#f3f4f6'
                }
              }}
              onMouseLeave={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.backgroundColor = 'transparent'
                }
              }}
            >
              {hasChildren && (
                <span style={{ 
                  marginRight: '6px', 
                  fontSize: '11px', 
                  color: '#6b7280',
                  width: '12px',
                  display: 'inline-block',
                  textAlign: 'center'
                }}>
                  {isExpanded ? '▼' : '▶'}
                </span>
              )}
              {!hasChildren && (
                <span style={{ 
                  marginRight: '18px',
                  color: '#9ca3af',
                  fontSize: '10px'
                }}>•</span>
              )}
              <span style={{ 
                flex: 1, 
                fontWeight: isSelected ? '600' : depth === 0 ? '600' : 'normal',
                color: depth === 0 ? '#1f2937' : '#374151'
              }}>
                {node.node_name || node.node_id}
              </span>
              {hasRule && (
                <span
                  style={{
                    background: 'linear-gradient(135deg, #fef3c7, #fbbf24)',
                    color: '#d97706',
                    borderRadius: '3px',
                    padding: '2px 6px',
                    fontSize: '10px',
                    fontWeight: '600',
                    fontFamily: 'monospace',
                    marginLeft: '4px',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
                  }}
                  title="Has active rule"
                >
                  fx
                </span>
              )}
            </div>
            {hasChildren && isExpanded && (
              <TreeNodeList
                nodes={node.children}
                selectedNodeId={selectedNodeId}
                onNodeSelect={onNodeSelect}
                rules={rules}
                expandedNodes={expandedNodes}
                onToggleExpand={onToggleExpand}
                depth={depth + 1}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

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

// Phase 5.7: Rule interface for TypeScript type safety
interface Rule {
  rule_id?: number
  node_id?: string
  node_name?: string
  rule_type?: string | null
  rule_expression?: string | null
  rule_dependencies?: string[] | null
  logic_en?: string | null
  sql_where?: string | null
  predicate_json?: any
  last_modified_by?: string
  created_at?: string
  last_modified_at?: string
  affected_rows?: number
  total_rows?: number
  percentage?: number
  estimatedImpact?: number
}

const RuleEditor: React.FC = () => {
  // Use ReportingContext for globalTotal
  const { globalTotal } = useReportingContext()
  
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
  
  // Hierarchy Tree State (for future use if needed)
  const [hierarchyTree, setHierarchyTree] = useState<HierarchyNode[]>([])

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
  
  // Phase 5.7: Math Formula Textarea Ref (for cursor position tracking)
  const mathFormulaRef = useRef<HTMLTextAreaElement>(null)
  const [generating, setGenerating] = useState<boolean>(false)
  const [lastGenerateTime, setLastGenerateTime] = useState<number>(0)
  const [generateCooldown, setGenerateCooldown] = useState<number>(0) // Seconds remaining

  // Standard Mode State
  const [conditions, setConditions] = useState<RuleCondition[]>([
    { field: '', operator: 'equals', value: '' }
  ])
  
  // Phase 5.7: Rule Type Selector (Standard Mode only)
  const [standardRuleType, setStandardRuleType] = useState<'filter' | 'math'>('filter')
  
  // Phase 5.7: Math Formula State
  const [mathFormula, setMathFormula] = useState<string>('')
  
  // Phase 5: Target Metric Selector (Standard Mode - Filter only)
  const [selectedMeasure, setSelectedMeasure] = useState<string>('daily_pnl')

  // Rule Preview
  const [rulePreview, setRulePreview] = useState<RulePreview | null>(null)
  const [previewLoading, setPreviewLoading] = useState<boolean>(false)

  // Calculation
  const [calculating, setCalculating] = useState<boolean>(false)
  const [calculationResult, setCalculationResult] = useState<string | null>(null)
  
  // Success Modal State
  const [successModalOpen, setSuccessModalOpen] = useState<boolean>(false)
  const [successModalData, setSuccessModalData] = useState<{
    useCaseName: string
    pnlDate: string
    rulesCount: number
    totalPlug: string
    calculationTime: string
  } | null>(null)

  // Loading & Error States
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [errorDetails, setErrorDetails] = useState<{ message: string; statusCode?: number; canRetry: boolean } | null>(null)

  const gridRef = useRef<AgGridReact>(null)

  // Schema fields state (fetched from API based on use case)
  const [availableFields, setAvailableFields] = useState<Array<{ value: string; label: string }>>([
    // Default fields (fallback for Use Cases 1 & 2)
    { value: 'account_id', label: 'Account ID' },
    { value: 'cc_id', label: 'Cost Center ID' },
    { value: 'book_id', label: 'Book ID' },
    { value: 'strategy_id', label: 'Strategy ID' },
    { value: 'trade_date', label: 'Trade Date' },
  ])

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

  // Listen for use case deletion events to refresh the list
  useEffect(() => {
    const handleUseCaseDeleted = async (event: any) => {
      const deletedUseCaseId = event.detail?.useCaseId
      const currentSelectedId = selectedUseCaseId
      
      // Reload use cases
      await loadUseCases()
      
      // Clear selection if the deleted use case was the one selected
      if (currentSelectedId === deletedUseCaseId) {
        setSelectedUseCaseId('')
        setSelectedUseCase(null)
        setRowData([])
      }
    }

    window.addEventListener('useCaseDeleted', handleUseCaseDeleted as EventListener)
    return () => {
      window.removeEventListener('useCaseDeleted', handleUseCaseDeleted as EventListener)
    }
  }, [selectedUseCaseId])

  // FORCE REFRESH: Clear rules immediately on ID change to prevent stale state
  useEffect(() => {
    let isMounted = true

    if (selectedUseCaseId) {
      // Step 1: Wipe the board clean (Visual feedback)
      setRules(new Map())
      setRulesLoading(true)

      // Step 2: Fetch new rules with Cache-Busting
      const fetchRules = async () => {
        try {
          const response = await axios.get(
            `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules?t=${Date.now()}`
          )
          if (isMounted) {
            const rulesList = response.data || []
            
            // Create a Map for quick lookup: node_id -> rule with impact
            const rulesMap = new Map<string, any>()
            let totalAffectedRows = 0
            let totalRows = 0
            let totalAdjustment = 0
            
            // Load impact for each rule
            for (const rule of rulesList) {
              if (!rule.node_id) continue
              
              // Phase 5.7: Handle Math Rules (NODE_ARITHMETIC) differently
              if (rule.rule_type === 'NODE_ARITHMETIC') {
                // Math rules don't have sql_where, so skip impact preview
                // They use rule_expression instead
                rulesMap.set(rule.node_id, {
                  ...rule,
                  affected_rows: 0, // Math rules don't have row-based impact
                  total_rows: 0,
                  percentage: 0,
                  estimatedImpact: 0 // Could calculate from formula if needed
                })
                continue
              }
              
              // Standard SQL-based rules: get impact preview
              if (rule.sql_where) {
                try {
                  // Get impact preview
                  const previewResponse = await axios.post(
                    `${API_BASE_URL}/api/v1/rules/preview`,
                    { sql_where: rule.sql_where, use_case_id: selectedUseCaseId }
                  )
                  
                  // Estimate P&L impact (simplified: use affected_rows * average daily_pnl)
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
              } else {
                // Rule without sql_where (shouldn't happen for non-math rules, but handle gracefully)
                rulesMap.set(rule.node_id, {
                  ...rule,
                  affected_rows: 0,
                  total_rows: 0,
                  percentage: 0,
                  estimatedImpact: 0
                })
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
          }
        } catch (error) {
          console.error("Failed to load rules", error)
          if (isMounted) {
            setRules(new Map())
            setAuditSummary(null)
          }
        } finally {
          if (isMounted) {
            setRulesLoading(false)
          }
        }
      }

      fetchRules()
    } else {
      // Clear rules if no use case selected
      setRules(new Map())
      setAuditSummary(null)
      setRulesLoading(false)
    }

    return () => { isMounted = false }
  }, [selectedUseCaseId]) // CRITICAL: Run whenever ID changes

  // Phase 5.9: Smart Default Mode Detection - Load existing rule when modal opens
  useEffect(() => {
    if (modalOpen && selectedNodes.length === 1) {
      const node = selectedNodes[0]
      
      if (node.hasRule && node.rule) {
        const rule = node.rule
        
        // Determine default mode based on rule type
        if (rule.rule_type === 'NODE_ARITHMETIC' && rule.rule_expression) {
          // Math Rule - Standard Mode (Math)
          setEditorMode('standard')
          setStandardRuleType('math')
          setMathFormula(rule.rule_expression)
          setRulePreview({
            logic_en: `Math Formula: ${rule.rule_expression}`,
            sql_where: '',
            predicate_json: null,
            translation_successful: true
          })
        } else if (rule.predicate_json) {
          // Standard Mode Filter rule - default to Standard Mode
          setEditorMode('standard')
          setStandardRuleType('filter')
          setSelectedMeasure(rule.measure_name || 'daily_pnl')
          
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
          
          // Load preview
          if (rule.sql_where) {
            setRulePreview({
              logic_en: rule.logic_en,
              sql_where: rule.sql_where,
              predicate_json: rule.predicate_json,
              translation_successful: true
            })
          }
        } else if (rule.logic_en) {
          // AI Mode rule - default to AI Mode
          setEditorMode('ai')
          setAiPrompt(rule.logic_en)
          
          // Load preview if available
          if (rule.sql_where) {
            setRulePreview({
              logic_en: rule.logic_en,
              sql_where: rule.sql_where,
              predicate_json: rule.predicate_json,
              translation_successful: true
            })
          }
        }
      } else {
        // No existing rule - default to Standard Mode (as user requested)
        setEditorMode('standard')
        setStandardRuleType('filter')
        setSelectedMeasure('daily_pnl')
        setConditions([{ field: '', operator: 'equals', value: '' }])
        setAiPrompt('')
        setMathFormula('')
        setRulePreview(null)
      }
    }
  }, [modalOpen, selectedNodes])

  // Load schema fields when use case is selected
  useEffect(() => {
    const loadSchemaFields = async () => {
      if (!selectedUseCaseId) {
        // Reset to default fields if no use case selected
        setAvailableFields([
          { value: 'account_id', label: 'Account ID' },
          { value: 'cc_id', label: 'Cost Center ID' },
          { value: 'book_id', label: 'Book ID' },
          { value: 'strategy_id', label: 'Strategy ID' },
          { value: 'trade_date', label: 'Trade Date' },
        ])
        setAvailableFieldsForHelper([
          { field: 'book_id', label: 'Book ID', type: 'String' },
          { field: 'strategy_id', label: 'Strategy ID', type: 'String' },
          { field: 'account_id', label: 'Account ID', type: 'String' },
          { field: 'cc_id', label: 'Cost Center ID', type: 'String' },
          { field: 'trade_date', label: 'Trade Date', type: 'Date' },
          { field: 'daily_pnl', label: 'Daily P&L', type: 'Numeric' },
          { field: 'mtd_pnl', label: 'MTD P&L', type: 'Numeric' },
          { field: 'ytd_pnl', label: 'YTD P&L', type: 'Numeric' },
        ])
        return
      }

      try {
        const response = await axios.get(
          `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/schema`
        )
        
        const schemaData = response.data
        if (schemaData && schemaData.fields) {
          // Update availableFields for Standard Mode dropdown
          setAvailableFields(schemaData.fields.map((f: any) => ({
            value: f.value,
            label: f.label
          })))
          
          // Update availableFieldsForHelper (dimension fields + measure fields)
          const dimensionFields = schemaData.fields.map((f: any) => ({
            field: f.value,
            label: f.label,
            type: f.type
          }))
          
          // Add measure fields (these are consistent across all use cases)
          const measureFields = [
            { field: 'daily_pnl', label: 'Daily P&L', type: 'Numeric' },
            { field: 'mtd_pnl', label: 'MTD P&L', type: 'Numeric' },
            { field: 'ytd_pnl', label: 'YTD P&L', type: 'Numeric' },
          ]
          
          setAvailableFieldsForHelper([...dimensionFields, ...measureFields])
          
          console.log(`[RuleEditor] Loaded schema for use case ${selectedUseCaseId}:`, schemaData)
        }
      } catch (err: any) {
        console.error('Failed to load schema fields:', err)
        // Keep default fields on error
      }
    }

    loadSchemaFields()
  }, [selectedUseCaseId])

  // Load hierarchy when use case is selected
  useEffect(() => {
    if (selectedUseCase && selectedUseCaseId) {
      loadHierarchyForUseCase(selectedUseCaseId, selectedUseCase.atlas_structure_id)
      
      // Load shared tree state (Tab 2 & 3 unification)
      // Only use saved state if it has meaningful expansion (more than just root)
      const stateKey = getTreeStateKey(selectedUseCase.atlas_structure_id)
      const savedState = localStorage.getItem(stateKey)
      if (savedState) {
        try {
          const state = JSON.parse(savedState)
          // Only use saved state if it has meaningful expansion (more than just root nodes)
          if (state.expandedNodes && state.expandedNodes.length > 1) {
            setExpandedNodes(new Set(state.expandedNodes))
          }
          // If saved state is minimal or empty, default expansion will be set in loadHierarchyForUseCase
        } catch (e) {
          console.warn('Failed to load shared tree state:', e)
          // Fallback: default expansion will be set in loadHierarchyForUseCase
        }
      }
      // If no saved state, default expansion will be set in loadHierarchyForUseCase
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
      // Ensure path is always a valid array
      let path: string[] = []
      if (node.path && Array.isArray(node.path) && node.path.length > 0) {
        // Use path from API (from SQL CTE)
        path = node.path
      } else if (parentPath.length > 0) {
        // Build path from parent path + current node name
        path = parentPath.concat([node.node_name || node.node_id || 'Unknown'])
      } else {
        // Root node - path is just the node name
        path = [node.node_name || node.node_id || 'Unknown']
      }
      
      // Validate path is never empty
      if (path.length === 0) {
        path = [node.node_name || node.node_id || 'Unknown']
      }
      
      // Check if this node has an active rule (safe access with null check)
      const hasRule = rules && rules instanceof Map && rules.has(node.node_id)
      const rule = hasRule && rules instanceof Map ? rules.get(node.node_id) : null
      
      const row = {
        ...node,
        path, // Path array for hierarchy tracking (used by manual tree engine) - MUST be array of strings
        hasRule: !!hasRule, // Flag for conditional rendering (ensure boolean)
        rule: rule || null, // Store rule data for recall
        ruleImpact: rule?.estimatedImpact || 0, // Dollar impact for heatmap
        hasConflict: false, // Will be set when rule stack is loaded
        // Parse P&L values from strings to numbers for grid display
        daily_pnl: parseFloat(node.daily_pnl) || 0,
        mtd_pnl: parseFloat(node.mtd_pnl) || 0,
        ytd_pnl: parseFloat(node.ytd_pnl) || 0,
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
      if (selectedUseCase && selectedUseCaseId) {
        loadHierarchyForUseCase(selectedUseCaseId, selectedUseCase.atlas_structure_id)
      }
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
      
      // Auto-select first use case if available (but check localStorage first)
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
      setError('Failed to load use cases. Please ensure the backend is running.')
    }
  }

  // Load hierarchy using results endpoint for Adjusted P&L (with fallback to hierarchy endpoint)
  const loadHierarchyForUseCase = useCallback(async (useCaseId: string, structureId: string) => {
    if (!useCaseId || !structureId) return

    // CRITICAL: Log current use case ID to verify it's correct
    console.log('='.repeat(80))
    console.log('CURRENT USE CASE ID IN TAB 3:', useCaseId)
    console.log('STRUCTURE ID:', structureId)
    console.log('='.repeat(80))

    setLoading(true)
    setError(null)
    setErrorDetails(null)

    try {
      // Try results endpoint first (for Adjusted P&L values)
      let response
      let hierarchy: HierarchyNode[] = []
      
      try {
        // Try results endpoint to get Adjusted P&L
        // CRITICAL: Add timestamp to bust server-side caching
        const timestamp = Date.now()
        const resultsResponse = await axios.get(
          `${API_BASE_URL}/api/v1/use-cases/${useCaseId}/results?t=${timestamp}`
        )
        
        // Results endpoint returns different format - convert to hierarchy format
        // CRITICAL: If results are empty, immediately fall back to unified_pnl_service via discovery endpoint
        if (resultsResponse.data?.hierarchy && resultsResponse.data.hierarchy.length > 0) {
          // Convert ResultsNode format to HierarchyNode format
          const convertResultsToHierarchy = (nodes: any[]): HierarchyNode[] => {
            return nodes.map(node => ({
              node_id: node.node_id,
              node_name: node.node_name,
              parent_node_id: node.parent_node_id,
              depth: node.depth || 0,
              is_leaf: node.is_leaf || false,
              // Always show Natural Value in Rule Editor so users see the "Source Data"
              // This matches Tab 4 behavior (Original Daily P&L = Natural Value)
              daily_pnl: node.natural_value?.daily?.toString() || '0',
              mtd_pnl: node.natural_value?.mtd?.toString() || '0',
              ytd_pnl: node.natural_value?.ytd?.toString() || '0',
              path: node.path || [node.node_name],
              children: node.children ? convertResultsToHierarchy(node.children) : []
            }))
          }
          
          hierarchy = convertResultsToHierarchy(resultsResponse.data.hierarchy)
          console.log('Tab 3: Loaded Natural P&L (Original values) from results endpoint')
        } else {
          // CRITICAL: No results available - immediately fall back to discovery endpoint (unified_pnl_service)
          console.log('Tab 3: No results found, falling back to discovery endpoint (unified_pnl_service baseline)')
          throw new Error('No results available - using baseline from unified_pnl_service')
        }
      } catch (resultsErr: any) {
        // Fallback to hierarchy endpoint (natural rollups)
        console.warn('Tab 3: Results endpoint failed or no results, using hierarchy endpoint:', resultsErr)
        try {
          // CRITICAL: Add timestamp to bust server-side caching
          const timestamp = Date.now()
          response = await axios.get<DiscoveryResponse>(
            `${API_BASE_URL}/api/v1/use-cases/${useCaseId}/hierarchy?t=${timestamp}`
          )
          hierarchy = response.data?.hierarchy || []
        } catch (useCaseErr: any) {
          // Final fallback to discovery endpoint
          // CRITICAL: Add timestamp and use_case_id to bust server-side caching
          console.warn('Tab 3: Use-case hierarchy endpoint failed, falling back to discovery:', useCaseErr)
          const timestamp = Date.now()
          response = await axios.get<DiscoveryResponse>(
            `${API_BASE_URL}/api/v1/discovery`,
            { params: { structure_id: structureId, use_case_id: useCaseId, t: timestamp } }
          )
          hierarchy = response.data?.hierarchy || []
        }
      }

      if (hierarchy.length === 0) {
        setError('No hierarchy data found.')
        setErrorDetails({
          message: 'No hierarchy data found. The structure may be empty.',
          canRetry: true
        })
        setRowData([])
        setHierarchyTree([])
        setLoading(false)
        return
      }

      // Store hierarchy tree for sidebar
      setHierarchyTree(hierarchy)

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
      setExpandedNodes(expandAllNodes(hierarchy))

      // Flatten hierarchy for AG-Grid (with rule information)
      try {
        const flatData = flattenHierarchy(hierarchy)
        
        // Debug: Log hierarchy data
        console.log('RuleEditor: Hierarchy loaded successfully', {
          hierarchyLength: hierarchy.length,
          flatDataLength: flatData.length,
          firstNode: flatData[0],
          samplePaths: flatData.slice(0, 5).map(d => ({ node_name: d.node_name, path: d.path }))
        })
        
        // Validate paths
        const invalidPaths = flatData.filter(d => !d.path || !Array.isArray(d.path) || d.path.length === 0)
        if (invalidPaths.length > 0) {
          console.warn('RuleEditor: Found nodes with invalid paths:', invalidPaths)
          // Fix invalid paths
          invalidPaths.forEach(node => {
            node.path = [node.node_name || node.node_id || 'Unknown']
          })
        }
        
        setRowData(flatData)
        
        // Initialize expandedNodes: expand first 4 levels by default (matches Tab 2)
        const defaultExpanded = new Set<string>()
        flatData.forEach(row => {
          if (row.depth < 4 && !row.is_leaf) {
            defaultExpanded.add(row.node_id)
          }
        })
        setExpandedNodes(defaultExpanded)
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
        
        // Initialize expandedNodes for fallback data: expand first 4 levels (matches Tab 2)
        const defaultExpanded = new Set<string>()
        fallbackData.forEach(row => {
          if (row.depth < 4 && !row.is_leaf) {
            defaultExpanded.add(row.node_id)
          }
        })
        setExpandedNodes(defaultExpanded)
      }
    } catch (err: any) {
      console.error('Failed to load hierarchy:', err)
      const statusCode = err.response?.status
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load hierarchy data.'
      
      // Log detailed error for debugging
      console.error('Hierarchy load error details:', {
        statusCode,
        message: errorMessage,
        response: err.response?.data,
        useCaseId,
        structureId
      })
      
      setError(errorMessage)
      setErrorDetails({
        message: errorMessage,
        statusCode,
        canRetry: statusCode === 404 || statusCode === 500 || statusCode >= 500 || !statusCode
      })
      
      // Set empty data to prevent grid errors
      setRowData([])
      setHierarchyTree([])
    } finally {
      setLoading(false)
    }
  }, [flattenHierarchy])

  const loadHierarchy = useCallback(async (structureId: string) => {
    if (!structureId) return

    setLoading(true)
    setError(null)
    setErrorDetails(null)

    try {
      // CRITICAL: Add timestamp to bust server-side caching
      const timestamp = Date.now()
      const response = await axios.get<DiscoveryResponse>(
        `${API_BASE_URL}/api/v1/discovery`,
        { params: { structure_id: structureId, t: timestamp } }
      )

      const hierarchy = response.data?.hierarchy || []
      if (hierarchy.length === 0) {
        setError('No hierarchy data found.')
        setErrorDetails({
          message: 'No hierarchy data found. The structure may be empty.',
          canRetry: true
        })
        setRowData([])
        setHierarchyTree([])
        setLoading(false)
        return
      }

      // Store hierarchy tree for sidebar
      setHierarchyTree(hierarchy)

      // Flatten hierarchy for AG-Grid (with rule information)
      // Safe call - flattenHierarchy handles null/undefined rules
      try {
        const flatData = flattenHierarchy(hierarchy)
        setRowData(flatData)
        
        // Initialize expandedNodes: expand first 4 levels by default (matches Tab 2)
        const defaultExpanded = new Set<string>()
        flatData.forEach(row => {
          if (row.depth < 4 && !row.is_leaf) {
            defaultExpanded.add(row.node_id)
          }
        })
        setExpandedNodes(defaultExpanded)
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
        
        // Initialize expandedNodes for fallback data: expand first 4 levels (matches Tab 2)
        const defaultExpanded = new Set<string>()
        fallbackData.forEach(row => {
          if (row.depth < 4 && !row.is_leaf) {
            defaultExpanded.add(row.node_id)
          }
        })
        setExpandedNodes(defaultExpanded)
      }
    } catch (err: any) {
      console.error('Failed to load hierarchy:', err)
      const statusCode = err.response?.status
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load hierarchy data.'
      
      // Log detailed error for debugging
      console.error('Hierarchy load error details:', {
        statusCode,
        message: errorMessage,
        response: err.response?.data,
        url: `${API_BASE_URL}/api/v1/discovery?structure_id=${structureId}`
      })
      
      setError(errorMessage)
      setErrorDetails({
        message: errorMessage,
        statusCode,
        canRetry: statusCode === 404 || statusCode === 500 || statusCode >= 500 || !statusCode
      })
      
      // Set empty data to prevent grid errors
      setRowData([])
      setHierarchyTree([])
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

  // Check calculation freshness - Use backend's is_outdated flag instead of client-side comparison
  useEffect(() => {
    if (!selectedUseCaseId) return
    
    const checkFreshness = async () => {
      try {
        // Get results from backend which includes is_outdated flag (with grace period)
        const response = await axios.get(
          `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/results`
        )
        
        // Use backend's is_outdated flag (computed with 2-second grace period)
        if (response.data?.is_outdated !== undefined) {
          setIsCalculationOutdated(response.data.is_outdated)
        }
        
        // Also update lastCalculated timestamp if available
        if (response.data?.run_timestamp) {
          setLastCalculated(response.data.run_timestamp)
        }
        
        // Get latest rule modification time for display purposes
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
          }
        }
      } catch (err) {
        console.error('Failed to check freshness:', err)
      }
    }
    
    checkFreshness()
  }, [selectedUseCaseId])

  // Load last calculated timestamp and outdated status
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
        // Use backend's is_outdated flag (computed with grace period)
        if (response.data?.is_outdated !== undefined) {
          setIsCalculationOutdated(response.data.is_outdated)
        }
      } catch (err) {
        // No runs yet
        setLastCalculated(null)
        setIsCalculationOutdated(false)
      }
    }
    
    loadLastRun()
  }, [selectedUseCaseId])

  // Load sample values for a field
  const loadSampleValues = async (fieldName: string) => {
    if (sampleValues.has(fieldName) || loadingSamples.has(fieldName)) return

    setLoadingSamples(prev => new Set(prev).add(fieldName))
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/fact-values/${fieldName}?limit=5`
      )
      setSampleValues(prev => new Map(prev).set(fieldName, response.data.sample_values || []))
    } catch (err) {
      console.error(`Failed to load sample values for ${fieldName}:`, err)
    } finally {
      setLoadingSamples(prev => {
        const next = new Set(prev)
        next.delete(fieldName)
        return next
      })
    }
  }

  // Available schema fields for Field Helper Tag Cloud (derived from availableFields + measures)
  const [availableFieldsForHelper, setAvailableFieldsForHelper] = useState<Array<{ field: string; label: string; type: string }>>([
    // Default fields (fallback)
    { field: 'book_id', label: 'Book ID', type: 'String' },
    { field: 'strategy_id', label: 'Strategy ID', type: 'String' },
    { field: 'account_id', label: 'Account ID', type: 'String' },
    { field: 'cc_id', label: 'Cost Center ID', type: 'String' },
    { field: 'trade_date', label: 'Trade Date', type: 'Date' },
    { field: 'daily_pnl', label: 'Daily P&L', type: 'Numeric' },
    { field: 'mtd_pnl', label: 'MTD P&L', type: 'Numeric' },
    { field: 'ytd_pnl', label: 'YTD P&L', type: 'Numeric' },
  ])

  // Sample values state for Field Helper
  const [sampleValues, setSampleValues] = useState<Map<string, string[]>>(new Map())
  const [loadingSamples, setLoadingSamples] = useState<Set<string>>(new Set())
  
  // Autocomplete state for value input
  const [autocompleteOpen, setAutocompleteOpen] = useState<Map<number, boolean>>(new Map())
  const [autocompleteFilter, setAutocompleteFilter] = useState<Map<number, string>>(new Map())

  // Phase 5.7: Helper function to determine if a rule is a Math Rule
  const isMathRule = (rule: any): boolean => {
    if (!rule) return false
    // Primary check: rule_type field
    if (rule.rule_type === 'NODE_ARITHMETIC') return true
    // Fallback: If rule has rule_expression but no logic_en or sql_where, it's likely a math rule
    if (rule.rule_expression && !rule.logic_en && !rule.sql_where) return true
    return false
  }

  // Toggle node expansion (Manual Tree Engine)
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

  // Manual Tree Cell Renderer (replaces Native AG-Grid Tree)
  // Matches DiscoveryScreen.tsx visual density and indentation
  const nodeNameCellRenderer = useCallback((params: any) => {
    const data = params.data
    if (!data) return ''
    
    const depth = data.depth || 0
    const isLeaf = data.is_leaf || false
    const isExpanded = expandedNodes.has(data.node_id)
    const paddingLeft = depth * 20 + 8 // 20px per level + 8px base
    
    const nodeName = data.node_name || params.value || ''
    const rule = data.rule
    const hasRule = data.hasRule || false
    const isMath = rule ? isMathRule(rule) : false
    
    // Chevron for non-leaf nodes
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
    
    // Render rule badge (from HierarchyGroupInnerRenderer logic)
    const renderRuleBadge = () => {
      if (!hasRule || !rule) return null
      
      if (isMath) {
        // Math Rule Badge (Blue)
        return (
          <span
            style={{
              background: '#dbeafe',
              color: '#1e40af',
              padding: '0.125rem 0.5rem',
              borderRadius: '3px',
              fontSize: '0.7rem',
              fontWeight: '600',
              marginLeft: '8px',
              cursor: 'pointer'
            }}
            className="fx-icon-badge"
            data-fx-icon="true"
            title={`Math Formula: ${rule.rule_expression || 'No formula'}`}
            onClick={(e) => {
              e.stopPropagation()
              // Trigger parent cell click handler for inheritance overlay
              if (params.onCellClicked) {
                params.onCellClicked({
                  ...params,
                  event: e.nativeEvent
                } as any)
              }
            }}
          >
            Math
          </span>
        )
      } else {
        // SQL Rule Badge (Yellow/Amber)
        return (
          <span
            style={{
              background: 'linear-gradient(135deg, #fef3c7, #fbbf24)',
              color: '#d97706',
              borderRadius: '3px',
              padding: '2px 6px',
              fontSize: '10px',
              fontWeight: '600',
              fontFamily: 'monospace',
              marginLeft: '8px',
              boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
              cursor: 'pointer'
            }}
            className="fx-icon-badge"
            data-fx-icon="true"
            title={`SQL Rule: ${rule.logic_en || rule.sql_where || 'No logic'}`}
            onClick={(e) => {
              e.stopPropagation()
              // Trigger parent cell click handler for inheritance overlay
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
        )
      }
    }
    
    return (
      <div style={{ 
        paddingLeft: `${paddingLeft}px`,
        display: 'flex',
        alignItems: 'center',
        fontWeight: depth === 0 ? '600' : depth === 1 ? '500' : '400',
        color: depth === 0 ? '#2c3e50' : '#333'
      }}>
        {chevron}
        <span>{nodeName}</span>
        {renderRuleBadge()}
      </div>
    )
  }, [expandedNodes, toggleNodeExpansion, isMathRule])

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

  // Native Tree Group Cell Inner Renderer (for rule badges)
  // DEPRECATED: Replaced by nodeNameCellRenderer (Manual Tree Engine)
  // Kept for reference but no longer used
  const HierarchyGroupInnerRenderer: React.FC<ICellRendererParams> = (params) => {
    const nodeName = params.value || params.data?.node_name || ''
    const rule = params.data?.rule
    const hasRule = params.data?.hasRule || false
    const isMath = rule ? isMathRule(rule) : false
    
    // Determine node type for icon
    const getNodeIcon = () => {
      const depth = params.data?.depth || 0
      if (depth === 0) {
        return '🌐' // Globe for Root
      } else if (params.data?.region || nodeName.includes('Americas') || nodeName.includes('EMEA') || nodeName.includes('APAC')) {
        return '📍' // MapPin for Region
      } else if (params.data?.book || nodeName.includes('Book')) {
        return '💼' // Briefcase for Book
      } else if (params.data?.cost_center || nodeName.includes('Cost Center') || nodeName.includes('Trade')) {
        return '#' // Hash for Cost Center
      }
      return ''
    }
    
    // Render rule badge
    const renderRuleBadge = () => {
      if (!hasRule || !rule) return null
      
      if (isMath) {
        // Math Rule Badge (Blue)
        return (
          <span
            style={{
              background: '#dbeafe',
              color: '#1e40af',
              padding: '0.125rem 0.5rem',
              borderRadius: '3px',
              fontSize: '0.7rem',
              fontWeight: '600',
              marginLeft: '8px',
              cursor: 'pointer'
            }}
            className="fx-icon-badge"
            data-fx-icon="true"
            title={`Math Formula: ${rule.rule_expression || 'No formula'}`}
          >
            Math
          </span>
        )
      } else {
        // SQL Rule Badge (Yellow/Amber)
        return (
          <span
            style={{
              background: 'linear-gradient(135deg, #fef3c7, #fbbf24)',
              color: '#d97706',
              borderRadius: '3px',
              padding: '2px 6px',
              fontSize: '10px',
              fontWeight: '600',
              fontFamily: 'monospace',
              marginLeft: '8px',
              boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
              cursor: 'pointer'
            }}
            className="fx-icon-badge"
            data-fx-icon="true"
            title={`SQL Rule: ${rule.logic_en || rule.sql_where || 'No logic'}`}
          >
            fx
          </span>
        )
      }
    }
    
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        height: '100%',
        paddingLeft: '8px'
      }}>
        {getNodeIcon() && <span style={{ marginRight: '6px', fontSize: '14px' }}>{getNodeIcon()}</span>}
        <span style={{
          fontSize: '0.875rem',
          fontWeight: 500,
          color: '#374151'
        }}>
          {nodeName}
        </span>
        {renderRuleBadge()}
      </div>
    )
  }

  // Status Pill Renderer for Business Rule column (with Rich Tooltip)
  const BusinessRuleCellRenderer: React.FC<ICellRendererParams> = (params) => {
    const rule = params.data?.rule
    
    if (!rule) {
      return <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>—</span>
    }
    
    // Phase 5.7: Handle Math Rules (NODE_ARITHMETIC)
    const isMath = isMathRule(rule)
    
    // For Math Rules, display the formula (even if rule_expression is empty, show placeholder)
    if (isMath) {
      const rawFormula = rule.rule_expression || 'No formula defined'
      // Phase 5.9: Format formula to replace node IDs with readable names
      const formula = formatFormula(rawFormula, rowData)
      const original = parseFloat(params.data?.daily_pnl || params.data?.natural_value?.daily || 0)
      const adjusted = parseFloat(params.data?.adjusted_daily || params.data?.adjusted_value?.daily || 0)
      const impact = adjusted - original
      
      const tooltipContent = (
        <div>
          <div style={{ fontWeight: '700', marginBottom: '0.25rem', color: '#1e40af' }}>
            Math Formula
          </div>
          <div style={{ color: '#d1d5db', marginBottom: '0.25rem', fontSize: '0.8rem', fontFamily: 'monospace' }}>
            {formula}
          </div>
          {rule.rule_dependencies && rule.rule_dependencies.length > 0 && (
            <div style={{ color: '#059669', marginBottom: '0.25rem', fontSize: '0.7rem' }}>
              Dependencies: {rule.rule_dependencies.join(', ')}
            </div>
          )}
          <div style={{ 
            color: impact >= 0 ? '#10b981' : '#ef4444', 
            fontFamily: 'monospace', 
            fontWeight: '600',
            fontSize: '0.875rem'
          }}>
            Impact: ${impact >= 0 ? '+' : ''}${impact.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
      )
      
      return (
        <SmartTooltip content={tooltipContent}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{
              background: '#dbeafe',
              color: '#1e40af',
              padding: '0.125rem 0.5rem',
              borderRadius: '3px',
              fontSize: '0.7rem',
              fontWeight: '600'
            }}>
              Math
            </span>
            <span style={{ 
              color: '#6b7280', 
              fontSize: '0.875rem',
              fontFamily: 'monospace'
            }}>
              {formula}
            </span>
          </div>
        </SmartTooltip>
      )
    }
    
    // Standard SQL-based rules (existing logic)
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
    
    // Phase 5: Get measure label for filter rules (Multi-Measure support)
    const measureLabel = rule.measure_name && MEASURE_LABELS[rule.measure_name] 
      ? MEASURE_LABELS[rule.measure_name] 
      : null
    
    // Calculate impact (adjusted - original)
    const original = parseFloat(params.data?.daily_pnl || params.data?.natural_value?.daily || 0)
    const adjusted = parseFloat(params.data?.adjusted_daily || params.data?.adjusted_value?.daily || 0)
    const impact = adjusted - original
    
    const ruleLogic = rule.sql_where || (rule.predicate_json ? JSON.stringify(rule.predicate_json) : null)
    
    const tooltipContent = (
      <div>
        {/* Phase 5: Display measure name in tooltip */}
        {measureLabel && (
          <div style={{ 
            fontWeight: '600', 
            marginBottom: '0.25rem', 
            color: '#059669',
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            Target: {measureLabel}
          </div>
        )}
        <div style={{ fontWeight: '700', marginBottom: '0.25rem', color: '#fbbf24' }}>
          {rule.logic_en}
        </div>
        {ruleLogic && (
          <div style={{ color: '#d1d5db', marginBottom: '0.25rem', fontSize: '0.7rem' }}>
            Logic: {ruleLogic}
          </div>
        )}
        <div style={{ 
          color: impact >= 0 ? '#10b981' : '#ef4444', 
          fontFamily: 'monospace', 
          fontWeight: '600',
          fontSize: '0.875rem'
        }}>
          Impact: ${impact >= 0 ? '+' : ''}${impact.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
      </div>
    )
    
    // Phase 5: Format display text with measure context (polished formatting)
    const baseLogicText = rule.logic_en || rule.sql_where || 'No rule logic'
    let displayText: React.ReactNode = baseLogicText
    
    // If measure is specified and not default, format as "Sum(Measure): Logic"
    if (measureLabel && rule.measure_name !== 'daily_pnl') {
      displayText = (
        <>
          <strong style={{ color: '#374151', fontWeight: '600' }}>
            Sum({measureLabel}):
          </strong>{' '}
          <span style={{ color: '#6b7280' }}>{baseLogicText}</span>
        </>
      )
    } else {
      // Default: just show the logic text
      displayText = <span style={{ color: '#6b7280' }}>{baseLogicText}</span>
    }
    
    return (
      <SmartTooltip content={tooltipContent}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span className={pillClass}>{pillText}</span>
          <span style={{ fontSize: '0.875rem' }}>
            {displayText}
          </span>
        </div>
      </SmartTooltip>
    )
  }

  // Financial formatter (standard format)
  const financialFormatter = (params: any) => {
    if (!params.value && params.value !== 0) return ''
    const value = typeof params.value === 'number' ? params.value : parseFloat(params.value)
    if (isNaN(value)) return ''
    
    const isNegative = value < 0
    const absValue = Math.abs(value)
    const formatted = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(absValue)
    
    return isNegative ? `(${formatted})` : formatted
  }

  // Cell class rules for red negatives
  const cellClassRules = {
    'negative-value': (params: any) => {
      if (params.value == null) return false
      const value = typeof params.value === 'number' ? params.value : parseFloat(params.value)
      return !isNaN(value) && value < 0
    }
  }

  // AG-Grid Column Definitions (Manual Tree Engine - Matches Tab 2)
  const columnDefs: ColDef[] = [
    {
      field: 'node_name',
      headerName: 'Hierarchy',
      minWidth: 350,
      pinned: 'left',
      checkboxSelection: true,
      headerCheckboxSelection: true,
      cellRenderer: nodeNameCellRenderer,
      cellStyle: (params: any) => {
        const depth = params.data?.depth || 0
        return {
          backgroundColor: depth === 0 ? '#f0f4f8' : depth === 1 ? '#f9f9f9' : '#ffffff',
          borderLeft: depth > 1 ? '1px solid #e0e0e0' : 'none',
        }
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
    },
    {
      field: 'business_rule',
      headerName: 'Business Rule',
      flex: 2,
      cellRenderer: BusinessRuleCellRenderer,
    },
    {
      field: 'daily_pnl',
      headerName: 'Daily P&L',
      width: 150,
      valueFormatter: financialFormatter,
      cellClass: 'monospace-number',
      cellClassRules: cellClassRules,
      cellStyle: { textAlign: 'right' },
    },
    {
      field: 'mtd_pnl',
      headerName: 'MTD P&L',
      width: 150,
      valueFormatter: financialFormatter,
      cellClass: 'monospace-number',
      cellClassRules: cellClassRules,
      cellStyle: { textAlign: 'right' },
    },
    {
      field: 'ytd_pnl',
      headerName: 'YTD P&L',
      width: 150,
      valueFormatter: financialFormatter,
      cellClass: 'monospace-number',
      cellClassRules: cellClassRules,
      cellStyle: { textAlign: 'right' },
    },
  ]

  const defaultColDef: ColDef = {
    sortable: true,
    filter: true,
    resizable: true,
  }

  // Structural Column row styling with zebra striping and conflict detection
  // Clean Look: Removed inline height and border styles (handled by CSS)
  const getRowStyle = (params: any) => {
    const baseStyle: any = {
      // Height removed - let CSS handle 32px via rowHeight prop
      padding: 0
    }
    
    // Zebra striping: even rows get subtle gray background
    if (params.node.rowIndex % 2 === 1) {
      baseStyle.backgroundColor = 'rgba(249, 250, 251, 0.3)' // gray-50/30
    }
    
    // Conflict row: Faded red background (overrides zebra)
    const hasConflict = params.data?.hasConflict || false
    if (hasConflict) {
      baseStyle.backgroundColor = '#fff5f5'
      baseStyle.borderLeft = '3px solid #dc2626'
    }
    
    // Level-based styling (keep for root nodes)
    const depth = params.data?.depth || 0
    if (depth === 0) {
      baseStyle.fontWeight = '700'
      // borderBottom removed - CSS handles transparent borders for clean look
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
    
    // Manual Tree Engine: Trigger external filter after grid is ready
    setTimeout(() => {
      if (params.api) {
        params.api.onFilterChanged()
      }
    }, 100)
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
          
          // Phase 5.7: Check if this is a Math Rule (NODE_ARITHMETIC)
          if (rule.rule_type === 'NODE_ARITHMETIC' && rule.rule_expression) {
            // Load math formula into Standard Mode
            setEditorMode('standard')
            setStandardRuleType('math')
            setMathFormula(rule.rule_expression)
            setRulePreview({
              logic_en: `Math Formula: ${rule.rule_expression}`,
              sql_where: '', // Math rules don't have SQL
              predicate_json: null,
              translation_successful: true
            })
          } else if (rule.logic_en) {
            // AI Mode rule
            setAiPrompt(rule.logic_en)
            setEditorMode('ai')
          } else if (rule.predicate_json) {
            // Standard Mode Filter rule
            setEditorMode('standard')
            setStandardRuleType('filter')
            // Phase 5: Set target metric from existing rule (backward compatibility)
            setSelectedMeasure(rule.measure_name || 'daily_pnl')
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
          
          // Load preview if available (for filter rules)
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
          setMathFormula('')
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
    
    // Load sample values when field changes
    if (field === 'field' && value) {
      loadSampleValues(value)
    }
    
    // Show autocomplete when typing in value field
    if (field === 'value') {
      setAutocompleteFilter(prev => new Map(prev).set(index, value))
      const fieldName = updated[index].field
      if (fieldName && !sampleValues.has(fieldName)) {
        loadSampleValues(fieldName)
      }
    }
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

  // Phase 5.7: Extract node dependencies from math formula
  const extractDependencies = (formula: string): string[] => {
    // Match patterns like NODE_A, NODE_3, NODE_AMER_CASH_NY_001, etc.
    const nodePattern = /\bNODE_[\w]+\b/gi
    const matches = formula.match(nodePattern)
    if (!matches) return []
    // Return unique node IDs (case-insensitive)
    return Array.from(new Set(matches.map(m => m.toUpperCase())))
  }

  // Phase 5.7: Insert node reference into formula at cursor position
  const insertNodeReference = (nodeId: string) => {
    const textarea = mathFormulaRef.current
    if (!textarea) {
      // Fallback: append to end if ref not available
      setMathFormula(prev => prev + (prev ? ' + ' : '') + nodeId)
      return
    }
    
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const currentValue = mathFormula
    const before = currentValue.substring(0, start)
    const after = currentValue.substring(end)
    
    // Insert node ID with space before if needed
    const insertText = (before && !before.match(/\s$/)) ? ' ' + nodeId : nodeId
    const newValue = before + insertText + (after && !after.match(/^\s/) ? ' ' : '') + after
    
    setMathFormula(newValue)
    
    // Restore cursor position after insertion
    setTimeout(() => {
      const newCursorPos = start + insertText.length
      textarea.setSelectionRange(newCursorPos, newCursorPos)
      textarea.focus()
    }, 0)
  }

  // Save & Apply Rule (single or batch)
  const handleSaveRule = async () => {
    // Phase 5.7: Validation for Math Formula mode
    if (editorMode === 'standard' && standardRuleType === 'math') {
      if (!mathFormula.trim()) {
        setError('Please enter a math formula.')
        return
      }
      // For math rules, we don't need rulePreview.sql_where
    } else {
      // For filter rules, require sql_where
      if (!selectedUseCaseId || !rulePreview?.sql_where) {
        setError('No rule to save. Please generate a rule first.')
        return
      }
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
        if (editorMode === 'ai' && rulePreview && rulePreview.logic_en) {
          await axios.post(
            `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules/bulk`,
            {
              node_ids: nodeIds,
              logic_en: rulePreview.logic_en,
              last_modified_by: 'user123', // TODO: Get from auth context
            }
          )
        } else if (editorMode === 'standard' && standardRuleType === 'math' && mathFormula.trim()) {
          // Phase 5.7: Math Formula Mode (Batch)
          const dependencies = extractDependencies(mathFormula)
          await axios.post(
            `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules/bulk`,
            {
              node_ids: nodeIds,
              rule_type: 'NODE_ARITHMETIC',
              rule_expression: mathFormula.trim(),
              rule_dependencies: dependencies,
              sql_where: '', // Empty string to satisfy backend validation (not used for math rules)
              last_modified_by: 'user123', // TODO: Get from auth context
            }
          )
        } else if (editorMode === 'standard' && standardRuleType === 'filter' && conditions.length > 0) {
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
              measure_name: selectedMeasure, // Phase 5: Include target metric
              last_modified_by: 'user123', // TODO: Get from auth context
            }
          )
        }
        
        setCalculationResult(`Rule saved successfully to ${nodeIds.length} node(s)!`)
      } else {
        // Single node save (existing logic)
        if (editorMode === 'ai' && rulePreview && rulePreview.logic_en) {
          await axios.post(
            `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules`,
            {
              node_id: nodeIds[0],
              logic_en: rulePreview.logic_en,
              last_modified_by: 'user123', // TODO: Get from auth context
            }
          )
        } else if (editorMode === 'standard' && standardRuleType === 'math' && mathFormula.trim()) {
          // Phase 5.7: Math Formula Mode (Single)
          const dependencies = extractDependencies(mathFormula)
          await axios.post(
            `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules`,
            {
              node_id: nodeIds[0],
              rule_type: 'NODE_ARITHMETIC',
              rule_expression: mathFormula.trim(),
              rule_dependencies: dependencies,
              sql_where: '', // Empty string to satisfy backend validation (not used for math rules)
              last_modified_by: 'user123', // TODO: Get from auth context
            }
          )
        } else if (editorMode === 'standard' && standardRuleType === 'filter' && conditions.length > 0) {
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
              measure_name: selectedMeasure, // Phase 5: Include target metric
              last_modified_by: 'user123', // TODO: Get from auth context
            }
          )
        }
        
        setCalculationResult('Rule saved successfully!')
      }

      // Refresh rules and hierarchy to update icons
      if (selectedUseCaseId) {
        await loadRules(selectedUseCaseId)
        if (selectedUseCase && selectedUseCaseId) {
          await loadHierarchyForUseCase(selectedUseCaseId, selectedUseCase.atlas_structure_id)
        }
      }

      // Refresh impact preview (only for filter/AI rules, not math rules)
      if (rulePreview && rulePreview.sql_where && 
          (editorMode === 'ai' || (editorMode === 'standard' && standardRuleType === 'filter'))) {
        await fetchRulePreview(rulePreview.sql_where)
      }

      // Success - clear form, close modal, and show message
      setRulePreview(null)
      setAiPrompt('')
      setMathFormula('') // Phase 5.7: Clear math formula
      setConditions([{ field: '', operator: 'equals', value: '' }])
      setModalOpen(false)
      setCalculationResult('Rule saved successfully!')
      setTimeout(() => setCalculationResult(null), 3000)
    } catch (err: any) {
      console.error('Failed to save rule:', err)
      
      // Phase 5.7: Extract error message as string (not object)
      let errorMessage = 'Failed to save rule. Please try again.'
      
      if (err.response?.data) {
        // Handle different error response formats
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail
        } else if (typeof err.response.data.detail === 'object') {
          // If detail is an object, try to extract a meaningful message
          if (err.response.data.detail.message) {
            errorMessage = err.response.data.detail.message
          } else if (Array.isArray(err.response.data.detail)) {
            // Pydantic validation errors are often arrays
            errorMessage = err.response.data.detail.map((e: any) => 
              typeof e === 'string' ? e : e.msg || JSON.stringify(e)
            ).join(', ')
          } else {
            // Fallback: stringify the object
            errorMessage = JSON.stringify(err.response.data.detail)
          }
        } else if (typeof err.response.data.message === 'string') {
          errorMessage = err.response.data.message
        } else if (typeof err.response.data === 'string') {
          errorMessage = err.response.data
        }
      } else if (err.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
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
      if (selectedUseCase && selectedUseCaseId) {
        await loadHierarchyForUseCase(selectedUseCaseId, selectedUseCase.atlas_structure_id)
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

  // Pre-Flight Execution Plan Modal (Rule Sequence Review)
  const [preFlightModalOpen, setPreFlightModalOpen] = useState<boolean>(false)
  const [executionPlan, setExecutionPlan] = useState<any>(null)
  const [ruleSequence, setRuleSequence] = useState<any[]>([])
  const [acknowledged, setAcknowledged] = useState<boolean>(false)

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
      // Graceful error handling: Don't block the UI, just log and set empty plan
      console.warn('Failed to load execution plan (non-fatal):', err)
      console.warn('Error details:', err.response?.data || err.message)
      
      // Set empty plan instead of showing error toast
      setExecutionPlan({
        use_case_id: selectedUseCaseId,
        total_rules: 0,
        leaf_rules: 0,
        parent_rules: 0,
        steps: [{
          step: 1,
          description: "Unable to load execution plan. You can still proceed with calculation."
        }],
        business_summary: null
      })
      setRuleSequence([])
      setAcknowledged(false)
      setPreFlightModalOpen(true)
    }
  }

  // Handle Execute Business Rules (with Pre-Flight)
  const handleExecuteBusinessRules = async () => {
    if (!selectedUseCaseId) {
      setError('Please select a use case first.')
      return
    }

    // Show Pre-Flight modal first
    await loadExecutionPlan()
  }

  // Confirm and Run Calculation (from Pre-Flight modal)
  const handleConfirmAndRun = async () => {
    if (!acknowledged) {
      alert('Please acknowledge that you have reviewed the execution sequence.')
      return
    }
    
    setPreFlightModalOpen(false)
    setCalculating(true)
    setError(null) // Clear error when new calculation starts
    setErrorDetails(null) // Clear error details
    setCalculationResult(null)

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/calculate`
      )

      const message = response.data.message || 
        `Calculation complete. ${response.data.rules_applied} rules applied. Total Plug: $${response.data.total_plug?.daily || '0.00'}`
      
      setCalculationResult(message)
      
      // Show success alert/confirmation with detailed information
      const rulesCount = response.data.rules_applied || 0
      const totalPlug = response.data.total_plug?.daily || 0
      const formattedPlug = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(totalPlug)
      
      // Get use case name
      const useCaseName = selectedUseCase?.name || 'Unknown Use Case'
      
      // Get PNL date from response or current date
      const pnlDate = response.data.pnl_date || response.data.run_timestamp || new Date().toISOString().split('T')[0]
      const formattedDate = new Date(pnlDate).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
      
      // Get run timestamp
      const runTimestamp = response.data.run_timestamp || new Date().toISOString()
      const formattedTimestamp = new Date(runTimestamp).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
      
      // Show custom success modal instead of browser alert
      setSuccessModalData({
        useCaseName,
        pnlDate: formattedDate,
        rulesCount,
        totalPlug: formattedPlug,
        calculationTime: formattedTimestamp
      })
      setSuccessModalOpen(true)
      
      // Update last calculated timestamp
      if (response.data.run_timestamp) {
        setLastCalculated(response.data.run_timestamp)
        setIsCalculationOutdated(false)
      }
      
      // Reload rules after calculation to refresh icons
      if (selectedUseCaseId) {
        loadRules(selectedUseCaseId)
      }
      
      // Reload hierarchy to show calculated P&L values
      if (selectedUseCase && selectedUseCaseId) {
        await loadHierarchyForUseCase(selectedUseCaseId, selectedUseCase.atlas_structure_id)
      }
      
      // NOTE: Page reload is now handled by the modal's "Close & Refresh" button
      // This allows users to see the success modal before the page reloads
      console.log('Run Waterfall completed successfully. Success modal should be visible.')
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
    handleExecuteBusinessRules()
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
          {/* Execute Business Rules button - consolidated to global header */}
          <button
            className="execute-business-rules-btn-primary"
            onClick={handleExecuteBusinessRules}
            disabled={calculating || !selectedUseCaseId}
            style={{ 
              background: calculating 
                ? 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)' 
                : 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '6px',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: calculating || !selectedUseCaseId ? 'not-allowed' : 'pointer',
              opacity: calculating || !selectedUseCaseId ? 0.6 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              transition: 'all 0.2s ease'
            }}
            title={calculating ? 'Processing calculation...' : !selectedUseCaseId ? 'Please select a use case first' : 'Execute business rules and run waterfall calculation'}
          >
            {calculating ? (
              <>
                <span className="spinner" style={{ 
                  display: 'inline-block',
                  width: '16px',
                  height: '16px',
                  border: '2px solid rgba(255, 255, 255, 0.3)',
                  borderTopColor: 'white',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite'
                }}></span>
                Processing...
              </>
            ) : (
              <>
                <span style={{ fontSize: '1.1em' }}>⚡</span>
                Execute Business Rules
              </>
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
        <div className="message error-message" style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 16px',
          backgroundColor: '#fee2e2',
          border: '1px solid #fecaca',
          borderRadius: '6px',
          color: '#991b1b'
        }}>
          <div>
            <strong>Error:</strong> {error}
            {errorDetails?.statusCode && (
              <span style={{ marginLeft: '8px', fontSize: '0.875rem', color: '#7f1d1d' }}>
                (Status: {errorDetails.statusCode})
              </span>
            )}
          </div>
          {errorDetails?.canRetry && selectedUseCase && (
            <button
              onClick={() => {
                setError(null)
                setErrorDetails(null)
                if (selectedUseCase && selectedUseCaseId) {
                  loadHierarchyForUseCase(selectedUseCaseId, selectedUseCase.atlas_structure_id)
                }
              }}
              style={{
                padding: '6px 12px',
                backgroundColor: '#dc2626',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500'
              }}
            >
              Reconnect
            </button>
          )}
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
        </div>
      </div>

      {/* Unified AG-Grid Tree (Clean Look - Matches Tab 2) */}
      <div className="grid-hero-container" style={{ width: '100%' }}>
        <div className="ag-theme-alpine grid-hero rule-editor-grid" style={{ 
          height: '600px', // Fixed height like Tab 2 (cleaner than calc)
          width: '100%',
          overflow: 'hidden' // Prevent whitespace gaps when scrolling
        }}>
          <AgGridReact
            ref={gridRef}
            rowData={searchQuery ? filteredRowData : rowData}
            columnDefs={columnDefs}
            defaultColDef={defaultColDef}
            onGridReady={onGridReady}
            onSelectionChanged={onSelectionChanged}
            rowSelection="multiple"
            getRowId={(params) => params.data.node_id || params.data.id || params.data.node_name || `row-${params.rowIndex}`}
            animateRows={true}
            loading={loading}
            getRowStyle={getRowStyle}
            getRowClass={getRowClass}
            suppressRowClickSelection={false}
            enableRangeSelection={false}
            suppressHorizontalScroll={false}
            suppressVerticalScroll={false}
            // Manual Tree Engine: External filter for parent-child visibility
            isExternalFilterPresent={isExternalFilterPresent}
            doesExternalFilterPass={doesExternalFilterPass}
            // Clean Look: Compact row and header heights (matches Tab 2)
            rowHeight={32}
            headerHeight={32}
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
                      const newMode = e.target.checked ? 'ai' : 'standard'
                      
                      // Phase 5.9: Preserve rule data when switching modes
                      const currentNode = selectedNodes[0]
                      if (currentNode?.hasRule && currentNode?.rule) {
                        const rule = currentNode.rule
                        
                        if (newMode === 'standard' && rule.predicate_json) {
                          // Switching to Standard Mode - load conditions
                          setStandardRuleType('filter')
                          setSelectedMeasure(rule.measure_name || 'daily_pnl')
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
                          // Preserve preview
                          if (rule.sql_where) {
                            setRulePreview({
                              logic_en: rule.logic_en,
                              sql_where: rule.sql_where,
                              predicate_json: rule.predicate_json,
                              translation_successful: true
                            })
                          }
                        } else if (newMode === 'ai' && rule.logic_en) {
                          // Switching to AI Mode - load prompt
                          setAiPrompt(rule.logic_en)
                          // Preserve preview
                          if (rule.sql_where) {
                            setRulePreview({
                              logic_en: rule.logic_en,
                              sql_where: rule.sql_where,
                              predicate_json: rule.predicate_json,
                              translation_successful: true
                            })
                          }
                        } else {
                          // No matching rule data - clear preview
                          setRulePreview(null)
                        }
                      } else {
                        // No existing rule - clear preview
                        setRulePreview(null)
                      }
                      
                      setEditorMode(newMode)
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
                      {availableFieldsForHelper.map((field) => {
                        const samples = sampleValues.get(field.field) || []
                        const isLoading = loadingSamples.has(field.field)
                        const showSamples = ['book_id', 'strategy_id', 'account_id', 'cc_id'].includes(field.field)
                        
                        return (
                          <div key={field.field} className="field-tag-wrapper" style={{ position: 'relative' }}>
                            <span
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
                              onMouseEnter={() => {
                                if (showSamples && samples.length === 0 && !isLoading) {
                                  loadSampleValues(field.field)
                                }
                              }}
                              title={`${field.label} (${field.type}) - Click to insert`}
                            >
                              {field.label}
                            </span>
                            {showSamples && samples.length > 0 && (
                              <div className="field-samples-tooltip">
                                <div className="field-samples-header">Sample Values:</div>
                                <div className="field-samples-list">
                                  {samples.map((val, idx) => (
                                    <span key={idx} className="field-sample-value">{val}</span>
                                  ))}
                                </div>
                              </div>
                            )}
                            {isLoading && (
                              <div className="field-samples-tooltip">
                                <div className="field-samples-loading">Loading samples...</div>
                              </div>
                            )}
                          </div>
                        )
                      })}
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
                  {/* Phase 5.7: Rule Type Selector */}
                  <label htmlFor="rule-type-selector">Rule Type</label>
                  <select
                    id="rule-type-selector"
                    className="rule-type-selector"
                    value={standardRuleType}
                    onChange={(e) => {
                      setStandardRuleType(e.target.value as 'filter' | 'math')
                      // Clear preview when switching rule types
                      setRulePreview(null)
                      setMathFormula('')
                      setConditions([{ field: '', operator: 'equals', value: '' }])
                      // Reset target metric to default when switching to filter mode
                      if (e.target.value === 'filter') {
                        setSelectedMeasure('daily_pnl')
                      }
                    }}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      marginBottom: '1rem',
                      border: '1px solid #d1d5db',
                      borderRadius: '4px',
                      fontSize: '0.875rem'
                    }}
                  >
                    <option value="filter">Data Filter (SQL)</option>
                    <option value="math">Math Formula</option>
                  </select>

                  {/* Math Formula Mode */}
                  {standardRuleType === 'math' && (
                    <div style={{ marginBottom: '1rem' }}>
                      {/* Phase 5.7: Node Reference Dropdown */}
                      <label htmlFor="node-reference-select">Insert Reference to Node:</label>
                      <select
                        id="node-reference-select"
                        value=""
                        onChange={(e) => {
                          const selectedNodeId = e.target.value
                          if (selectedNodeId) {
                            insertNodeReference(selectedNodeId)
                            e.target.value = '' // Reset dropdown
                          }
                        }}
                        style={{
                          width: '100%',
                          padding: '0.5rem',
                          marginBottom: '0.75rem',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          fontSize: '0.875rem',
                          backgroundColor: 'white'
                        }}
                      >
                        <option value="">-- Select a node to insert --</option>
                        {rowData
                          .filter((node: any) => node.node_id && node.node_name)
                          .sort((a: any, b: any) => {
                            // Sort by node_name for better UX
                            const nameA = (a.node_name || a.node_id || '').toLowerCase()
                            const nameB = (b.node_name || b.node_id || '').toLowerCase()
                            return nameA.localeCompare(nameB)
                          })
                          .map((node: any) => (
                            <option key={node.node_id} value={node.node_id}>
                              {node.node_name || node.node_id} ({node.node_id})
                            </option>
                          ))}
                      </select>
                      
                      <label htmlFor="math-formula">Enter Formula</label>
                      <textarea
                        ref={mathFormulaRef}
                        id="math-formula"
                        className="math-formula-input"
                        value={mathFormula}
                        onChange={(e) => setMathFormula(e.target.value)}
                        placeholder="e.g., NODE_A * 0.10 + NODE_B"
                        rows={4}
                        style={{
                          width: '100%',
                          padding: '0.5rem',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          fontSize: '0.875rem',
                          fontFamily: 'monospace',
                          resize: 'vertical'
                        }}
                      />
                      <div style={{ 
                        marginTop: '0.5rem', 
                        fontSize: '0.75rem', 
                        color: '#6b7280',
                        fontStyle: 'italic'
                      }}>
                        Supported operators: +, -, *, /, parentheses. Use NODE_X to reference other nodes.
                      </div>
                      {mathFormula && (
                        <div style={{ 
                          marginTop: '0.5rem', 
                          fontSize: '0.75rem', 
                          color: '#059669'
                        }}>
                          Dependencies: {extractDependencies(mathFormula).join(', ') || 'None'}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Data Filter Mode */}
                  {standardRuleType === 'filter' && (
                    <>
                      {/* Phase 5: Target Metric Dropdown */}
                      <label htmlFor="target-metric-selector">Target Metric</label>
                      <select
                        id="target-metric-selector"
                        value={selectedMeasure}
                        onChange={(e) => setSelectedMeasure(e.target.value)}
                        style={{
                          width: '100%',
                          padding: '0.5rem',
                          marginBottom: '1rem',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          fontSize: '0.875rem'
                        }}
                      >
                        <option value="daily_pnl">Daily P&L</option>
                        <option value="pnl_commission">Commission P&L</option>
                        <option value="pnl_trade">Trade P&L</option>
                        <option value="ytd_pnl">YTD P&L</option>
                      </select>
                      
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
                      <div style={{ position: 'relative', width: '100%' }}>
                        <input
                          type="text"
                          className="condition-value"
                          value={typeof condition.value === 'string' ? condition.value : condition.value.join(', ')}
                          onChange={(e) => {
                            const value = (condition.operator === 'in' || condition.operator === 'not_in')
                              ? e.target.value
                              : e.target.value
                            handleConditionChange(index, 'value', value)
                            setAutocompleteOpen(prev => new Map(prev).set(index, true))
                          }}
                          onFocus={() => {
                            if (condition.field) {
                              loadSampleValues(condition.field)
                              setAutocompleteOpen(prev => new Map(prev).set(index, true))
                            }
                          }}
                          onBlur={() => {
                            // Delay closing to allow click on suggestion
                            setTimeout(() => {
                              setAutocompleteOpen(prev => {
                                const next = new Map(prev)
                                next.set(index, false)
                                return next
                              })
                            }, 200)
                          }}
                          placeholder={
                            condition.operator === 'in' || condition.operator === 'not_in'
                              ? 'Comma-separated values (e.g., B01, B02)'
                              : 'Enter value or select from suggestions'
                          }
                        />
                        {/* Autocomplete Dropdown */}
                        {autocompleteOpen.get(index) && condition.field && sampleValues.has(condition.field) && (
                          <div 
                            className="autocomplete-dropdown"
                            style={{
                              position: 'absolute',
                              top: '100%',
                              left: 0,
                              right: 0,
                              background: 'white',
                              border: '1px solid #d1d5db',
                              borderRadius: '4px',
                              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                              maxHeight: '200px',
                              overflowY: 'auto',
                              zIndex: 1000,
                              marginTop: '4px'
                            }}
                          >
                            {sampleValues.get(condition.field)!
                              .filter(val => {
                                const filter = autocompleteFilter.get(index) || ''
                                return !filter || val.toLowerCase().includes(filter.toLowerCase())
                              })
                              .map((val, valIdx) => (
                                <div
                                  key={valIdx}
                                  onClick={() => {
                                    handleConditionChange(index, 'value', val)
                                    setAutocompleteOpen(prev => {
                                      const next = new Map(prev)
                                      next.set(index, false)
                                      return next
                                    })
                                  }}
                                  style={{
                                    padding: '0.5rem',
                                    cursor: 'pointer',
                                    borderBottom: '1px solid #f3f4f6'
                                  }}
                                  onMouseEnter={(e) => {
                                    e.currentTarget.style.background = '#f3f4f6'
                                  }}
                                  onMouseLeave={(e) => {
                                    e.currentTarget.style.background = 'white'
                                  }}
                                >
                                  {val}
                                </div>
                              ))}
                          </div>
                        )}
                      </div>
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
                    </>
                  )}
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
                </div>
              )}

              {/* Phase 5.7: Math Formula Preview (when no rulePreview exists) */}
              {editorMode === 'standard' && standardRuleType === 'math' && mathFormula.trim() && !rulePreview && (
                <div className="rule-preview-card" style={{
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  padding: '1rem',
                  backgroundColor: '#f9fafb',
                  marginTop: '1rem'
                }}>
                  <h4 style={{ marginTop: 0, marginBottom: '0.75rem' }}>Math Formula Preview</h4>
                  <div className="preview-section">
                    <strong>Formula:</strong>
                    <code style={{
                      display: 'block',
                      padding: '0.5rem',
                      marginTop: '0.5rem',
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '4px',
                      fontFamily: 'monospace',
                      fontSize: '0.875rem'
                    }}>
                      {mathFormula}
                    </code>
                  </div>
                  {extractDependencies(mathFormula).length > 0 && (
                    <div className="preview-section" style={{ marginTop: '0.75rem' }}>
                      <strong>Dependencies:</strong>
                      <p style={{ marginTop: '0.25rem', color: '#059669', fontSize: '0.875rem' }}>
                        {extractDependencies(mathFormula).join(', ')}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Phase 5.7: Action Buttons - Always Visible */}
              <div className="modal-footer-actions" style={{
                display: 'flex',
                justifyContent: 'flex-end',
                gap: '0.75rem',
                marginTop: '1.5rem',
                paddingTop: '1rem',
                borderTop: '1px solid #e5e7eb'
              }}>
                <button
                  className="cancel-button"
                  onClick={() => {
                    setModalOpen(false)
                    setRulePreview(null)
                    setMathFormula('')
                    setConditions([{ field: '', operator: 'equals', value: '' }])
                    setError(null)
                  }}
                  style={{
                    padding: '0.5rem 1rem',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    backgroundColor: 'white',
                    color: '#374151',
                    cursor: 'pointer',
                    fontSize: '0.875rem'
                  }}
                >
                  Cancel
                </button>
                <button
                  className="save-button"
                  onClick={handleSaveRule}
                  disabled={
                    loading || 
                    (editorMode === 'standard' && standardRuleType === 'math' && !mathFormula.trim()) ||
                    (editorMode === 'standard' && standardRuleType === 'filter' && (!rulePreview?.translation_successful || !rulePreview?.sql_where)) ||
                    (editorMode === 'ai' && (!rulePreview?.translation_successful || !rulePreview?.sql_where))
                  }
                  style={{
                    padding: '0.5rem 1.5rem',
                    border: 'none',
                    borderRadius: '4px',
                    backgroundColor: loading || 
                      (editorMode === 'standard' && standardRuleType === 'math' && !mathFormula.trim()) ||
                      (editorMode === 'standard' && standardRuleType === 'filter' && (!rulePreview?.translation_successful || !rulePreview?.sql_where)) ||
                      (editorMode === 'ai' && (!rulePreview?.translation_successful || !rulePreview?.sql_where))
                      ? '#9ca3af' : '#0ea5e9',
                    color: 'white',
                    cursor: loading || 
                      (editorMode === 'standard' && standardRuleType === 'math' && !mathFormula.trim()) ||
                      (editorMode === 'standard' && standardRuleType === 'filter' && (!rulePreview?.translation_successful || !rulePreview?.sql_where)) ||
                      (editorMode === 'ai' && (!rulePreview?.translation_successful || !rulePreview?.sql_where))
                      ? 'not-allowed' : 'pointer',
                    fontSize: '0.875rem',
                    fontWeight: '600'
                  }}
                >
                  {loading ? 'Saving...' : 'Save & Apply'}
                </button>
              </div>
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
                          ['Node Name', 'Rule Type', 'Rule Logic/Formula', 'Created By', 'Impact', 'Affected Rows', 'Total Rows', 'Percentage', 'Dependencies'].join(','),
                          ...rulesArray.map((rule: any) => {
                            const isMath = isMathRule(rule)
                            const ruleType = isMath ? 'Math Formula' : (rule.rule_type || 'Filter')
                            const ruleContent = isMath 
                              ? (rule.rule_expression || '')
                              : (rule.logic_en || rule.sql_where || '')
                            
                            return [
                              rule.node_name || rule.node_id,
                              ruleType,
                              `"${ruleContent.replace(/"/g, '""')}"`,
                              rule.last_modified_by || 'Unknown',
                              rule.estimatedImpact || 0,
                              rule.affected_rows || 0,
                              rule.total_rows || 0,
                              rule.percentage || 0,
                              isMath && rule.rule_dependencies ? rule.rule_dependencies.join('; ') : ''
                            ].join(',')
                          })
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
                  Array.from(rules.values()).map((rule: any) => {
                    // Phase 5.7: Determine rule type and display accordingly
                    const isMath = isMathRule(rule)
                    
                    // For math rules, use rule_expression; for others, use logic_en or sql_where
                    // Format Math rule formulas: Replace node IDs with readable names
                    const rawExpression = isMath 
                      ? (rule.rule_expression || 'No formula defined')
                      : (rule.logic_en || rule.sql_where || 'No rule logic defined')
                    
                    const ruleDescription = isMath && rawExpression !== 'No formula defined'
                      ? formatFormula(rawExpression, rowData)
                      : rawExpression
                    const ruleBadge = isMath ? 'Math' : 'fx'
                    const badgeClass = isMath ? 'rule-badge-math' : 'rule-badge-small'
                    
                    // Phase 5: Get measure label for filter rules (Multi-Measure support)
                    const measureLabel = rule.measure_name && MEASURE_LABELS[rule.measure_name] 
                      ? MEASURE_LABELS[rule.measure_name] 
                      : null
                    
                    return (
                      <div key={rule.rule_id} className="library-rule-card">
                        <div className="library-rule-header">
                          <strong>{rule.node_name || rule.node_id}</strong>
                          <span className={badgeClass} style={isMath ? {
                            background: '#dbeafe',
                            color: '#1e40af',
                            padding: '0.125rem 0.5rem',
                            borderRadius: '3px',
                            fontSize: '0.7rem',
                            fontWeight: '600'
                          } : {}}>
                            {ruleBadge}
                          </span>
                        </div>
                        <div className="library-rule-body">
                          {/* Phase 5: Display measure name for filter rules */}
                          {!isMath && measureLabel && (
                            <div style={{
                              fontSize: '0.75rem',
                              color: '#059669',
                              fontWeight: '600',
                              marginBottom: '0.25rem',
                              textTransform: 'uppercase',
                              letterSpacing: '0.5px'
                            }}>
                              Target: {measureLabel}
                            </div>
                          )}
                          <p className="rule-logic" style={isMath ? {
                            fontFamily: 'monospace',
                            backgroundColor: '#f3f4f6',
                            padding: '0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.85rem'
                          } : {}}>
                            {isMath ? 'Formula: ' : ''}{ruleDescription}
                          </p>
                          <div className="library-rule-meta">
                            <span>By: {rule.last_modified_by || 'Unknown'}</span>
                            {!isMath && (
                              <span className={`impact-badge ${rule.estimatedImpact < 0 ? 'negative' : 'positive'}`}>
                                {rule.estimatedImpact < 0 ? '-' : '+'}${Math.abs(rule.estimatedImpact).toLocaleString()}k
                              </span>
                            )}
                            {isMath && rule.rule_dependencies && rule.rule_dependencies.length > 0 && (
                              <span style={{
                                fontSize: '0.75rem',
                                color: '#059669',
                                fontStyle: 'italic'
                              }}>
                                Depends on: {rule.rule_dependencies.join(', ')}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })
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
                {auditRules.map((rule, index) => {
                  // Phase 5.7: Handle Math Rules in audit drawer
                  const isMath = isMathRule(rule)
                  const rawExpression = isMath 
                    ? (rule.rule_expression || 'No formula defined')
                    : (rule.logic_en || rule.sql_where || 'No rule logic defined')
                  
                  // Format Math rule formulas: Replace node IDs with readable names
                  const ruleDescription = isMath && rawExpression !== 'No formula defined'
                    ? formatFormula(rawExpression, rowData)
                    : rawExpression
                  
                  return (
                    <div key={rule.rule_id || index} className="audit-rule-item">
                      <div className="audit-rule-header">
                        <strong>{rule.node_name || rule.node_id}</strong>
                        <span className="audit-rule-badge">
                          {isMath ? 'Math Rule' : `Rule #${rule.rule_id}`}
                        </span>
                      </div>
                      <div className="audit-rule-details">
                        <div className="audit-rule-logic">
                          <strong>{isMath ? 'Formula:' : 'Logic:'}</strong>{' '}
                          <span style={isMath ? {
                            fontFamily: 'monospace',
                            backgroundColor: '#f3f4f6',
                            padding: '0.25rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.85rem'
                          } : {}}>
                            {ruleDescription}
                          </span>
                        </div>
                        {!isMath && (
                          <div className="audit-rule-impact">
                            <strong>Impact:</strong> {rule.affected_rows?.toLocaleString() || 0} of {rule.total_rows?.toLocaleString() || 0} rows ({rule.percentage?.toFixed(2) || 0}%)
                          </div>
                        )}
                        {isMath && rule.rule_dependencies && rule.rule_dependencies.length > 0 && (
                          <div className="audit-rule-impact" style={{ color: '#059669', fontSize: '0.875rem' }}>
                            <strong>Dependencies:</strong> {rule.rule_dependencies.join(', ')}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
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

      {/* Success Modal */}
      {successModalOpen && successModalData && (
        <div className="rule-editor-modal-overlay" onClick={() => setSuccessModalOpen(false)}>
          <div className="rule-editor-modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className="rule-editor-modal-header" style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', color: 'white' }}>
              <h3 style={{ color: 'white', margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '1.5rem' }}>✅</span>
                Business Rules Applied Successfully!
              </h3>
              <button
                className="modal-close-btn"
                onClick={() => setSuccessModalOpen(false)}
                style={{ color: 'white' }}
              >
                ×
              </button>
            </div>
            <div className="rule-editor-modal-body" style={{ padding: '2rem' }}>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'auto 1fr', 
                gap: '1rem 1.5rem',
                marginBottom: '1.5rem'
              }}>
                <div style={{ fontWeight: '600', color: '#374151' }}>Use Case:</div>
                <div style={{ color: '#1f2937' }}>{successModalData.useCaseName}</div>
                
                <div style={{ fontWeight: '600', color: '#374151' }}>P&L Date:</div>
                <div style={{ color: '#1f2937' }}>{successModalData.pnlDate}</div>
                
                <div style={{ fontWeight: '600', color: '#374151' }}>Rules Applied:</div>
                <div style={{ color: '#1f2937' }}>{successModalData.rulesCount}</div>
                
                <div style={{ fontWeight: '600', color: '#374151' }}>Total Reconciliation Plug:</div>
                <div style={{ 
                  color: parseFloat(successModalData.totalPlug.replace(/[^0-9.-]/g, '')) >= 0 ? '#059669' : '#dc2626',
                  fontWeight: '600',
                  fontSize: '1.1rem'
                }}>
                  {successModalData.totalPlug}
                </div>
                
                <div style={{ fontWeight: '600', color: '#374151' }}>Calculation Time:</div>
                <div style={{ color: '#6b7280', fontSize: '0.9rem' }}>{successModalData.calculationTime}</div>
              </div>
              
              <div style={{
                padding: '1rem',
                backgroundColor: '#f0fdf4',
                border: '1px solid #86efac',
                borderRadius: '6px',
                color: '#166534',
                fontSize: '0.95rem',
                marginTop: '1rem'
              }}>
                The calculation has been completed and the results are now visible in the hierarchy.
              </div>
              
              <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  onClick={() => {
                    setSuccessModalOpen(false)
                    // Reload page after a short delay to show updated results
                    setTimeout(() => {
                      window.location.reload()
                    }, 500)
                  }}
                  style={{
                    padding: '0.75rem 2rem',
                    backgroundColor: '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '1rem',
                    fontWeight: '600',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                    boxShadow: '0 2px 4px rgba(16, 185, 129, 0.3)'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#059669'}
                  onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#10b981'}
                >
                  Close & Refresh
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Optimize tab switching: Use React.memo to prevent unnecessary re-renders
export default React.memo(RuleEditor)

