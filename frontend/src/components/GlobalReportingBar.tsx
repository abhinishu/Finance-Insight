/**
 * GlobalReportingBar - Global reporting controls visible across all tabs
 * Step 4.3: Includes PNL date selector, comparison mode toggle, and run selectors
 */

import React, { useState, useEffect } from 'react'
import { useReportingContext } from '../contexts/ReportingContext'
import axios from 'axios'
import './GlobalReportingBar.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface Run {
  id: string
  run_name: string
  executed_at: string
  status: string
}

const GlobalReportingBar: React.FC = () => {
  const {
    selectedPnlDate,
    setSelectedPnlDate,
    selectedUseCaseId,
    isComparisonMode,
    setIsComparisonMode,
    selectedRunId,
    setSelectedRunId,
    baselineRunId,
    setBaselineRunId,
    targetRunId,
    setTargetRunId,
    latestPnlDate,
    loadingDefaults,
  } = useReportingContext()
  
  const [availableRuns, setAvailableRuns] = useState<Run[]>([])
  const [loadingRuns, setLoadingRuns] = useState<boolean>(false)
  
  // Load runs when date or use case changes
  useEffect(() => {
    if (selectedPnlDate && selectedUseCaseId) {
      loadRunsForDate()
    } else {
      setAvailableRuns([])
    }
  }, [selectedPnlDate, selectedUseCaseId])
  
  const loadRunsForDate = async () => {
    if (!selectedPnlDate || !selectedUseCaseId) return
    
    setLoadingRuns(true)
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/runs?pnl_date=${selectedPnlDate}&use_case_id=${selectedUseCaseId}`
      )
      setAvailableRuns(response.data.runs || [])
    } catch (error: any) {
      console.error('Failed to load runs:', error)
      setAvailableRuns([])
    } finally {
      setLoadingRuns(false)
    }
  }
  
  return (
    <div className="global-reporting-bar">
      <div className="reporting-bar-left">
        {/* PNL Date Selector */}
        <div className="reporting-control-group">
          <label htmlFor="pnl-date-select">PNL Date:</label>
          <input
            id="pnl-date-select"
            type="date"
            value={selectedPnlDate || ''}
            onChange={(e) => setSelectedPnlDate(e.target.value || null)}
            className="date-input"
            disabled={loadingDefaults}
          />
          {latestPnlDate && selectedPnlDate === latestPnlDate && (
            <span className="latest-badge" title="Latest available date">Latest</span>
          )}
        </div>
        
        {/* Comparison Mode Toggle */}
        <div className="reporting-control-group">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={isComparisonMode}
              onChange={(e) => setIsComparisonMode(e.target.checked)}
              className="comparison-toggle"
            />
            <span>Comparison Mode</span>
          </label>
        </div>
      </div>
      
      <div className="reporting-bar-right">
        {isComparisonMode ? (
          /* Dual Run Selectors - Comparison Mode */
          <>
            <div className="reporting-control-group">
              <label htmlFor="baseline-run-select">Baseline Run:</label>
              <select
                id="baseline-run-select"
                value={baselineRunId || ''}
                onChange={(e) => setBaselineRunId(e.target.value || null)}
                className="run-select"
                disabled={loadingRuns || !selectedPnlDate || !selectedUseCaseId}
              >
                <option value="">Select baseline...</option>
                {availableRuns.map(run => (
                  <option key={run.id} value={run.id}>
                    {run.run_name} - {new Date(run.executed_at).toLocaleString()}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="reporting-control-group">
              <label htmlFor="target-run-select">Target Run:</label>
              <select
                id="target-run-select"
                value={targetRunId || ''}
                onChange={(e) => setTargetRunId(e.target.value || null)}
                className="run-select"
                disabled={loadingRuns || !selectedPnlDate || !selectedUseCaseId}
              >
                <option value="">Select target...</option>
                {availableRuns.map(run => (
                  <option key={run.id} value={run.id}>
                    {run.run_name} - {new Date(run.executed_at).toLocaleString()}
                  </option>
                ))}
              </select>
            </div>
          </>
        ) : (
          /* Single Run Selector - Standard Mode */
          <div className="reporting-control-group">
            <label htmlFor="run-select">Run:</label>
            <select
              id="run-select"
              value={selectedRunId || ''}
              onChange={(e) => setSelectedRunId(e.target.value || null)}
              className="run-select"
              disabled={loadingRuns || !selectedPnlDate || !selectedUseCaseId}
            >
              <option value="">Select run...</option>
              {availableRuns.map(run => (
                <option key={run.id} value={run.id}>
                  {run.run_name} - {new Date(run.executed_at).toLocaleString()}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
    </div>
  )
}

export default GlobalReportingBar



