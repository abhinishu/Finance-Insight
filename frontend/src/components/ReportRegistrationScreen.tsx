import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './ReportRegistrationScreen.css'

interface Structure {
  structure_id: string
  name: string
  node_count: number
}

interface ReportRegistration {
  report_id: string
  report_name: string
  atlas_structure_id: string
  selected_measures: string[]
  selected_dimensions: string[] | null
  measure_scopes?: { [key: string]: string[] }
  dimension_scopes?: { [key: string]: string[] }
  owner_id: string
  created_at: string
  updated_at: string
  status?: string
}

type Scope = 'input' | 'rule' | 'output'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const ReportRegistrationScreen: React.FC = () => {
  const [viewMode, setViewMode] = useState<'list' | 'form'>('list')
  const [editingReportId, setEditingReportId] = useState<string | null>(null)
  
  const [reportName, setReportName] = useState<string>('')
  const [selectedStructure, setSelectedStructure] = useState<string>('')
  const [availableStructures, setAvailableStructures] = useState<Structure[]>([])
  const [selectedMeasures, setSelectedMeasures] = useState<string[]>(['daily', 'mtd', 'ytd'])
  const [selectedDimensions, setSelectedDimensions] = useState<string[]>(['region', 'product', 'desk', 'strategy'])
  
  // Scoping: measure_scopes and dimension_scopes (scope matrix)
  const [measureScopes, setMeasureScopes] = useState<{ [key: string]: string[] }>({})
  const [dimensionScopes, setDimensionScopes] = useState<{ [key: string]: string[] }>({})
  
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [registeredReports, setRegisteredReports] = useState<ReportRegistration[]>([])
  const [showConfirmation, setShowConfirmation] = useState<boolean>(false)
  const [confirmationData, setConfirmationData] = useState<any>(null)

  // Available measures
  const availableMeasures = [
    { id: 'daily', label: 'Daily P&L' },
    { id: 'wtd', label: 'WTD (Week-to-Date)' },
    { id: 'mtd', label: 'MTD (Month-to-Date)' },
    { id: 'ytd', label: 'YTD (Year-to-Date)' }
  ]

  // Available dimensions
  const availableDimensions = [
    { id: 'region', label: 'Region' },
    { id: 'product', label: 'Product' },
    { id: 'desk', label: 'Desk' },
    { id: 'strategy', label: 'Strategy' }
  ]

  // Available scopes
  const availableScopes: { id: Scope; label: string; tab: string }[] = [
    { id: 'input', label: 'Input', tab: 'Tab 2' },
    { id: 'rule', label: 'Business Rules', tab: 'Tab 3' },
    { id: 'output', label: 'Output', tab: 'Tab 4' }
  ]

  // Load available structures
  useEffect(() => {
    const loadStructures = async () => {
      try {
        const response = await axios.get<{ structures: Structure[] }>(
          `${API_BASE_URL}/api/v1/structures`
        )
        setAvailableStructures(response.data.structures)
        if (response.data.structures.length > 0 && !selectedStructure) {
          setSelectedStructure(response.data.structures[0].structure_id)
        }
      } catch (err: any) {
        console.error('Failed to load structures:', err)
        setError('Failed to load available structures')
      }
    }
    loadStructures()
  }, [])

  // Load registered reports
  const loadReports = async () => {
    try {
      const response = await axios.get<ReportRegistration[]>(
        `${API_BASE_URL}/api/v1/reports`
      )
      setRegisteredReports(response.data)
    } catch (err: any) {
      console.error('Failed to load reports:', err)
    }
  }

  useEffect(() => {
    loadReports()
  }, [])

  // Initialize default scopes when measures/dimensions change
  useEffect(() => {
    const newMeasureScopes: { [key: string]: string[] } = {}
    selectedMeasures.forEach(measure => {
      if (!measureScopes[measure]) {
        newMeasureScopes[measure] = ['input', 'rule', 'output'] // Default: all scopes
      } else {
        newMeasureScopes[measure] = measureScopes[measure]
      }
    })
    setMeasureScopes(newMeasureScopes)
  }, [selectedMeasures])

  useEffect(() => {
    const newDimensionScopes: { [key: string]: string[] } = {}
    selectedDimensions.forEach(dimension => {
      if (!dimensionScopes[dimension]) {
        newDimensionScopes[dimension] = ['input', 'rule', 'output'] // Default: all scopes
      } else {
        newDimensionScopes[dimension] = dimensionScopes[dimension]
      }
    })
    setDimensionScopes(newDimensionScopes)
  }, [selectedDimensions])

  const handleMeasureToggle = (measureId: string) => {
    setSelectedMeasures(prev =>
      prev.includes(measureId)
        ? prev.filter(m => m !== measureId)
        : [...prev, measureId]
    )
  }

  const handleDimensionToggle = (dimensionId: string) => {
    setSelectedDimensions(prev =>
      prev.includes(dimensionId)
        ? prev.filter(d => d !== dimensionId)
        : [...prev, dimensionId]
    )
  }

  // Scope matrix toggle - grid selection
  const handleScopeToggle = (type: 'measure' | 'dimension', itemId: string, scope: Scope) => {
    if (type === 'measure') {
      setMeasureScopes(prev => {
        const current = prev[itemId] || []
        const updated = current.includes(scope)
          ? current.filter(s => s !== scope)
          : [...current, scope]
        return { ...prev, [itemId]: updated }
      })
    } else {
      setDimensionScopes(prev => {
        const current = prev[itemId] || []
        const updated = current.includes(scope)
          ? current.filter(s => s !== scope)
          : [...current, scope]
        return { ...prev, [itemId]: updated }
      })
    }
  }

  const handleCreateNew = () => {
    setViewMode('form')
    setEditingReportId(null)
    setReportName('')
    setSelectedMeasures(['daily', 'mtd', 'ytd'])
    setSelectedDimensions(['region', 'product', 'desk', 'strategy'])
    setMeasureScopes({})
    setDimensionScopes({})
    setError(null)
    setSuccess(null)
  }

  const handleEdit = async (reportId: string) => {
    try {
      const response = await axios.get<ReportRegistration>(
        `${API_BASE_URL}/api/v1/reports/${reportId}`
      )
      const report = response.data
      
      setEditingReportId(reportId)
      setReportName(report.report_name)
      setSelectedStructure(report.atlas_structure_id)
      setSelectedMeasures(report.selected_measures)
      setSelectedDimensions(report.selected_dimensions || [])
      setMeasureScopes(report.measure_scopes || {})
      setDimensionScopes(report.dimension_scopes || {})
      setViewMode('form')
      setError(null)
      setSuccess(null)
    } catch (err: any) {
      setError('Failed to load report for editing')
      console.error(err)
    }
  }

  const handleSaveClick = () => {
    // Prepare confirmation data
    const structureName = availableStructures.find(s => s.structure_id === selectedStructure)?.name || selectedStructure
    const measureCount = selectedMeasures.length
    const dimensionCount = selectedDimensions.length
    
    setConfirmationData({
      reportName,
      structureName,
      measureCount,
      dimensionCount,
      isEdit: !!editingReportId
    })
    setShowConfirmation(true)
  }

  const handleConfirmSave = async () => {
    setShowConfirmation(false)
    
    if (!reportName.trim()) {
      setError('Please enter a report name')
      return
    }

    if (!selectedStructure) {
      setError('Please select an Atlas structure')
      return
    }

    if (selectedMeasures.length === 0) {
      setError('Please select at least one measure')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const payload = {
        report_name: reportName,
        atlas_structure_id: selectedStructure,
        selected_measures: selectedMeasures,
        selected_dimensions: selectedDimensions.length > 0 ? selectedDimensions : null,
        measure_scopes: measureScopes,
        dimension_scopes: dimensionScopes,
        owner_id: 'current_user'
      }

      if (editingReportId) {
        // Update existing report
        await axios.put<ReportRegistration>(
          `${API_BASE_URL}/api/v1/reports/${editingReportId}`,
          payload
        )
        setSuccess(`Report "${reportName}" updated successfully!`)
      } else {
        // Create new report
        await axios.post<ReportRegistration>(
          `${API_BASE_URL}/api/v1/reports`,
          payload
        )
        setSuccess(`Report "${reportName}" registered successfully!`)
      }

      // Reset form
      handleCreateNew()
      
      // Reload reports list
      await loadReports()
      
      // Switch back to list view after a delay
      setTimeout(() => {
        setViewMode('list')
      }, 1500)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to save report'
      setError(errorMsg)
      console.error('Save error:', err)
    } finally {
      setLoading(false)
    }
  }

  const getStructureName = (structureId: string) => {
    return availableStructures.find(s => s.structure_id === structureId)?.name || structureId
  }

  return (
    <div className="report-registration-screen">
      {viewMode === 'list' ? (
        <div className="report-library-container">
          <div className="library-header">
            <h2>Report Library</h2>
            <button onClick={handleCreateNew} className="create-new-button">
              + Create New Report
            </button>
          </div>

          {registeredReports.length === 0 ? (
            <div className="empty-state">
              <p>No reports registered yet</p>
              <button onClick={handleCreateNew} className="create-first-button">
                Create Your First Report
              </button>
            </div>
          ) : (
            <div className="reports-table-container">
              <table className="reports-table">
                <thead>
                  <tr>
                    <th>Report Name</th>
                    <th>Structure</th>
                    <th>Created Date</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {registeredReports.map((report) => (
                    <tr key={report.report_id}>
                      <td>{report.report_name}</td>
                      <td>{getStructureName(report.atlas_structure_id)}</td>
                      <td>{new Date(report.created_at).toLocaleDateString()}</td>
                      <td>
                        <span className="status-badge">{report.status || 'ACTIVE'}</span>
                      </td>
                      <td>
                        <button
                          onClick={() => handleEdit(report.report_id)}
                          className="edit-button"
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="registration-container">
          <div className="form-header">
            <h2>{editingReportId ? 'Edit Report' : 'Report Registration'}</h2>
            <button onClick={() => setViewMode('list')} className="back-button">
              ← Back to Library
            </button>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {success && (
            <div className="success-message">
              {success}
            </div>
          )}

          <div className="form-section">
            <div className="form-group">
              <label htmlFor="report-name">Report Name *</label>
              <input
                id="report-name"
                type="text"
                value={reportName}
                onChange={(e) => setReportName(e.target.value)}
                placeholder="e.g., Americas Trading P&L"
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="structure-select">Atlas Structure *</label>
              <select
                id="structure-select"
                value={selectedStructure}
                onChange={(e) => setSelectedStructure(e.target.value)}
                className="form-select"
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
            </div>

            {/* Scope Matrix for Measures */}
            <div className="form-group">
              <label>Measures *</label>
              <div className="scope-matrix-container">
                <table className="scope-matrix">
                  <thead>
                    <tr>
                      <th>Measure</th>
                      {availableScopes.map((scope) => (
                        <th key={scope.id} title={scope.tab}>
                          {scope.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {availableMeasures.map((measure) => (
                      <tr key={measure.id}>
                        <td>
                          <label className="matrix-checkbox-label">
                            <input
                              type="checkbox"
                              checked={selectedMeasures.includes(measure.id)}
                              onChange={() => handleMeasureToggle(measure.id)}
                            />
                            <span>{measure.label}</span>
                          </label>
                        </td>
                        {availableScopes.map((scope) => (
                          <td key={scope.id}>
                            <input
                              type="checkbox"
                              checked={selectedMeasures.includes(measure.id) && (measureScopes[measure.id] || []).includes(scope.id)}
                              onChange={() => handleScopeToggle('measure', measure.id, scope.id)}
                              disabled={!selectedMeasures.includes(measure.id)}
                              className="scope-checkbox"
                            />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Scope Matrix for Dimensions */}
            <div className="form-group">
              <label>Dimensions (Optional)</label>
              <div className="scope-matrix-container">
                <table className="scope-matrix">
                  <thead>
                    <tr>
                      <th>Dimension</th>
                      {availableScopes.map((scope) => (
                        <th key={scope.id} title={scope.tab}>
                          {scope.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {availableDimensions.map((dimension) => (
                      <tr key={dimension.id}>
                        <td>
                          <label className="matrix-checkbox-label">
                            <input
                              type="checkbox"
                              checked={selectedDimensions.includes(dimension.id)}
                              onChange={() => handleDimensionToggle(dimension.id)}
                            />
                            <span>{dimension.label}</span>
                          </label>
                        </td>
                        {availableScopes.map((scope) => (
                          <td key={scope.id}>
                            <input
                              type="checkbox"
                              checked={selectedDimensions.includes(dimension.id) && (dimensionScopes[dimension.id] || []).includes(scope.id)}
                              onChange={() => handleScopeToggle('dimension', dimension.id, scope.id)}
                              disabled={!selectedDimensions.includes(dimension.id)}
                              className="scope-checkbox"
                            />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <button
              onClick={handleSaveClick}
              disabled={loading || !reportName.trim() || !selectedStructure}
              className="save-button"
            >
              {loading ? 'Saving...' : editingReportId ? 'Update Report' : 'Save Report'}
            </button>
          </div>
        </div>
      )}

      {showConfirmation && confirmationData && (
        <div className="modal-overlay" onClick={() => setShowConfirmation(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Confirm {confirmationData.isEdit ? 'Update' : 'Registration'}</h3>
            <div className="confirmation-summary">
              <p>
                Registering <strong>{confirmationData.reportName}</strong> with <strong>{confirmationData.measureCount}</strong> Measure(s) and <strong>{confirmationData.dimensionCount}</strong> Dimension(s).
              </p>
              <p>
                Using the <strong>{confirmationData.structureName}</strong> hierarchy.
              </p>
              <p className="confirmation-question">Continue?</p>
            </div>
            <div className="modal-actions">
              <button onClick={() => setShowConfirmation(false)} className="cancel-button">
                Cancel
              </button>
              <button onClick={handleConfirmSave} className="confirm-button">
                {confirmationData.isEdit ? 'Update' : 'Continue'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ReportRegistrationScreen
