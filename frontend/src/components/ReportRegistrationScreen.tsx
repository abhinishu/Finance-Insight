import React, { useState, useEffect } from 'react'
import axios from 'axios'
import './ReportRegistrationScreen.css'

interface Structure {
  structure_id: string
  name: string
  node_count: number
}

// Removed unused interfaces - ReportRegistration and Scope no longer needed

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const ReportRegistrationScreen: React.FC = () => {
  const [viewMode, setViewMode] = useState<'list' | 'form'>('list')
  const [editingUseCaseId, setEditingUseCaseId] = useState<string | null>(null)
  
  const [useCaseName, setUseCaseName] = useState<string>('')
  const [useCaseDescription, setUseCaseDescription] = useState<string>('')
  const [selectedStructure, setSelectedStructure] = useState<string>('')
  const [availableStructures, setAvailableStructures] = useState<Structure[]>([])
  
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [showConfirmation, setShowConfirmation] = useState<boolean>(false)
  const [confirmationData, setConfirmationData] = useState<any>(null)
  
  // Step 4.3: Admin - Use Case Management
  const [useCases, setUseCases] = useState<any[]>([])
  const [useCaseToDelete, setUseCaseToDelete] = useState<any>(null)
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState<boolean>(false)
  const [deleteSummary, setDeleteSummary] = useState<any>(null)
  const [showDeleteToast, setShowDeleteToast] = useState<boolean>(false)
  
  // Step 4.4: Metadata export state
  const [exportingMetadata, setExportingMetadata] = useState<boolean>(false)
  const [exportSuccess, setExportSuccess] = useState<string | null>(null)

  // Removed measures, dimensions, and scopes - not needed for use case creation

  // Step 4.3: Load use cases on mount
  useEffect(() => {
    loadUseCases()
  }, [])
  
  // Load available structures
  useEffect(() => {
    const loadStructures = async () => {
      try {
        console.log('Tab 1: Loading structures from:', `${API_BASE_URL}/api/v1/structures`)
        const response = await axios.get<{ structures: Structure[] }>(
          `${API_BASE_URL}/api/v1/structures`
        )
        console.log('Tab 1: Structures API response:', response.data)
        const structures = response.data?.structures || []
        console.log('Tab 1: Found', structures.length, 'structures')
        setAvailableStructures(structures)
        if (structures.length > 0 && !selectedStructure) {
          console.log('Tab 1: Auto-selecting first structure:', structures[0].structure_id)
          setSelectedStructure(structures[0].structure_id)
        } else if (structures.length === 0) {
          console.warn('Tab 1: No structures found')
          setError('No structures available. Please ensure mock data has been generated.')
        }
      } catch (err: any) {
        console.error('Tab 1: Failed to load structures:', err)
        console.error('Tab 1: Error details:', err.response?.data || err.message)
        setError(`Failed to load available structures: ${err.response?.data?.detail || err.message}`)
      }
    }
    loadStructures()
  }, [])

  // Step 4.3: Load use cases for admin deletion
  const loadUseCases = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/use-cases`)
      const useCasesList = response.data.use_cases || []
      // Filter out any use cases that might have been deleted (defensive check)
      setUseCases(useCasesList)
      console.log('TAB 1: Loaded', useCasesList.length, 'use cases')
    } catch (err: any) {
      console.error('Failed to load use cases:', err)
      setUseCases([]) // Clear on error
      // Non-fatal error - continue without use cases
    }
  }
  
  // Step 4.4: Export metadata
  const handleExportMetadata = async () => {
    setExportingMetadata(true)
    setExportSuccess(null)
    setError(null)
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/v1/admin/export-metadata`)
      const result = response.data
      
      setExportSuccess(
        `Metadata exported successfully! ${result.total_entries} entries exported to ${result.export_path}`
      )
      
      // Auto-hide success message after 5 seconds
      setTimeout(() => {
        setExportSuccess(null)
      }, 5000)
    } catch (err: any) {
      console.error('Failed to export metadata:', err)
      setError(err.response?.data?.detail || 'Failed to export metadata')
    } finally {
      setExportingMetadata(false)
    }
  }
  
  // Step 4.3: Show delete confirmation modal
  const handleDeleteClick = (useCase: any) => {
    setUseCaseToDelete(useCase)
    setShowDeleteConfirmation(true)
  }

  // Step 4.4: Delete use case with summary (enhanced to show modal instead of toast)
  const handleConfirmDeleteUseCase = async () => {
    if (!useCaseToDelete) {
      return
    }
    
    setLoading(true)
    setError(null)
    setShowDeleteConfirmation(false)
    
    try {
      const response = await axios.delete(`${API_BASE_URL}/api/v1/admin/use-case/${useCaseToDelete.use_case_id}`)
      const summary = response.data
      
      // Step 4.4: Show summary in prominent modal instead of toast
      setDeleteSummary(summary)
      setShowDeleteToast(true) // Reusing this state name but it's now a modal
      
      // Clear selection first
      const deletedId = useCaseToDelete.use_case_id
      setUseCaseToDelete(null)
      
      // Refresh use cases list immediately
      await loadUseCases()
      
      // Trigger a custom event to notify other tabs to refresh
      window.dispatchEvent(new CustomEvent('useCaseDeleted', { 
        detail: { useCaseId: deletedId } 
      }))
      
    } catch (err: any) {
      console.error('Failed to delete use case:', err)
      setError(err.response?.data?.detail || 'Failed to delete use case.')
    } finally {
      setLoading(false)
    }
  }
  
  // No longer need to load reports - only use cases

  // Removed scope-related functions - no longer needed for use cases

  const handleCreateNew = () => {
    setViewMode('form')
    setEditingUseCaseId(null)
    setUseCaseName('')
    setUseCaseDescription('')
    setSelectedStructure('')
    setError(null)
    setSuccess(null)
  }

  const handleEdit = async (useCaseId: string) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/use-cases/${useCaseId}`
      )
      const useCase = response.data
      
      setEditingUseCaseId(useCaseId)
      setUseCaseName(useCase.name)
      setUseCaseDescription(useCase.description || '')
      setSelectedStructure(useCase.atlas_structure_id)
      setViewMode('form')
      setError(null)
      setSuccess(null)
    } catch (err: any) {
      setError('Failed to load use case for editing')
      console.error(err)
    }
  }

  const handleSaveClick = () => {
    // Prepare confirmation data
    const structureName = availableStructures.find(s => s.structure_id === selectedStructure)?.name || selectedStructure
    
    setConfirmationData({
      useCaseName,
      structureName,
      isEdit: !!editingUseCaseId
    })
    setShowConfirmation(true)
  }

  const handleConfirmSave = async () => {
    setShowConfirmation(false)
    
    if (!useCaseName.trim()) {
      setError('Please enter a use case name')
      return
    }

    if (!editingUseCaseId && !selectedStructure) {
      setError('Please select an Atlas structure')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      if (editingUseCaseId) {
        // Step 4.4: Update existing use case - only name and description allowed
        const params = new URLSearchParams()
        params.append('name', useCaseName)
        if (useCaseDescription !== undefined) {
          params.append('description', useCaseDescription || '')
        }
        
        await axios.put(
          `${API_BASE_URL}/api/v1/use-cases/${editingUseCaseId}?${params.toString()}`
        )
        setSuccess(`Use case "${useCaseName}" updated successfully!`)
        
        // Trigger event to notify other tabs
        window.dispatchEvent(new CustomEvent('useCaseUpdated', { 
          detail: { useCaseId: editingUseCaseId } 
        }))
      } else {
        // Create new use case - use query parameters as per API
        const params = new URLSearchParams()
        params.append('name', useCaseName)
        if (useCaseDescription) {
          params.append('description', useCaseDescription)
        }
        params.append('atlas_structure_id', selectedStructure)
        params.append('owner_id', 'current_user')
        
        await axios.post(
          `${API_BASE_URL}/api/v1/use-cases?${params.toString()}`
        )
        setSuccess(`Use case "${useCaseName}" created successfully!`)
        
        // Trigger event to notify other tabs
        window.dispatchEvent(new CustomEvent('useCaseCreated', {}))
      }

      // Reset form
      handleCreateNew()
      
      // Reload use cases list
      await loadUseCases()
      
      // Switch back to list view after a delay
      setTimeout(() => {
        setViewMode('list')
      }, 1500)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to save use case'
      setError(errorMsg)
      console.error('Save error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="report-registration-screen">
      {viewMode === 'list' ? (
        <div className="report-library-container">
          <div className="library-header">
            <h2>Use Cases</h2>
            <button onClick={handleCreateNew} className="create-new-button">
              + Create Use Case
            </button>
          </div>

          {/* Use Cases Section */}
          <div style={{ marginBottom: '2rem' }}>
            <h3 style={{ marginBottom: '1rem', color: '#1f2937' }}>Use Cases</h3>
            {useCases.length === 0 ? (
              <div className="empty-state" style={{ padding: '2rem', textAlign: 'center', background: '#f9fafb', borderRadius: '8px' }}>
                <p>No use cases found</p>
              </div>
            ) : (
              <div className="reports-table-container">
                <table className="reports-table">
                  <thead>
                    <tr>
                      <th>Use Case Name</th>
                      <th>Description</th>
                      <th>Status</th>
                      <th>Created Date</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {useCases.map((useCase) => (
                      <tr key={useCase.use_case_id}>
                        <td>{useCase.name}</td>
                        <td>{useCase.description || '-'}</td>
                        <td>
                          <span className="status-badge">{useCase.status || 'ACTIVE'}</span>
                        </td>
                        <td>{useCase.created_at ? new Date(useCase.created_at).toLocaleDateString() : '-'}</td>
                        <td>
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button
                              onClick={() => handleEdit(useCase.use_case_id)}
                              className="edit-button"
                              style={{ padding: '0.25rem 0.75rem', fontSize: '0.875rem' }}
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => {
                                // Toggle active status
                                setError('Active toggle functionality coming soon')
                              }}
                              className="edit-button"
                              style={{ padding: '0.25rem 0.75rem', fontSize: '0.875rem' }}
                            >
                              {useCase.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
                            </button>
                            <button
                              onClick={() => handleDeleteClick(useCase)}
                              className="danger-button"
                              style={{ 
                                padding: '0.25rem 0.75rem', 
                                fontSize: '0.875rem',
                                background: '#ef4444',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer'
                              }}
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Step 4.4: Admin - Metadata Management */}
          <div style={{ 
            marginTop: '3rem', 
            padding: '1.5rem', 
            background: '#f9fafb', 
            borderRadius: '8px',
            border: '1px solid #e5e7eb'
          }}>
            <h3 style={{ marginBottom: '1rem', color: '#1f2937' }}>Admin: Metadata Management</h3>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <button
                onClick={handleExportMetadata}
                disabled={exportingMetadata}
                style={{
                  padding: '0.75rem 1.5rem',
                  background: exportingMetadata ? '#9ca3af' : '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                  fontWeight: '600',
                  cursor: exportingMetadata ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                {exportingMetadata ? (
                  <>
                    <span>⏳</span> Exporting...
                  </>
                ) : (
                  <>
                    <span>📥</span> Export Metadata
                  </>
                )}
              </button>
              {exportSuccess && (
                <div style={{ 
                  padding: '0.5rem 1rem', 
                  background: '#d1fae5', 
                  border: '1px solid #10b981',
                  borderRadius: '4px',
                  color: '#065f46',
                  fontSize: '0.875rem'
                }}>
                  ✓ {exportSuccess}
                </div>
              )}
            </div>
            <p style={{ 
              marginTop: '0.75rem', 
              fontSize: '0.8125rem', 
              color: '#6b7280',
              fontStyle: 'italic'
            }}>
              Exports dictionary definitions to <code>/metadata/backups/</code> for environment synchronization.
            </p>
          </div>

          {/* Step 4.4: Deletion Summary Modal (Prominent Alert) */}
          {showDeleteToast && deleteSummary && (
            <div 
              className="modal-overlay" 
              onClick={() => {
                setShowDeleteToast(false)
                setDeleteSummary(null)
              }}
              style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: 'rgba(0, 0, 0, 0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 2000
              }}
            >
              <div 
                className="modal-content" 
                onClick={(e) => e.stopPropagation()}
                style={{
                  background: 'white',
                  borderRadius: '8px',
                  padding: '2rem',
                  maxWidth: '600px',
                  width: '90%',
                  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
                  border: '2px solid #dc2626'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                  <h2 style={{ color: '#dc2626', margin: 0, fontSize: '1.5rem' }}>
                    ⚠️ Deletion Summary
                  </h2>
                  <button
                    onClick={() => {
                      setShowDeleteToast(false)
                      setDeleteSummary(null)
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      fontSize: '1.5rem',
                      cursor: 'pointer',
                      color: '#6b7280',
                      padding: '0',
                      lineHeight: '1'
                    }}
                  >
                    ×
                  </button>
                </div>
                
                <div style={{ 
                  background: '#fef2f2', 
                  border: '1px solid #fecaca', 
                  borderRadius: '6px', 
                  padding: '1.5rem',
                  marginBottom: '1.5rem'
                }}>
                  <p style={{ marginBottom: '1rem', fontSize: '1.1rem', fontWeight: '600', color: '#991b1b' }}>
                    Use case <strong>{deleteSummary.deleted_use_case}</strong> has been permanently deleted.
                  </p>
                  
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: '1fr 1fr', 
                    gap: '1rem',
                    marginTop: '1rem'
                  }}>
                    <div style={{ padding: '0.75rem', background: 'white', borderRadius: '4px', border: '1px solid #fecaca' }}>
                      <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Rules Purged</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#dc2626' }}>
                        {deleteSummary.rules_purged || 0}
                      </div>
                    </div>
                    <div style={{ padding: '0.75rem', background: 'white', borderRadius: '4px', border: '1px solid #fecaca' }}>
                      <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Legacy Runs Purged</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#dc2626' }}>
                        {deleteSummary.legacy_runs_purged || 0}
                      </div>
                    </div>
                    <div style={{ padding: '0.75rem', background: 'white', borderRadius: '4px', border: '1px solid #fecaca' }}>
                      <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Calculation Runs Purged</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#dc2626' }}>
                        {deleteSummary.calculation_runs_purged || 0}
                      </div>
                    </div>
                    <div style={{ padding: '0.75rem', background: 'white', borderRadius: '4px', border: '1px solid #fecaca' }}>
                      <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Facts Purged</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: '700', color: '#dc2626' }}>
                        {deleteSummary.facts_purged || 0}
                      </div>
                    </div>
                  </div>
                  
                  <div style={{ 
                    marginTop: '1.5rem', 
                    padding: '1rem', 
                    background: '#dc2626', 
                    borderRadius: '4px',
                    textAlign: 'center'
                  }}>
                    <div style={{ fontSize: '0.875rem', color: 'white', marginBottom: '0.25rem' }}>Total Items Deleted</div>
                    <div style={{ fontSize: '2rem', fontWeight: '700', color: 'white' }}>
                      {deleteSummary.total_items_deleted || 0}
                    </div>
                  </div>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    onClick={() => {
                      setShowDeleteToast(false)
                      setDeleteSummary(null)
                    }}
                    style={{
                      padding: '0.75rem 1.5rem',
                      background: '#dc2626',
                      color: 'white',
                      border: 'none',
                      borderRadius: '6px',
                      fontSize: '1rem',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    Acknowledge
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="registration-container">
          <div className="form-header">
            <h2>{editingUseCaseId ? 'Edit Use Case' : 'Create Use Case'}</h2>
            <button onClick={() => setViewMode('list')} className="back-button">
              ← Back to Use Cases
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
              <label htmlFor="use-case-name">Use Case Name *</label>
              <input
                id="use-case-name"
                type="text"
                value={useCaseName}
                onChange={(e) => setUseCaseName(e.target.value)}
                placeholder="e.g., Americas Trading P&L"
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="use-case-description">Description (Optional)</label>
              <textarea
                id="use-case-description"
                value={useCaseDescription}
                onChange={(e) => setUseCaseDescription(e.target.value)}
                placeholder="Enter a description for this use case..."
                className="form-input"
                rows={3}
              />
            </div>

            <div className="form-group">
              <label htmlFor="structure-select">
                Atlas Structure *
                {editingUseCaseId && (
                  <span style={{ 
                    marginLeft: '0.5rem', 
                    fontSize: '0.75rem', 
                    color: '#6b7280',
                    fontStyle: 'italic'
                  }}>
                    (Cannot be changed after creation)
                  </span>
                )}
              </label>
              <select
                id="structure-select"
                value={selectedStructure}
                onChange={(e) => setSelectedStructure(e.target.value)}
                className="form-select"
                disabled={loading || availableStructures.length === 0 || !!editingUseCaseId}
                style={editingUseCaseId ? { 
                  backgroundColor: '#f3f4f6', 
                  cursor: 'not-allowed',
                  color: '#6b7280'
                } : {}}
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

            <button
              onClick={handleSaveClick}
              disabled={loading || !useCaseName.trim() || !selectedStructure}
              className="save-button"
            >
              {loading ? 'Saving...' : editingUseCaseId ? 'Update Use Case' : 'Create Use Case'}
            </button>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirmation && useCaseToDelete && (
        <div className="modal-overlay" onClick={() => setShowDeleteConfirmation(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3 style={{ color: '#dc2626', marginBottom: '1rem' }}>Confirm Deletion</h3>
            <div className="confirmation-summary">
              <p style={{ marginBottom: '1rem' }}>
                Are you sure you want to delete the use case <strong>{useCaseToDelete.name}</strong>?
              </p>
              <p style={{ marginBottom: '1rem', color: '#dc2626', fontWeight: '600' }}>
                This action cannot be undone and will permanently delete:
              </p>
              <ul style={{ marginLeft: '1.5rem', marginBottom: '1rem', color: '#6b7280' }}>
                <li>All associated business rules</li>
                <li>All calculation runs</li>
                <li>All P&L fact entries</li>
                <li>All related data</li>
              </ul>
              <p className="confirmation-question" style={{ marginTop: '1rem' }}>Do you want to proceed?</p>
            </div>
            <div className="modal-actions">
              <button 
                onClick={() => {
                  setShowDeleteConfirmation(false)
                  setUseCaseToDelete(null)
                }} 
                className="cancel-button"
                disabled={loading}
              >
                Cancel
              </button>
              <button 
                onClick={handleConfirmDeleteUseCase} 
                className="danger-button"
                disabled={loading}
                style={{
                  background: '#dc2626',
                  color: 'white',
                  border: 'none',
                  padding: '0.5rem 1.5rem',
                  borderRadius: '4px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.6 : 1
                }}
              >
                {loading ? 'Deleting...' : 'Delete Use Case'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showConfirmation && confirmationData && (
        <div className="modal-overlay" onClick={() => setShowConfirmation(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Confirm {confirmationData.isEdit ? 'Update' : 'Registration'}</h3>
            <div className="confirmation-summary">
              <p>
                {confirmationData.isEdit ? 'Updating' : 'Creating'} use case <strong>{confirmationData.useCaseName}</strong>.
              </p>
              <p>
                Using the <strong>{confirmationData.structureName}</strong> Atlas Structure.
              </p>
              <p className="confirmation-question">Continue?</p>
            </div>
            <div className="modal-actions">
              <button onClick={() => setShowConfirmation(false)} className="cancel-button">
                Cancel
              </button>
              <button onClick={handleConfirmSave} className="confirm-button">
                {confirmationData.isEdit ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ReportRegistrationScreen
