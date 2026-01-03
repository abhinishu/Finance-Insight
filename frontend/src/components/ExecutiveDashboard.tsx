import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridApi, ColumnApi, ICellRendererParams } from 'ag-grid-community'
import axios from 'axios'
import { useReportingContext } from '../contexts/ReportingContext'
import { calculateRuleAttribution } from '../utils/pnlAttribution'
import RuleImpactTable from './RuleImpactTable'
import PnlWaterfallChart from './PnlWaterfallChart'
import DrillDownModal from './DrillDownModal'
import RuleDrillDownModal from './RuleDrillDownModal'
import PortalTooltip from './PortalTooltip'
import SmartTooltip from './SmartTooltip'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import './ExecutiveDashboard.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Phase 5.9: Measure Labels Map for Multi-Measure Rules (matching Tab 3)
const MEASURE_LABELS: Record<string, string> = {
  'daily_pnl': 'Daily P&L',
  'pnl_commission': 'Commission P&L',
  'pnl_trade': 'Trading P&L',
  'daily_commission': 'Commission P&L',
  'daily_trade': 'Trading P&L',
  'ytd_pnl': 'YTD P&L'
}

// ============================================================================
// HELPER FUNCTIONS: Defensive Data Processing
// ============================================================================

/**
 * HELPER 1: Recursively flatten tree AND remove duplicates
 * Safely handles nested children arrays and null/undefined values
 * Uses a Set to track seen IDs and prevent duplicate rows in AG Grid
 */
const flattenTree = (nodes: any[], seenIds = new Set<string>()): any[] => {
  let flat: any[] = []
  if (!nodes || !Array.isArray(nodes)) return flat
  
  nodes.forEach(node => {
    if (!node) return // Skip null/undefined nodes
    
    // Ensure we have a valid ID. Fallback to name or random string if missing.
    const uniqueId = node.node_id || node.id || node.node_name || Math.random().toString(36)
    
    // DEDUPLICATION: Only add if we haven't seen this ID before
    if (!seenIds.has(uniqueId)) {
      seenIds.add(uniqueId)
      flat.push(node)
      
      // Process children recursively, passing the 'seenIds' Set along
      if (node.children && Array.isArray(node.children) && node.children.length > 0) {
        flat = flat.concat(flattenTree(node.children, seenIds))
      }
    }
  })
  
  return flat
}

/**
 * HELPER 2: Robustly parse numerical amounts from any format (String, Number, Object)
 * Handles V1 API (strings), V2 API (objects), and edge cases
 */
const parseAmount = (val: any): number => {
  if (val === null || val === undefined) return 0
  
  if (typeof val === 'number') {
    return isNaN(val) ? 0 : val
  }
  
  // Remove currency symbols/commas if string
  if (typeof val === 'string') {
    const cleaned = val.replace(/[^0-9.-]+/g, '')
    const parsed = parseFloat(cleaned)
    return isNaN(parsed) ? 0 : parsed
  }
  
  // Handle V2 API Objects { daily: "...", mtd: "..." }
  if (typeof val === 'object') {
    const raw = val.daily || val.amount || val.value || 0
    if (typeof raw === 'string') {
      const cleaned = raw.replace(/[^0-9.-]+/g, '')
      const parsed = parseFloat(cleaned)
      return isNaN(parsed) ? 0 : parsed
    }
    return typeof raw === 'number' ? (isNaN(raw) ? 0 : raw) : 0
  }
  
  return 0
}

// ============================================================================
// INTERFACES
// ============================================================================

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
    // Phase 5.9: Math Rule fields
    rule_type?: string | null
    rule_expression?: string | null
    rule_dependencies?: string[] | null
    // Phase 5.9: Measure name for display
    measure_name?: string | null
  } | null
  path?: string[] | null
  children: ResultsNode[]
}

interface UseCaseRun {
  id?: string  // Step 4.2: New calculation_runs format
  run_id?: string  // Legacy use_case_runs format
  pnl_date?: string  // Step 4.2: Date anchor
  run_name?: string  // Step 4.2: New format
  version_tag?: string  // Legacy format
  executed_at?: string  // Step 4.2: New format
  run_timestamp?: string  // Legacy format
  status?: string
  triggered_by?: string
  duration_ms?: number
}

