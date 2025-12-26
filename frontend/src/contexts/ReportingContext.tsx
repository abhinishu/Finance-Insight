/**
 * ReportingContext - Global state for reporting configuration
 * Step 4.3: Manages PNL date, run selection, and comparison mode across all tabs
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface ReportingContextType {
  // Date Selection
  selectedPnlDate: string | null
  setSelectedPnlDate: (date: string | null) => void
  
  // Use Case Selection
  selectedUseCaseId: string | null
  setSelectedUseCaseId: (id: string | null) => void
  
  // Run Selection (Single Mode)
  selectedRunId: string | null
  setSelectedRunId: (id: string | null) => void
  
  // Comparison Mode
  isComparisonMode: boolean
  setIsComparisonMode: (enabled: boolean) => void
  
  // Comparison Runs
  baselineRunId: string | null
  setBaselineRunId: (id: string | null) => void
  targetRunId: string | null
  setTargetRunId: (id: string | null) => void
  
  // Latest Defaults
  latestPnlDate: string | null
  latestRunId: string | null
  
  // Loading State
  loadingDefaults: boolean
}

const ReportingContext = createContext<ReportingContextType | undefined>(undefined)

export const useReportingContext = () => {
  const context = useContext(ReportingContext)
  if (!context) {
    throw new Error('useReportingContext must be used within ReportingProvider')
  }
  return context
}

interface ReportingProviderProps {
  children: ReactNode
  useCaseId?: string | null  // Optional initial use case
}

export const ReportingProvider: React.FC<ReportingProviderProps> = ({ 
  children, 
  useCaseId: initialUseCaseId = null 
}) => {
  // State
  const [selectedPnlDate, setSelectedPnlDate] = useState<string | null>(null)
  const [selectedUseCaseId, setSelectedUseCaseId] = useState<string | null>(initialUseCaseId)
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [isComparisonMode, setIsComparisonMode] = useState<boolean>(false)
  const [baselineRunId, setBaselineRunId] = useState<string | null>(null)
  const [targetRunId, setTargetRunId] = useState<string | null>(null)
  
  // Latest Defaults
  const [latestPnlDate, setLatestPnlDate] = useState<string | null>(null)
  const [latestRunId, setLatestRunId] = useState<string | null>(null)
  const [loadingDefaults, setLoadingDefaults] = useState<boolean>(true)
  
  // Global P&L Totals (shared across all tabs)
  const [globalTotal, setGlobalTotal] = useState<{
    daily_pnl: number | null
    mtd_pnl: number | null
    ytd_pnl: number | null
  } | null>(null)
  
  // Load latest defaults on mount
  useEffect(() => {
    const loadLatestDefaults = async () => {
      setLoadingDefaults(true)
      try {
        const url = selectedUseCaseId 
          ? `${API_BASE_URL}/api/v1/runs/latest/defaults?use_case_id=${selectedUseCaseId}`
          : `${API_BASE_URL}/api/v1/runs/latest/defaults`
        
        const response = await axios.get(url)
        const data = response.data
        
        if (data.pnl_date) {
          setLatestPnlDate(data.pnl_date)
          setSelectedPnlDate(data.pnl_date)
        }
        
        if (data.run_id) {
          setLatestRunId(data.run_id)
          if (!selectedRunId && !isComparisonMode) {
            setSelectedRunId(data.run_id)
          }
        }
      } catch (error: any) {
        console.error('Failed to load latest defaults:', error)
        // Non-fatal - continue without defaults
      } finally {
        setLoadingDefaults(false)
      }
    }
    
    loadLatestDefaults()
  }, [selectedUseCaseId])  // Reload when use case changes
  
  // Reset comparison runs when comparison mode is disabled
  useEffect(() => {
    if (!isComparisonMode) {
      setBaselineRunId(null)
      setTargetRunId(null)
    }
  }, [isComparisonMode])
  
  // Reset single run when comparison mode is enabled
  useEffect(() => {
    if (isComparisonMode) {
      setSelectedRunId(null)
    }
  }, [isComparisonMode])
  
  // Reset globalTotal when use case changes
  useEffect(() => {
    setGlobalTotal(null)
  }, [selectedUseCaseId])
  
  const value: ReportingContextType = {
    selectedPnlDate,
    setSelectedPnlDate,
    selectedUseCaseId,
    setSelectedUseCaseId,
    selectedRunId,
    setSelectedRunId,
    isComparisonMode,
    setIsComparisonMode,
    baselineRunId,
    setBaselineRunId,
    targetRunId,
    setTargetRunId,
    latestPnlDate,
    latestRunId,
    loadingDefaults,
    globalTotal,
    setGlobalTotal,
  }
  
  return (
    <ReportingContext.Provider value={value}>
      {children}
    </ReportingContext.Provider>
  )
}

