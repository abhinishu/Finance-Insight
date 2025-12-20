import React, { useState, useEffect, useCallback, useRef } from 'react'
import { AgGridReact } from 'ag-grid-react'
import { ColDef, GridApi, ColumnApi } from 'ag-grid-community'
import axios from 'axios'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'
import './RuleEditor.css'

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

  // Editor Mode
  const [editorMode, setEditorMode] = useState<'ai' | 'standard'>('ai')

  // AI Mode State
  const [aiPrompt, setAiPrompt] = useState<string>('')
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

  // Load hierarchy when use case is selected
  useEffect(() => {
    if (selectedUseCase) {
      loadHierarchy(selectedUseCase.atlas_structure_id)
    }
  }, [selectedUseCase])

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

  const loadHierarchy = async (structureId: string) => {
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

      // Flatten hierarchy for AG-Grid
      const flatData = flattenHierarchy(hierarchy)
      setRowData(flatData)
    } catch (err: any) {
      console.error('Failed to load hierarchy:', err)
      setError('Failed to load hierarchy data.')
    } finally {
      setLoading(false)
    }
  }

  const flattenHierarchy = (nodes: HierarchyNode[], parentPath: string[] = []): any[] => {
    const result: any[] = []
    
    for (const node of nodes) {
      const path = node.path || parentPath.concat([node.node_name])
      const row = {
        ...node,
        path, // AG-Grid treeData uses getDataPath to extract this
      }
      result.push(row)
      
      // Recursively add children if they exist
      if (node.children && node.children.length > 0) {
        result.push(...flattenHierarchy(node.children, path))
      }
    }
    
    return result
  }

  // AG-Grid Column Definitions
  const columnDefs: ColDef[] = [
    {
      field: 'node_name',
      headerName: 'Node Name',
      flex: 1,
      cellRenderer: 'agGroupCellRenderer',
    },
    {
      field: 'node_id',
      headerName: 'Node ID',
      flex: 0.8,
    },
    {
      field: 'daily_pnl',
      headerName: 'Daily P&L',
      flex: 0.6,
      valueFormatter: (params) => {
        if (!params.value) return '$0.00'
        const num = parseFloat(params.value)
        return `$${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
      },
    },
  ]

  const defaultColDef: ColDef = {
    sortable: true,
    filter: true,
    resizable: true,
  }

  const onGridReady = (params: { api: GridApi; columnApi: ColumnApi }) => {
    setGridApi(params.api)
  }

  const onSelectionChanged = () => {
    if (gridApi) {
      const selectedRows = gridApi.getSelectedRows()
      if (selectedRows.length > 0) {
        setSelectedNode(selectedRows[0])
        // Clear preview when node changes
        setRulePreview(null)
      } else {
        setSelectedNode(null)
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
    if (!selectedNode || !selectedUseCaseId || !aiPrompt.trim()) {
      setError('Please select a node and enter a natural language prompt.')
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
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules/genai`,
        {
          node_id: selectedNode.node_id,
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
    if (!selectedNode || !selectedUseCaseId) {
      setError('Please select a node.')
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
      // Create rule to get SQL
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules`,
        {
          node_id: selectedNode.node_id,
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

  // Save & Apply Rule
  const handleSaveRule = async () => {
    if (!selectedNode || !selectedUseCaseId || !rulePreview?.sql_where) {
      setError('No rule to save. Please generate a rule first.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      if (editorMode === 'ai' && rulePreview.logic_en) {
        // Save AI-generated rule
        await axios.post(
          `${API_BASE_URL}/api/v1/use-cases/${selectedUseCaseId}/rules`,
          {
            node_id: selectedNode.node_id,
            logic_en: rulePreview.logic_en,
            last_modified_by: 'user123', // TODO: Get from auth context
          }
        )
      } else if (editorMode === 'standard' && conditions.length > 0) {
        // Save standard rule
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
            node_id: selectedNode.node_id,
            conditions: formattedConditions,
            last_modified_by: 'user123', // TODO: Get from auth context
          }
        )
      }

      // Success - clear form and show message
      setRulePreview(null)
      setAiPrompt('')
      setConditions([{ field: '', operator: 'equals', value: '' }])
      setCalculationResult('Rule saved successfully!')
      setTimeout(() => setCalculationResult(null), 3000)
    } catch (err: any) {
      console.error('Failed to save rule:', err)
      setError(err.response?.data?.detail || 'Failed to save rule. Please try again.')
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
    } catch (err: any) {
      console.error('Failed to run calculation:', err)
      setError(err.response?.data?.detail || 'Failed to run calculation. Please try again.')
    } finally {
      setCalculating(false)
    }
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

      {/* Split Pane Layout */}
      <div className="rule-editor-split">
        {/* Left Pane: Hierarchy Tree */}
        <div className="rule-editor-left">
          <div className="pane-header">
            <h3>Hierarchy Tree</h3>
            <p>Select a node to apply a rule</p>
          </div>
          <div className="ag-theme-alpine" style={{ height: '100%', width: '100%' }}>
            <AgGridReact
              ref={gridRef}
              rowData={rowData}
              columnDefs={columnDefs}
              defaultColDef={defaultColDef}
              onGridReady={onGridReady}
              onSelectionChanged={onSelectionChanged}
              rowSelection="single"
              treeData={true}
              getDataPath={(data) => data.path || []}
              groupDefaultExpanded={1}
              animateRows={true}
              loading={loading}
            />
          </div>
        </div>

        {/* Right Pane: Rule Editor */}
        <div className="rule-editor-right">
          <div className="pane-header">
            <h3>Rule Editor</h3>
            {selectedNode && (
              <p className="selected-node">
                Selected: <strong>{selectedNode.node_name}</strong> ({selectedNode.node_id})
              </p>
            )}
          </div>

          {!selectedNode ? (
            <div className="no-selection">
              <p>Please select a node from the hierarchy tree to create a rule.</p>
            </div>
          ) : (
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
                  <textarea
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
          )}
        </div>
      </div>
    </div>
  )
}

export default RuleEditor