interface ResultsResponse {
  run_id: string
  use_case_id: string
  version_tag: string
  run_timestamp: string
  hierarchy: ResultsNode[]
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

// Business Rule Cell Renderer (using PortalTooltip for rich tooltips)

// Custom Cell Renderer Component for Business Rule
const BusinessRuleCellRenderer: React.FC<ICellRendererParams> = (params) => {
  const rule = params.data?.rule
  
  if (!rule) {
    return <span style={{ color: '#999' }}>—</span>
  }
  
  // Debug: Log rule object for Commissions node to diagnose Math rule detection
  if (params.data?.node_name === 'Commissions') {
    console.log('Tab 4 Debug - Commissions node rule:', JSON.stringify(rule, null, 2))
    console.log('Tab 4 Debug - rule_type:', rule.rule_type)
    console.log('Tab 4 Debug - rule_expression:', rule.rule_expression)
    console.log('Tab 4 Debug - logic_en:', rule.logic_en)
  }
  
  // Phase 5.9: Handle Math Rules (NODE_ARITHMETIC)
  // Case A: Math Rule - check rule_type or rule_expression
  // Check both rule_type and rule_expression (handle cases where one might be missing)
  const isMathRule = rule.rule_type === 'NODE_ARITHMETIC' || 
                     (rule.rule_expression && rule.rule_expression.trim() !== '')
  
  if (isMathRule) {
    const rawFormula = rule.rule_expression || 'No formula defined'
    
    // Get all row data from grid API for formatting
    const allRowData: any[] = []
    if (params.api) {
      params.api.forEachNode((node: any) => {
        if (node.data) {
          allRowData.push(node.data)
        }
      })
    }
    
    // Format formula: Replace node IDs with readable names
    const formattedFormula = formatFormula(rawFormula, allRowData)
    
    // Calculate impact (adjusted - original)
    const original = parseFloat(params.data?.natural_value?.daily || params.data?.daily_pnl || 0)
    const adjusted = parseFloat(params.data?.adjusted_value?.daily || params.data?.adjusted_daily || 0)
    const impact = adjusted - original
    
    const tooltipContent = (
      <div>
        <div style={{ fontWeight: '700', marginBottom: '0.25rem', color: '#1e40af' }}>
          Math Formula
        </div>
        <div style={{ color: '#d1d5db', marginBottom: '0.25rem', fontSize: '0.8rem', fontFamily: 'monospace' }}>
          {formattedFormula}
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
    
    const displayText = formattedFormula.length > 60 ? formattedFormula.substring(0, 57) + '...' : formattedFormula
    
    return (
      <SmartTooltip content={tooltipContent}>
        <span 
          className="rule-badge" 
          style={{ 
            cursor: 'help',
            background: '#dbeafe',
            color: '#1e40af',
            padding: '0.125rem 0.5rem',
            borderRadius: '3px',
            fontSize: '0.75rem',
            fontWeight: '600'
          }}
        >
          {displayText}
        </span>
      </SmartTooltip>
    )
  }
  
  // Case B: Filter Rule (Existing logic)
  if (rule.logic_en) {
    // Phase 5.9: Debug logging for measure_name
    if (params.data?.node_name === 'Commissions (Non Swap)') {
      console.log('Tab 4 Debug - Rule object:', JSON.stringify(rule, null, 2))
      console.log('Tab 4 Debug - measure_name:', rule.measure_name)
      console.log('Tab 4 Debug - MEASURE_LABELS keys:', Object.keys(MEASURE_LABELS))
    }
    
    // Phase 5.9: Get measure label for filter rules (Multi-Measure support)
    const measureLabel = rule.measure_name && MEASURE_LABELS[rule.measure_name] 
      ? MEASURE_LABELS[rule.measure_name] 
      : null
    
    // Debug: Log if measureLabel is null but measure_name exists
    if (rule.measure_name && !measureLabel) {
      console.warn(`Tab 4 - measure_name "${rule.measure_name}" not found in MEASURE_LABELS`)
    }
    
    const baseLogicText = rule.logic_en || 'Business Rule Applied'
    
    // Calculate impact (adjusted - original)
    const original = parseFloat(params.data?.natural_value?.daily || params.data?.daily_pnl || 0)
    const adjusted = parseFloat(params.data?.adjusted_value?.daily || params.data?.adjusted_daily || 0)
    const impact = adjusted - original
    
    const tooltipContent = (
      <div>
        {/* Phase 5.9: Display measure name in tooltip */}
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
          {baseLogicText}
        </div>
        {rule.sql_where && (
          <div style={{ color: '#d1d5db', marginBottom: '0.25rem', fontSize: '0.7rem' }}>
            Logic: {rule.sql_where}
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
    
    // Phase 5.9: Format display text with measure context (matching Tab 3)
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
    
    // Truncate if too long (for string display only)
    const finalDisplayText = typeof displayText === 'string' && displayText.length > 60 
      ? displayText.substring(0, 57) + '...' 
      : displayText
    
    return (
      <SmartTooltip content={tooltipContent}>
        <span 
          className="rule-badge" 
          style={{ cursor: 'help' }}
        >
          {finalDisplayText}
        </span>
      </SmartTooltip>
    )
  }
  
  // No rule found
  return <span style={{ color: '#999' }}>—</span>
}

const ExecutiveDashboard: React.FC = () => {
  // Step 4.3: Use ReportingContext for global state
  const {
    selectedUseCaseId: contextUseCaseId,
    setSelectedUseCaseId: setContextUseCaseId,
    selectedRunId: contextRunId,
    isComparisonMode,
    baselineRunId,
    targetRunId,
  } = useReportingContext()
  
  // Use Case Management
  const [useCases, setUseCases] = useState<UseCase[]>([])
  const [selectedUseCaseId, setSelectedUseCaseId] = useState<string>(contextUseCaseId || '')
  const [selectedUseCase, setSelectedUseCase] = useState<UseCase | null>(null)

  // Run Management (kept for backward compatibility, but will sync with context)
  const [runs, setRuns] = useState<UseCaseRun[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string>('')
  
  // Comparison Data
  const [baselineData, setBaselineData] = useState<any[]>([])
  const [targetData, setTargetData] = useState<any[]>([])

  // Data
  const [rowData, setRowData] = useState<any[]>([])
  const [filteredRowData, setFilteredRowData] = useState<any[]>([])
  const [gridApi, setGridApi] = useState<GridApi | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [calculating, setCalculating] = useState<boolean>(false) // For Run Calculation button
  
  // Manual Tree Engine: Track expanded nodes (matches Tab 2 & 3)
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())

  // Side Drawer
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false)
  const [selectedRule, setSelectedRule] = useState<ResultsNode | null>(null)
  
  // Drill-Down Modal for Waterfall Chart
  const [selectedRuleName, setSelectedRuleName] = useState<string | null>(null)
  
  // Forensic Drill-Down Modal (Rule Evidence Locker)
  const [selectedDrillRule, setSelectedDrillRule] = useState<string | null>(null)
  
  // Scope Node for Dynamic Waterfall Chart
  const [scopeNode, setScopeNode] = useState<any>(null)

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

  // Load runs when use case changes
  useEffect(() => {
    if (selectedUseCaseId) {
      loadRuns(selectedUseCaseId)
      checkCalculationFreshness(selectedUseCaseId)
    }
  }, [selectedUseCaseId])

  // Sync local use case with context
  useEffect(() => {
    if (contextUseCaseId && contextUseCaseId !== selectedUseCaseId) {
      setSelectedUseCaseId(contextUseCaseId)
    }
  }, [contextUseCaseId])
  
  // Update context when local use case changes
  useEffect(() => {
    if (selectedUseCaseId && selectedUseCaseId !== contextUseCaseId) {
      setContextUseCaseId(selectedUseCaseId)
    }
  }, [selectedUseCaseId])
  
  // Load results when run is selected (standard mode)
  useEffect(() => {
    if (selectedUseCaseId && !isComparisonMode) {
      // Use contextRunId if available, otherwise try selectedRunId, otherwise load most recent
      const runIdToUse = contextRunId || selectedRunId || undefined
      // Wrap in try/catch to prevent component crash
      try {
        loadResults(selectedUseCaseId, runIdToUse)
      } catch (err: any) {
        console.error('TAB 4: Error in useEffect loadResults:', err)
        setError('Dashboard data unavailable for this Use Case.')
        setRowData([])
        setLoading(false)
      }
    }
  }, [selectedUseCaseId, contextRunId, selectedRunId, isComparisonMode])
  
  // Load comparison data when both runs are selected
  useEffect(() => {
    if (selectedUseCaseId && isComparisonMode && baselineRunId && targetRunId) {
      loadComparisonResults(selectedUseCaseId, baselineRunId, targetRunId)
    }
  }, [selectedUseCaseId, isComparisonMode, baselineRunId, targetRunId])

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
      // Use the new Step 4.2 runs API endpoint
      const response = await axios.get(`${API_BASE_URL}/api/v1/runs?use_case_id=${useCaseId}`)
      const runsList = response.data.runs || []
      setRuns(runsList)
      
      // Auto-select the most recent run if available and no run is currently selected
      if (runsList.length > 0 && !selectedRunId && !contextRunId) {
        const firstRunId = runsList[0].id || runsList[0].run_id
        setSelectedRunId(firstRunId)
        // Trigger loadResults with the selected run
        setTimeout(() => loadResults(useCaseId, firstRunId), 100)
      } else if (runsList.length === 0) {
        // No runs found - still try to load results (will get most recent or natural values)
        console.log('No runs found, loading results without run_id to get natural values')
        setTimeout(() => loadResults(useCaseId), 100)
      }
    } catch (err: any) {
      console.error('Failed to load runs:', err)
      // Fallback: try to load legacy runs from use_case_runs
      try {
        const useCaseResponse = await axios.get(`${API_BASE_URL}/api/v1/use-cases/${useCaseId}`)
        // If no runs found, still try to load results
        setRuns([])
        console.log('No runs found (fallback), loading results without run_id')
        setTimeout(() => loadResults(useCaseId), 100)
      } catch (fallbackErr: any) {
        console.error('Failed to load use case:', fallbackErr)
        setRuns([])
        // Still try to load results even if runs fail
        setTimeout(() => loadResults(useCaseId), 100)
      }
    }
  }

  const loadResults = async (useCaseId: string, runId?: string) => {
    setLoading(true)
    setError(null)

    try {
      const url = runId
        ? `${API_BASE_URL}/api/v1/use-cases/${useCaseId}/results?run_id=${runId}`
        : `${API_BASE_URL}/api/v1/use-cases/${useCaseId}/results`
      
      console.log('TAB 4: Loading results from:', url)
      const response = await axios.get<ResultsResponse>(url)
      console.log('TAB 4: Results API response:', {
        hasHierarchy: !!response.data.hierarchy,
        hierarchyLength: response.data.hierarchy?.length || 0,
        runId: response.data.run_id,
        versionTag: response.data.version_tag
      })
      
      // Phase 5.9: Debug - Check if measure_name is in the API response
      if (response.data.hierarchy && response.data.hierarchy.length > 0) {
        const sampleNode = response.data.hierarchy[0]
        console.log('TAB 4: Sample node from API:', {
          node_name: sampleNode.node_name,
          hasRule: !!sampleNode.rule,
          rule: sampleNode.rule ? {
            rule_id: sampleNode.rule.rule_id,
            logic_en: sampleNode.rule.logic_en,
            measure_name: sampleNode.rule.measure_name, // Check if this exists
            rule_type: sampleNode.rule.rule_type
          } : null
        })
        
        // Find a node with a rule to debug
        const nodeWithRule = response.data.hierarchy.find((n: any) => n.rule && n.rule.logic_en)
        if (nodeWithRule) {
          console.log('TAB 4: Node with rule found:', {
            node_name: nodeWithRule.node_name,
            rule: JSON.stringify(nodeWithRule.rule, null, 2)
          })
        }
      }
      
      // Store last calculated timestamp
      if (response.data.run_timestamp) {
        setLastCalculated(response.data.run_timestamp)
      }
      
      const hierarchy = response.data.hierarchy || []
      if (hierarchy.length === 0) {
        // Graceful fallback: Don't crash, just show gentle warning
        console.warn('TAB 4: No hierarchy returned from results API. This might indicate an issue with the use case or structure.')
        setError('Dashboard data unavailable for this Use Case.')
        setRowData([])
        setLoading(false)
        return
      }

      // Flatten hierarchy for AG-Grid
      const flatData = flattenHierarchy(hierarchy)
      console.log('TAB 4: Flattened data:', {
        totalRows: flatData.length,
        sampleRow: flatData[0] || null
      })
      setRowData(flatData)
      
      // Initialize expandedNodes: expand first 4 levels by default (matches Tab 2)
      const defaultExpanded = new Set<string>()
      flatData.forEach(row => {
        if (row.depth < 4 && !row.is_leaf) {
          defaultExpanded.add(row.node_id)
        }
      })
      setExpandedNodes(defaultExpanded)
      
      // Set default scopeNode to Root Node on initial load
      if (flatData.length > 0 && !scopeNode) {
        const rootNode = flatData.find((r: any) => 
          r.node_name === 'Global Trading P&L' || 
          r.node_name === 'ROOT' ||
          r.depth === 0 ||
          !r.parent_node_id
        ) || flatData[0]
        setScopeNode(rootNode)
        console.log('[EXECUTIVE DASHBOARD] Default scopeNode set to:', rootNode?.node_name)
      }
      
      // Check if calculation is outdated (compare with rules last modified)
      await checkCalculationFreshness(useCaseId)
    } catch (err: any) {
      // Robust error handling: Do NOT crash the component
      console.error('TAB 4: Failed to load results:', err)
      console.error('TAB 4: Error details:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status
      })
      
      // Graceful fallback: Set empty state and show gentle warning
      setError('Dashboard data unavailable for this Use Case.')
      setRowData([])
    } finally {
      setLoading(false)
    }
  }
  
  // Step 4.3: Load comparison results for baseline and target runs
  const loadComparisonResults = async (useCaseId: string, baselineRunId: string, targetRunId: string) => {
    setLoading(true)
    setError(null)
    
    try {
      // Load both runs in parallel
      const [baselineResponse, targetResponse] = await Promise.all([
        axios.get<ResultsResponse>(`${API_BASE_URL}/api/v1/use-cases/${useCaseId}/results?run_id=${baselineRunId}`),
        axios.get<ResultsResponse>(`${API_BASE_URL}/api/v1/use-cases/${useCaseId}/results?run_id=${targetRunId}`)
      ])
      
      const baselineHierarchy = baselineResponse.data.hierarchy || []
      const targetHierarchy = targetResponse.data.hierarchy || []
      
      if (baselineHierarchy.length === 0 || targetHierarchy.length === 0) {
        setError('One or both runs have no results.')
        setRowData([])
        setLoading(false)
        return
      }
      
      // Flatten and merge with variance calculation
      const baselineFlat = flattenHierarchy(baselineHierarchy)
      const targetFlat = flattenHierarchy(targetHierarchy)
      
      // Create a map for quick lookup
      const targetMap = new Map(targetFlat.map(item => [item.node_id, item]))
      
      // Merge data with variance
      const mergedData = baselineFlat.map(baselineItem => {
        const targetItem = targetMap.get(baselineItem.node_id)
        if (!targetItem) {
          return {
            ...baselineItem,
            target_adjusted_value: { daily: '0', mtd: '0', ytd: '0' },
            variance: { daily: '0', mtd: '0', ytd: '0' }
          }
        }
        
        // Calculate variance: Target - Baseline
        const variance = {
          daily: (parseFloat(targetItem.adjusted_value?.daily || '0') - parseFloat(baselineItem.adjusted_value?.daily || '0')).toString(),
          mtd: (parseFloat(targetItem.adjusted_value?.mtd || '0') - parseFloat(baselineItem.adjusted_value?.mtd || '0')).toString(),
          ytd: (parseFloat(targetItem.adjusted_value?.ytd || '0') - parseFloat(baselineItem.adjusted_value?.ytd || '0')).toString(),
        }
        
        return {
          ...baselineItem,
          target_adjusted_value: targetItem.adjusted_value,
          variance,
        }
      })
      
      setBaselineData(baselineFlat)
      setTargetData(targetFlat)
      setRowData(mergedData)
      
      // Initialize expandedNodes: expand first 4 levels by default (matches Tab 2)
      const defaultExpanded = new Set<string>()
      mergedData.forEach(row => {
        if (row.depth < 4 && !row.is_leaf) {
          defaultExpanded.add(row.node_id)
        }
      })
      setExpandedNodes(defaultExpanded)
      
    } catch (err: any) {
      console.error('Failed to load comparison results:', err)
      setError(err.response?.data?.detail || 'Failed to load comparison results.')
    } finally {
      setLoading(false)
    }
  }

  // Check if calculation is outdated - Use backend's is_outdated flag instead of client-side comparison
  const checkCalculationFreshness = async (useCaseId: string) => {
    try {
      // Get results from backend which includes is_outdated flag (with grace period)
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/use-cases/${useCaseId}/results`
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

  // Manual Tree Cell Renderer (matches Tab 2 & 3 visual density)
  const nodeNameCellRenderer = useCallback((params: any) => {
    const data = params.data
    if (!data) return ''
    
    const depth = data.depth || 0
    // Check if node is a leaf: no children or empty children array
    const hasChildren = data.children && Array.isArray(data.children) && data.children.length > 0
    const isLeaf = !hasChildren
    const isExpanded = expandedNodes.has(data.node_id)
    const paddingLeft = depth * 20 + 8 // 20px per level + 8px base (matches Tab 2 & 3)
    
    const nodeName = data.node_name || params.value || ''
    
    // Determine node type for icon (from StructuralHierarchyCellRenderer)
    const getNodeIcon = () => {
      if (depth === 0) {
        return '🌐' // Globe for Root
      } else if (data.region || nodeName.includes('Americas') || nodeName.includes('EMEA') || nodeName.includes('APAC')) {
        return '📍' // MapPin for Region
      } else if (data.book || nodeName.includes('Book')) {
        return '💼' // Briefcase for Book
      } else if (data.cost_center || nodeName.includes('Cost Center') || nodeName.includes('Trade')) {
        return '#' // Hash for Cost Center
      }
      return ''
    }
    
    const nodeIcon = getNodeIcon()
    
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
    
    return (
      <div style={{ 
        paddingLeft: `${paddingLeft}px`,
        display: 'flex',
        alignItems: 'center',
        fontWeight: depth === 0 ? '600' : depth === 1 ? '500' : '400',
        color: depth === 0 ? '#2c3e50' : '#333'
      }}>
        {chevron}
        {nodeIcon && <span style={{ marginRight: '6px', fontSize: '14px' }}>{nodeIcon}</span>}
        <span>{nodeName}</span>
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

  // --- RESTORED LOGIC START ---
  // DEFENSIVE DATA PROCESSING: Process rowData into safe, flat format
  const processedRows = useMemo(() => {
    if (!rowData) return []
    
    // DEFENSIVE: Check for "Envelope" structure vs Raw Array
    let rawInput = rowData
    if (!Array.isArray(rawInput) && (rawInput as any).hierarchy) {
      rawInput = (rawInput as any).hierarchy
    }
    
    // Ensure we have an array
    const rootNodes = Array.isArray(rawInput) ? rawInput : [rawInput].filter(Boolean)
    
    if (rootNodes.length === 0) return []
    
    // 1. Flatten the tree (Get all nodes, including leaf nodes)
    const allNodes = flattenTree(rootNodes)
    
    // 2. Map to Flat Format for Charts with safe parsing
    return allNodes.map(row => {
      if (!row) return null
      
      return {
        ...row,
        // Parse amounts safely
        original_amount: parseAmount(row.natural_value || row.original_amount),
        adjusted_amount: parseAmount(row.adjusted_value || row.adjusted_amount),
        
        // Extract Rule Info (Try all possible keys)
        rule_name: row.rule?.rule_name || row.rule?.name || row.rule_name || row.rule?.logic_en || null,
        applied_rule_id: row.rule?.rule_id || row.rule?.id || row.applied_rule_id || null,
        
        // Calculate Delta
        delta: parseAmount(row.adjusted_value || row.adjusted_amount) - parseAmount(row.natural_value || row.original_amount)
      }
    }).filter(Boolean) // Remove any null entries
  }, [rowData])
  // --- RESTORED LOGIC END ---

  // Calculate rule attribution from row data (memoized for performance)
  // Uses "Anchor & Scale" logic: Selected Scope Node is Source of Truth
  const attributionResult = useMemo(() => {
    if (!processedRows || processedRows.length === 0) {
      console.log('[EXECUTIVE DASHBOARD] No processedRows for attribution calculation')
      return { totalOriginal: 0, totalAdjusted: 0, breakdown: [] }
    }
    
    // Use selected scope node, or fallback to root node, or fallback to first row, or zero-safe object
    const activeNode = scopeNode || 
      processedRows.find((r: any) => 
        r.node_name === 'Global Trading P&L' || 
        r.node_name === 'ROOT' ||
        r.depth === 0 ||
        !r.parent_node_id
      ) || 
      processedRows[0] || 
      { daily_pnl: 0, adjusted_daily: 0, node_name: 'Unknown', natural_value: { daily: 0 }, adjusted_value: { daily: 0 } }
    
    console.log('[EXECUTIVE DASHBOARD] Active Scope Node:', {
      node_name: activeNode?.node_name,
      node_id: activeNode?.node_id,
      depth: activeNode?.depth
    })
    
    // Extract active node values using robust parsing
    const parseVal = (val: any): number => {
      if (typeof val === 'number') return val
      if (!val) return 0
      if (typeof val === 'object' && val !== null) {
        const nested = val.daily || val.mtd || val.ytd || val.value || val.amount
        if (nested !== undefined) return parseVal(nested)
        return 0
      }
      const clean = String(val)
        .replace(/,/g, '')
        .replace(/\$/g, '')
        .replace(/\(/g, '-')
        .replace(/\)/g, '')
        .trim()
      const num = parseFloat(clean)
      return isNaN(num) ? 0 : num
    }
    
    const activeOriginal = parseVal(
      activeNode?.natural_value?.daily ||
      activeNode?.natural_value ||
      activeNode?.daily_pnl ||
      activeNode?.original_daily ||
      0
    )
    
    const activeAdjusted = parseVal(
      activeNode?.adjusted_value?.daily ||
      activeNode?.adjusted_value ||
      activeNode?.adjusted_daily ||
      activeNode?.adjusted_pnl ||
      0
    )
    
    console.log('[EXECUTIVE DASHBOARD] Active Node Values (Source of Truth):', {
      nodeName: activeNode?.node_name,
      original: activeOriginal.toLocaleString(),
      adjusted: activeAdjusted.toLocaleString(),
      delta: (activeAdjusted - activeOriginal).toLocaleString()
    })
    
    console.log('[EXECUTIVE DASHBOARD] Calculating attribution from', processedRows.length, 'rows')
    const result = calculateRuleAttribution(processedRows, activeOriginal, activeAdjusted, activeNode?.node_name)
    console.log('[EXECUTIVE DASHBOARD] Attribution result:', {
      totalOriginal: result.totalOriginal,
      totalAdjusted: result.totalAdjusted,
      breakdownCount: result.breakdown.length,
      breakdown: result.breakdown
    })
    return result
  }, [processedRows, scopeNode])
  
  // Extract breakdown for components that expect array format
  const attributionData = attributionResult.breakdown
  
  // Calculate original and adjusted P&L totals (for waterfall chart)
  // Always use Scope Node values (Source of Truth from attribution calculation)
  const { originalPnl, adjustedPnl } = useMemo(() => {
    // Use totals from attribution calculation (Scope Node is Source of Truth)
    console.log('[EXECUTIVE DASHBOARD] Using P&L totals from Scope Node (Source of Truth):', {
      originalPnl: attributionResult.totalOriginal,
      adjustedPnl: attributionResult.totalAdjusted,
      delta: attributionResult.totalAdjusted - attributionResult.totalOriginal
    })
    return {
      originalPnl: attributionResult.totalOriginal,
      adjustedPnl: attributionResult.totalAdjusted
    }
  }, [attributionResult])
  
  // Create list of key nodes for Analysis Scope dropdown
  // Filter to show only parent nodes (Key Nodes) to keep the list clean
  const keyNodes = useMemo(() => {
    if (!processedRows || processedRows.length === 0) return []
    
    // Key parent nodes (non-leaf nodes with children)
    const parentNodes = processedRows.filter((row: any) => {
      const hasChildren = Array.isArray(row.children) && row.children.length > 0
      const isExplicitParent = row.is_leaf === false || row.depth !== undefined
      const nodeName = row.node_name || ''
      
      // Include known parent nodes or nodes with children
      const isKeyNode = [
        "Global Trading P&L",
        "Americas",
        "Cash Equities",
        "High Touch Trading",
        "EMEA",
        "APAC",
        "UK"
      ].includes(nodeName) || (hasChildren && isExplicitParent)
      
      return isKeyNode
    })
    
    // If we have less than 50 total nodes, show all unique nodes
    // Otherwise, show only key parent nodes
    if (processedRows.length < 50) {
      const uniqueNodes = Array.from(new Map(processedRows.map((r: any) => [r.node_name, r])).values())
      return uniqueNodes.sort((a: any, b: any) => {
        // Sort by depth first, then by name
        const depthA = a.depth || 0
        const depthB = b.depth || 0
        if (depthA !== depthB) return depthA - depthB
        return (a.node_name || '').localeCompare(b.node_name || '')
      })
    }
    
    return parentNodes.sort((a: any, b: any) => {
      const depthA = a.depth || 0
      const depthB = b.depth || 0
      if (depthA !== depthB) return depthA - depthB
      return (a.node_name || '').localeCompare(b.node_name || '')
    })
  }, [processedRows])

  // Delta Mode Filtering: Show only rows with changes or parent nodes
  const displayRowData = useMemo(() => {
    if (viewMode !== 'delta') {
      return processedRows
    }
    
    // Filter to show only rows where abs(adjusted - original) > 0.01 OR is_parent = true
    return processedRows.filter((row: any) => {
      // Always show parent nodes
      if (row.is_parent === true) {
        return true
      }
      
      // Calculate delta
      const original = parseFloat(row.natural_value?.daily || row.daily_pnl || 0)
      const adjusted = parseFloat(row.adjusted_value?.daily || row.adjusted_daily || 0)
      const delta = Math.abs(adjusted - original)
      
      return delta > 0.01
    })
  }, [processedRows, viewMode])

  // AG-Grid Column Definitions (dynamic based on view mode and comparison mode)
  const getColumnDefs = (): ColDef[] => {
    // Manual Tree Engine: node_name column with manual tree renderer
    const baseColumns: ColDef[] = [
      {
        field: 'node_name',
        headerName: 'Dimension Node',
        flex: 2,
        pinned: 'left',
        cellRenderer: nodeNameCellRenderer,
        cellStyle: (params: any) => {
          const depth = params.data?.depth || 0
          return {
            backgroundColor: depth === 0 ? '#f0f4f8' : depth === 1 ? '#f9f9f9' : '#ffffff',
            borderLeft: depth > 1 ? '1px solid #e0e0e0' : 'none',
          }
        },
      }
    ]

    // Step 4.3: Comparison Mode Columns
    if (isComparisonMode) {
      return [
        ...baseColumns,
        {
          field: 'baseline_adjusted_value',
          headerName: 'Baseline P&L',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.adjusted_value?.daily || 0),
          valueFormatter: (params) => {
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
          },
          cellStyle: { textAlign: 'right' },
        },
        {
          field: 'target_adjusted_value',
          headerName: 'Target P&L',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.target_adjusted_value?.daily || 0),
          valueFormatter: (params) => {
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
          },
          cellStyle: { textAlign: 'right' },
        },
        {
          field: 'variance',
          headerName: 'Variance (Target - Baseline)',
          headerTooltip: 'Green = Positive movement (Revenue up/Expense down), Red = Negative movement',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.variance?.daily || 0),
          valueFormatter: (params) => {
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
          },
          cellStyle: (params) => {
            const value = parseFloat(params.data?.variance?.daily || 0)
            const baseStyle: any = { textAlign: 'right', fontWeight: '600' }
            // Green for positive (revenue up/expense down), Red for negative
            if (value > 0.01) {
              baseStyle.color = '#10b981' // Green
            } else if (value < -0.01) {
              baseStyle.color = '#ef4444' // Red
            } else {
              baseStyle.color = '#6b7280' // Gray for zero
            }
            return baseStyle
          },
        },
      ]
    }

    if (viewMode === 'standard') {
      // Standard: Show Natural, Adjusted, Plug
      return [
        ...baseColumns,
        {
          field: 'natural_value',
          headerName: 'Original Daily P&L',
          headerTooltip: 'Original P&L from source data (before business rules are applied)',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.natural_value?.daily || 0),
          valueFormatter: (params) => {
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
          headerName: 'Adjusted Daily P&L',
          headerTooltip: 'P&L after business rules are applied',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.adjusted_value?.daily || 0),
          valueFormatter: (params) => {
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
          headerTooltip: 'Plug = Original Daily P&L - Adjusted Daily P&L (Golden Equation: Original = Adjusted + Plug)',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.plug?.daily || 0),
          valueFormatter: (params) => {
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
          headerName: 'Business Rule',
          headerTooltip: 'Business rule applied to this node',
          flex: 1.5,
          cellRenderer: BusinessRuleCellRenderer,
          cellStyle: { textAlign: 'left', paddingLeft: '8px' },
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
          headerName: 'Original Daily P&L',
          headerTooltip: 'Original P&L from source data (before business rules are applied)',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.natural_value?.daily || 0),
          valueFormatter: (params) => {
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
          },
          cellStyle: { textAlign: 'right', cursor: 'pointer' },
          onCellClicked: (params) => loadCalculationTrace(params.data),
        },
        {
          field: 'adjusted_value',
          headerName: 'Adjusted Daily P&L',
          headerTooltip: 'P&L after business rules are applied',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.adjusted_value?.daily || 0),
          valueFormatter: (params) => {
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
          },
          cellStyle: { textAlign: 'right', cursor: 'pointer' },
          onCellClicked: (params) => loadCalculationTrace(params.data),
        },
        {
          field: 'plug',
          headerName: 'Reconciliation Plug',
          headerTooltip: 'Plug = Original Daily P&L - Adjusted Daily P&L (Golden Equation: Original = Adjusted + Plug)',
          flex: 1.2,
          valueGetter: (params) => parseFloat(params.data?.plug?.daily || 0),
          valueFormatter: (params) => {
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
          headerName: 'Business Rule',
          headerTooltip: 'Business rule applied to this node',
          flex: 1.5,
          cellRenderer: BusinessRuleCellRenderer,
          cellStyle: { textAlign: 'left', paddingLeft: '8px' },
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
    
    // Manual Tree Engine: Trigger external filter after grid is ready
    setTimeout(() => {
      if (params.api) {
        params.api.onFilterChanged()
      }
    }, 100)
  }

  // Handle row click to update scope node
  const onRowClicked = (params: any) => {
    if (params.data) {
      setScopeNode(params.data)
      console.log('[EXECUTIVE DASHBOARD] Scope node updated to:', params.data?.node_name)
    }
  }

  // Row style for conditional formatting (amber highlight for plugs, blue for selected scope)
  // DEPRECATED: StructuralHierarchyCellRenderer - Replaced by nodeNameCellRenderer (Manual Tree Engine)
  // Kept for reference but no longer used
  const StructuralHierarchyCellRenderer: React.FC<ICellRendererParams> = (params) => {
    const depth = params.data?.depth || 0
    const nodeName = params.value || params.data?.node_name || ''
    const hasChildren = params.data?.children && params.data.children.length > 0
    // Safely check if node is expanded (can be property or method)
    const isExpanded = params.node 
      ? (typeof params.node.isExpanded === 'function' 
          ? params.node.isExpanded() 
          : params.node.expanded === true)
      : false
    
    // Determine node type for icon
    const getNodeIcon = () => {
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
    
    const toggleExpand = (e: React.MouseEvent) => {
      e.stopPropagation()
      if (params.node) {
        if (typeof params.node.setExpanded === 'function') {
          params.node.setExpanded(!isExpanded)
        } else if (typeof params.node.expanded !== 'undefined') {
          // Fallback: try to toggle expanded property directly
          params.node.expanded = !isExpanded
        }
      }
    }
    
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'stretch',
        height: '100%',
        width: '100%'
      }}>
        {/* The Indentation "Guide Rails" */}
        {Array.from({ length: depth }).map((_, i) => (
          <div
            key={i}
            style={{
              flexShrink: 0,
              width: '32px',
              height: '100%',
              borderRight: '1px solid #e5e7eb',
              backgroundColor: 'rgba(249, 250, 251, 0.5)' // gray-50/50
            }}
          />
        ))}
        
        {/* The Expand Toggle / Leaf Connector */}
        <div
          style={{
            flexShrink: 0,
            width: '32px',
            height: '100%',
            borderRight: '1px solid #e5e7eb',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(249, 250, 251, 0.5)', // gray-50/50
            cursor: hasChildren ? 'pointer' : 'default'
          }}
          onClick={toggleExpand}
        >
          {hasChildren ? (
            isExpanded ? (
              <span style={{ fontSize: '14px', color: '#6b7280' }}>▼</span>
            ) : (
              <span style={{ fontSize: '14px', color: '#6b7280' }}>▶</span>
            )
          ) : (
            <div style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: '#d1d5db'
            }} />
          )}
        </div>
        
        {/* The Node Cell with Icon and Name */}
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          paddingLeft: '8px',
          fontSize: '0.875rem',
          fontWeight: 500,
          color: '#374151'
        }}>
          {getNodeIcon() && <span style={{ marginRight: '6px', fontSize: '14px' }}>{getNodeIcon()}</span>}
          <span>{nodeName}</span>
        </div>
      </div>
    )
  }

  const getRowStyle = (params: any) => {
    const baseStyle: any = {
      height: '40px', // h-10
      padding: 0
    }
    
    // Zebra striping: even rows get subtle gray background
    if (params.node.rowIndex % 2 === 1) {
      baseStyle.backgroundColor = 'rgba(249, 250, 251, 0.3)' // gray-50/30
    }
    
    // Highlight selected scope node with light blue background
    if (scopeNode && params.data?.node_id === scopeNode?.node_id) {
      baseStyle.backgroundColor = '#e0f2fe' // Light blue
      baseStyle.borderLeft = '3px solid #0ea5e9' // Blue border
    }
    // Amber background for rows with plugs
    else if (params.data?.hasPlug) {
      baseStyle.backgroundColor = '#fef3c7' // Amber background
    }
    
    return baseStyle
  }

  // Export Reconciliation Excel (Phase 5.9: Backend-generated Excel with formatting)
  const handleExportReconciliation = async () => {
    if (!selectedUseCaseId) {
      setError('Please select a use case first.')
      return
    }

    try {
      // Call the backend Excel export endpoint
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/export/reconciliation`,
        {
          responseType: 'blob', // Important: receive as blob for file download
        }
      )

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      
      // Extract filename from Content-Disposition header or use default
      const contentDisposition = response.headers['content-disposition']
      let filename = `reconciliation_export_${new Date().toISOString().split('T')[0]}.xlsx`
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }
      
      link.setAttribute('download', filename)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      // Clean up the URL object
      window.URL.revokeObjectURL(url)
      
      console.log('[TAB 4] Excel export completed successfully')
    } catch (err: any) {
      console.error('[TAB 4] Failed to export Excel:', err)
      setError(err.response?.data?.detail || 'Failed to export reconciliation data. Please try again.')
    }
  }

  // Handle Run Calculation (same logic as Tab 3)
  const handleRunCalculation = async () => {
    if (!selectedUseCaseId) {
      setError('Please select a use case first.')
      return
    }

    setCalculating(true)
    setError(null)

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/calculate`
      )

      // Show success message
      const rulesCount = response.data.rules_applied || 0
      const totalPlug = response.data.total_plug?.daily || 0
      const formattedPlug = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(totalPlug)

      console.log(`[TAB 4] Calculation complete: ${rulesCount} rules applied, Total Plug: ${formattedPlug}`)

      // Update last calculated timestamp
      if (response.data.run_timestamp) {
        setLastCalculated(response.data.run_timestamp)
      }

      // Automatically refresh results after calculation succeeds
      // Small delay to ensure backend has finished writing results
      setTimeout(() => {
        loadResults(selectedUseCaseId)
        // Also reload runs to get the new run in the dropdown
        loadRuns(selectedUseCaseId)
      }, 500)

      // Show success toast/notification (optional - can be enhanced with toast library)
      alert(`✅ Calculation complete!\n${rulesCount} rules applied\nTotal Plug: ${formattedPlug}`)

    } catch (err: any) {
      console.error('[TAB 4] Failed to run calculation:', err)
      setError(err.response?.data?.detail || 'Failed to run calculation. Please try again.')
    } finally {
      setCalculating(false)
    }
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
          
          {/* Run Selector - Step 4.2: Date-anchored runs */}
          {selectedUseCaseId && runs.length > 0 && (
            <>
              <label htmlFor="run-select" style={{ marginLeft: '16px', fontWeight: '500' }}>Run:</label>
              <select
                id="run-select"
                className="use-case-select"
                value={selectedRunId}
                onChange={(e) => {
                  setSelectedRunId(e.target.value)
                  if (e.target.value) {
                    loadResults(selectedUseCaseId, e.target.value)
                  }
                }}
                style={{ minWidth: '250px', marginLeft: '8px' }}
              >
                <option value="">Select a run...</option>
                {/* DEDUPLICATION FIX: Create a unique Set of runs based on id/run_id to prevent duplicates */}
                {Array.from(new Set(runs.map((run: any) => run.id || run.run_id).filter(Boolean)))
                  .map(id => {
                    const run = runs.find((r: any) => (r.id || r.run_id) === id)
                    if (!run) return null
                    return (
                      <option key={id} value={id}>
                        {run.run_name || run.version_tag || 'Run'} - {new Date(run.executed_at || run.run_timestamp || '').toLocaleString()}
                      </option>
                    )
                  })
                  .filter(Boolean)}
              </select>
            </>
          )}
          
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
          {/* Run Calculation Button */}
          <button
            onClick={handleRunCalculation}
            disabled={calculating || !selectedUseCaseId}
            style={{
              background: calculating 
                ? 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)' 
                : 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
              color: 'white',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              fontWeight: '600',
              cursor: calculating || !selectedUseCaseId ? 'not-allowed' : 'pointer',
              opacity: calculating || !selectedUseCaseId ? 0.6 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              marginRight: '8px',
              transition: 'all 0.2s ease'
            }}
            title={calculating ? 'Processing calculation...' : !selectedUseCaseId ? 'Please select a use case first' : 'Run waterfall calculation with current business rules'}
          >
            {calculating ? (
              <>
                <span style={{ 
                  display: 'inline-block',
                  width: '14px',
                  height: '14px',
                  border: '2px solid rgba(255, 255, 255, 0.3)',
                  borderTopColor: 'white',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite'
                }}></span>
                Processing...
              </>
            ) : (
              <>
                <span style={{ fontSize: '1em' }}>⚡</span>
                Run Calculation
              </>
            )}
          </button>
          {/* Refresh Button */}
          <button
            onClick={() => selectedUseCaseId && loadResults(selectedUseCaseId, selectedRunId || undefined)}
            disabled={loading || !selectedUseCaseId}
            style={{
              background: '#f3f4f6',
              color: '#374151',
              border: '1px solid #d1d5db',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              fontWeight: '500',
              cursor: loading || !selectedUseCaseId ? 'not-allowed' : 'pointer',
              opacity: loading || !selectedUseCaseId ? 0.6 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              marginRight: '8px',
              transition: 'all 0.2s ease'
            }}
            title={!selectedUseCaseId ? 'Please select a use case first' : 'Refresh current results'}
          >
            {loading ? (
              <>
                <span style={{ 
                  display: 'inline-block',
                  width: '14px',
                  height: '14px',
                  border: '2px solid rgba(55, 65, 81, 0.3)',
                  borderTopColor: '#374151',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite'
                }}></span>
                Loading...
              </>
            ) : (
              <>
                <span>🔄</span>
                Refresh
              </>
            )}
          </button>
          <button
            onClick={handleExportReconciliation}
            disabled={!selectedUseCaseId || processedRows.length === 0}
            style={{
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              color: 'white',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              fontWeight: '600',
              cursor: !selectedUseCaseId || processedRows.length === 0 ? 'not-allowed' : 'pointer',
              opacity: !selectedUseCaseId || processedRows.length === 0 ? 0.6 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease'
            }}
            title={!selectedUseCaseId ? 'Please select a use case first' : 'Export reconciliation data to Excel'}
          >
            <span style={{ fontSize: '1em' }}>📊</span>
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
        <strong>Golden Equation:</strong> Original Daily P&L = Adjusted Daily P&L + Reconciliation Plug
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
            rowData={displayRowData}
            columnDefs={columnDefs}
            defaultColDef={defaultColDef}
            onGridReady={onGridReady}
            onRowClicked={onRowClicked}
            getRowId={(params) => params.data.node_id || params.data.id || params.data.node_name || `row-${params.rowIndex}`}
            animateRows={true}
            loading={loading}
            getRowStyle={getRowStyle}
            rowSelection="single"
            suppressRowGroupHidesColumns={true}
            suppressRowClickSelection={false}
            // Manual Tree Engine: External filter for parent-child visibility
            isExternalFilterPresent={isExternalFilterPresent}
            doesExternalFilterPass={doesExternalFilterPass}
            // Clean Look: Compact row and header heights (matches Tab 2 & 3)
            rowHeight={32}
            headerHeight={32}
          />
        </div>
      </div>

      {/* Rule Attribution Analysis Table and Waterfall Chart */}
      {processedRows.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginTop: '2rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', marginBottom: '0.5rem' }}>
            Adjustment Attribution Analysis
          </h3>
          
          {/* Debug info (can be removed later) */}
          {process.env.NODE_ENV === 'development' && (
            <div style={{ padding: '0.5rem', backgroundColor: '#f3f4f6', borderRadius: '4px', fontSize: '0.875rem', color: '#6b7280' }}>
              Debug: {processedRows.length} rows, {attributionData.length} attribution items, Original: ${originalPnl.toLocaleString()}, Adjusted: ${adjustedPnl.toLocaleString()}
            </div>
          )}
          
          {/* Analysis Scope Dropdown Control */}
          {attributionData.length > 0 && originalPnl !== 0 && keyNodes.length > 0 && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              padding: '0.75rem 1rem',
              backgroundColor: '#f9fafb',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              marginBottom: '0.5rem'
            }}>
              <label style={{ 
                fontWeight: '600', 
                color: '#374151',
                fontSize: '0.875rem',
                whiteSpace: 'nowrap'
              }}>
                Analysis Scope:
              </label>
              <select
                style={{
                  border: '1px solid #d1d5db',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '6px',
                  width: '300px',
                  fontSize: '0.875rem',
                  color: '#1f2937',
                  backgroundColor: 'white',
                  cursor: 'pointer'
                }}
                value={scopeNode?.node_name || ""}
                onChange={(e) => {
                  const node = processedRows.find((n: any) => n.node_name === e.target.value)
                  if (node) {
                    setScopeNode(node)
                    console.log('[EXECUTIVE DASHBOARD] Scope changed via dropdown to:', node.node_name)
                    
                    // Scroll to the selected row in the grid if possible
                    if (gridApi) {
                      gridApi.forEachNode((rowNode: any) => {
                        if (rowNode.data?.node_id === node.node_id) {
                          gridApi.ensureNodeVisible(rowNode, 'middle')
                        }
                      })
                    }
                  }
                }}
              >
                <option value="">-- Select Scope --</option>
                {/* DEDUPLICATION FIX: Create a unique Set of nodes based on node_id to prevent duplicates */}
                {Array.from(new Set(keyNodes.map((r: any) => r.node_id).filter(Boolean)))
                  .map(id => {
                    const node = keyNodes.find((r: any) => r.node_id === id)
                    if (!node) return null
                    const depth = node.depth || 0
                    const indent = '  '.repeat(depth) // Simple indentation for hierarchy
                    return (
                      <option key={id} value={node.node_name}>
                        {indent}{node.node_name}
                      </option>
                    )
                  })
                  .filter(Boolean)}
              </select>
              <span style={{ 
                fontSize: '0.75rem', 
                color: '#6b7280',
                fontStyle: 'italic'
              }}>
                Select a hierarchy level to re-anchor the Waterfall Bridge.
              </span>
            </div>
          )}
          
          {/* Waterfall Chart */}
          {attributionData.length > 0 && originalPnl !== 0 && (
            <PnlWaterfallChart
              attributionData={attributionData}
              originalPnl={originalPnl}
              adjustedPnl={adjustedPnl}
                rootNodeName={scopeNode?.node_name || 
                processedRows.find((r: any) => 
                  r.node_name === 'Global Trading P&L' || 
                  r.node_name === 'ROOT' ||
                  r.depth === 0 ||
                  !r.parent_node_id
                )?.node_name || 'Global Trading P&L'}
              onBarClick={(ruleName) => {
                setSelectedDrillRule(ruleName)
                console.log('[EXECUTIVE DASHBOARD] Opening forensic drill-down for rule:', ruleName)
              }}
            />
          )}
          
          {/* Impact Table */}
          {attributionData.length > 0 ? (
            <RuleImpactTable attributionData={attributionData} />
          ) : (
            <div style={{ 
              padding: '2rem', 
              backgroundColor: '#f9fafb', 
              borderRadius: '8px', 
              textAlign: 'center',
              color: '#6b7280'
            }}>
              <p style={{ margin: 0 }}>No rule attribution data available.</p>
              <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.875rem' }}>
                Attribution is calculated from leaf nodes with rule impacts. Run a calculation to see attribution data.
              </p>
            </div>
          )}
        </div>
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
                    <strong>1. Original Daily P&L:</strong>
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
                    <strong>3. Adjusted Daily P&L:</strong>
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

      {/* Drill-Down Modal for Waterfall Chart */}
      {selectedRuleName && (
        <DrillDownModal
          ruleName={selectedRuleName}
          rows={processedRows}
          onClose={() => setSelectedRuleName(null)}
        />
      )}

      {/* Forensic Drill-Down Modal (Rule Evidence Locker) */}
      {selectedDrillRule && (
        <RuleDrillDownModal
          isOpen={!!selectedDrillRule}
          onClose={() => setSelectedDrillRule(null)}
          ruleName={selectedDrillRule}
          allRows={processedRows}
        />
      )}
    </div>
  )
}

export default ExecutiveDashboard

