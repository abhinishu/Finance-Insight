import React, { useMemo, useState } from 'react'
import { AttributionItem } from '../utils/pnlAttribution'

interface PnlWaterfallChartProps {
  attributionData: AttributionItem[]
  originalPnl: number
  adjustedPnl: number
  rootNodeName?: string
  onBarClick?: (ruleName: string) => void
}

/**
 * Format currency in compact form with higher precision for millions (e.g., "$1.203M", "$50k", "$100")
 */
const formatCurrencyCompact = (value: number): string => {
  const absValue = Math.abs(value)
  const sign = value < 0 ? '-' : ''
  
  if (absValue >= 1000000) {
    // Show 3 decimal places for millions for better accuracy (e.g., "$1.203M" instead of "$1.2M")
    return `${sign}$${(absValue / 1000000).toFixed(3)}M`
  } else if (absValue >= 1000) {
    return `${sign}$${(absValue / 1000).toFixed(0)}k`
  } else {
    return `${sign}$${absValue.toFixed(0)}`
  }
}

/**
 * Truncate label to maxLength with ellipsis
 */
const truncateLabel = (label: string, maxLength: number = 15): string => {
  if (label.length <= maxLength) return label
  return label.substring(0, maxLength - 3) + '...'
}

/**
 * Determine rule type from rule name
 */
const getRuleType = (ruleName: string): 'Manual Override' | 'Logic Adjustment' => {
  if (ruleName.toLowerCase().includes('override') || ruleName.toLowerCase().includes('manual')) {
    return 'Manual Override'
  }
  return 'Logic Adjustment'
}

/**
 * P&L Waterfall Chart Component
 * Visualizes the "bridge" from Original P&L to Adjusted P&L
 * Shows each rule's impact as a step in the waterfall
 */
const PnlWaterfallChart: React.FC<PnlWaterfallChartProps> = ({
  attributionData,
  originalPnl,
  adjustedPnl,
  rootNodeName = 'Global Trading P&L',
  onBarClick
}) => {
  const [hoveredBar, setHoveredBar] = useState<number | null>(null)
  const [tooltip, setTooltip] = useState<{ 
    x: number
    y: number
    ruleName: string
    fullRuleName: string
    value: number
    contribution: number
    ruleType: 'Manual Override' | 'Logic Adjustment'
  } | null>(null)
  
  // Calculate total adjustment for contribution percentage
  const totalAdjustment = useMemo(() => {
    return Math.abs(adjustedPnl - originalPnl)
  }, [originalPnl, adjustedPnl])
  // Build waterfall data structure
  const waterfallData = useMemo(() => {
    const steps: Array<{
      name: string
      fullName: string
      value: number
      start: number
      end: number
      color: string
      type: 'start' | 'step' | 'end'
    }> = []
    
    let currentValue = originalPnl
    
    // Add original P&L as starting point
    steps.push({
      name: 'Original P&L',
      fullName: 'Original P&L',
      value: originalPnl,
      start: 0,
      end: originalPnl,
      color: '#1e3a8a', // Navy Blue
      type: 'start'
    })
    
    // Add each rule's impact as a step
    attributionData.forEach((item) => {
      const start = currentValue
      const end = currentValue + item.impact
      const color = item.impact >= 0 ? '#10b981' : '#ef4444' // Green for positive, red for negative
      
      steps.push({
        name: truncateLabel(item.ruleName, 15), // Truncated for X-axis
        fullName: item.ruleName, // Full name for tooltip
        value: item.impact,
        start: start,
        end: end,
        color: color,
        type: 'step'
      })
      
      currentValue = end
    })
    
    // Add final adjusted P&L
    steps.push({
      name: 'Adjusted P&L',
      fullName: 'Adjusted P&L',
      value: adjustedPnl,
      start: 0,
      end: adjustedPnl,
      color: '#374151', // Dark Gray
      type: 'end'
    })
    
    return steps
  }, [attributionData, originalPnl, adjustedPnl])
  
  // Format currency for tooltip (full precision with sign)
  const formatCurrencyFull = (value: number): string => {
    const isNegative = value < 0
    const absValue = Math.abs(value)
    const formatted = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(absValue)
    return isNegative ? `-$${formatted}` : `+$${formatted}`
  }
  
  // Format simplified numbers for Y-axis (e.g., "$5M", "$500k")
  const formatAxisLabel = (value: number): string => {
    return formatCurrencyCompact(value)
  }
  
  // Calculate chart dimensions
  let runningTotal = originalPnl
  const allValues = [originalPnl, adjustedPnl]
  attributionData.forEach(item => {
    runningTotal += item.impact
    allValues.push(runningTotal)
  })
  
  // Ensure 0 is at the bottom - set minValue to 0 or below
  const maxValue = Math.max(...allValues) * 1.1 // Add 10% padding
  const minValue = Math.min(0, Math.min(...allValues) * 1.1) // Ensure we show below zero if needed
  // Force 0 to be at bottom by ensuring minValue is <= 0
  const adjustedMinValue = Math.min(0, minValue)
  const chartHeight = 400
  const barWidth = 80
  const barSpacing = 20
  const chartWidth = Math.max(800, (waterfallData.length - 1) * (barWidth + barSpacing) + 200)
  const valueRange = maxValue - adjustedMinValue
  const scale = valueRange > 0 ? chartHeight / valueRange : 1
  const zeroY = chartHeight - (0 - adjustedMinValue) * scale // Y position of zero line
  const xAxisY = chartHeight + 20 // Y position for X-axis labels
  const labelRotation = -45 // Rotate labels -45 degrees for readability
  
  return (
    <div style={{
      padding: '1.5rem',
      backgroundColor: 'white',
      borderRadius: '8px',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      marginTop: '1.5rem'
    }}>
      <h3 style={{ marginBottom: '0.5rem', color: '#1f2937', fontSize: '1.25rem', fontWeight: '600' }}>
        Impact Bridge: {rootNodeName} (Top Level)
      </h3>
      <p style={{ marginBottom: '1.5rem', color: '#6b7280', fontSize: '0.875rem' }}>
        Visual walk from Original P&L to Adjusted P&L showing each rule's impact. Click a bar to drill down.
      </p>
      
      {/* Simple SVG-based Waterfall Chart */}
      <div style={{ overflowX: 'auto', marginBottom: '1rem' }}>
        <svg width={chartWidth} height={chartHeight + 200} style={{ border: '1px solid #e5e7eb' }}>
          {/* Zero line (highlighted) */}
          <line
            x1={0}
            y1={zeroY}
            x2={chartWidth}
            y2={zeroY}
            stroke="#374151"
            strokeWidth={2}
            strokeDasharray="4,4"
          />
          
          {/* Grid lines with simplified labels */}
          {[0, 0.25, 0.5, 0.75, 1].map(ratio => {
            const value = adjustedMinValue + (maxValue - adjustedMinValue) * (1 - ratio)
            const y = chartHeight - (value - adjustedMinValue) * scale
            return (
              <g key={ratio}>
                <line
                  x1={0}
                  y1={y}
                  x2={chartWidth}
                  y2={y}
                  stroke={value === 0 ? "#374151" : "#e5e7eb"}
                  strokeWidth={value === 0 ? 2 : 1}
                  strokeDasharray="4,4"
                />
                <text
                  x={10}
                  y={y + 4}
                  fill={value === 0 ? "#374151" : "#6b7280"}
                  fontSize="11"
                  fontWeight={value === 0 ? "600" : "500"}
                >
                  {formatAxisLabel(value)}
                </text>
              </g>
            )
          })}
          
          {/* Waterfall bars */}
          {waterfallData.map((step, index) => {
            const x = 100 + index * (barWidth + barSpacing)
            const barHeight = Math.abs(step.value) * scale
            const yBase = chartHeight - (0 - minValue) * scale // Zero line
            const yTop = yBase - (step.value - minValue) * scale
            
            if (step.type === 'start' || step.type === 'end') {
              // Start (Original) or End (Adjusted) bars - full height from zero
              const y = step.value >= 0 ? (zeroY - barHeight) : zeroY
              const isHovered = hoveredBar === index
              return (
                <g key={index}>
                  <rect
                    x={x}
                    y={y}
                    width={barWidth}
                    height={barHeight}
                    fill={step.color}
                    opacity={isHovered ? 1 : 0.9}
                    rx={4}
                    style={{ cursor: 'default' }}
                  />
                  {/* X-axis label (rotated) */}
                  <text
                    x={x + barWidth / 2}
                    y={xAxisY + 30}
                    fill="#1f2937"
                    fontSize="10"
                    fontWeight="500"
                    textAnchor="end"
                    transform={`rotate(${labelRotation} ${x + barWidth / 2} ${xAxisY + 30})`}
                  >
                    {step.name}
                  </text>
                  {/* Value label - positioned above/below bar if too short */}
                  {barHeight > 25 ? (
                    // Inside bar if tall enough
                    <text
                      x={x + barWidth / 2}
                      y={step.value >= 0 ? y + barHeight / 2 : y + barHeight / 2}
                      fill="white"
                      fontSize="10"
                      fontWeight="700"
                      textAnchor="middle"
                      dominantBaseline="middle"
                    >
                      {formatCurrencyCompact(step.value)}
                    </text>
                  ) : (
                    // Above/below bar if too short
                    <text
                      x={x + barWidth / 2}
                      y={step.value >= 0 ? y - 8 : y + barHeight + 18}
                      fill={step.value >= 0 ? '#10b981' : '#ef4444'}
                      fontSize="10"
                      fontWeight="700"
                      textAnchor="middle"
                    >
                      {formatCurrencyCompact(step.value)}
                    </text>
                  )}
                </g>
              )
            } else {
              // Step (Rule Impact) - floating bar
              const prevStep = waterfallData[index - 1]
              const stepStart = prevStep.end
              const stepEnd = step.end
              const stepY = chartHeight - (stepStart - adjustedMinValue) * scale
              const stepHeight = Math.abs(step.value) * scale // Calculate height for step bars
              const isHovered = hoveredBar === index
              // Find the full rule name from attributionData
              const ruleIndex = index - 1 // Subtract 1 because first bar is "Original P&L"
              const fullRuleName = attributionData[ruleIndex]?.ruleName || step.fullName
              const ruleType = getRuleType(fullRuleName)
              
              return (
                <g key={index}>
                  {/* Bridge connector line */}
                  <line
                    x1={x - barSpacing}
                    y1={stepY}
                    x2={x}
                    y2={stepY}
                    stroke={step.color}
                    strokeWidth={2}
                    opacity={0.7}
                  />
                  {/* Impact bar (floating) - clickable */}
                  <rect
                    x={x}
                    y={step.value >= 0 ? stepY - stepHeight : stepY}
                    width={barWidth}
                    height={stepHeight}
                    fill={step.color}
                    opacity={isHovered ? 1 : 0.9}
                    rx={4}
                    style={{ cursor: onBarClick ? 'pointer' : 'default' }}
                    onMouseEnter={(e) => {
                      setHoveredBar(index)
                      // Calculate contribution percentage
                      const contribution = totalAdjustment > 0 
                        ? (Math.abs(step.value) / totalAdjustment) * 100 
                        : 0
                      // Position tooltip centered at the bottom of the chart
                      const tooltipX = chartWidth / 2 // Center of chart
                      const tooltipY = chartHeight + 60 // Position below the chart (below X-axis labels)
                      
                      setTooltip({
                        x: tooltipX,
                        y: tooltipY,
                        ruleName: truncateLabel(fullRuleName, 50), // Truncated for tooltip header
                        fullRuleName: fullRuleName, // Full name for tooltip body
                        value: step.value,
                        contribution,
                        ruleType
                      })
                    }}
                    onMouseLeave={() => {
                      setHoveredBar(null)
                      setTooltip(null)
                    }}
                    onClick={() => {
                      if (onBarClick) {
                        onBarClick(fullRuleName)
                      }
                    }}
                  />
                  {/* X-axis label (rotated) */}
                  <text
                    x={x + barWidth / 2}
                    y={xAxisY + 30}
                    fill="#1f2937"
                    fontSize="10"
                    fontWeight="500"
                    textAnchor="end"
                    transform={`rotate(${labelRotation} ${x + barWidth / 2} ${xAxisY + 30})`}
                  >
                    {step.name}
                  </text>
                  {/* Value label - positioned above/below bar if too short */}
                  {stepHeight > 25 ? (
                    // Inside bar if tall enough
                    <text
                      x={x + barWidth / 2}
                      y={step.value >= 0 ? stepY - stepHeight / 2 : stepY + stepHeight / 2}
                      fill="white"
                      fontSize="10"
                      fontWeight="700"
                      textAnchor="middle"
                      dominantBaseline="middle"
                    >
                      {formatCurrencyCompact(step.value)}
                    </text>
                  ) : (
                    // Above/below bar if too short
                    <text
                      x={x + barWidth / 2}
                      y={step.value >= 0 ? stepY - stepHeight - 8 : stepY + stepHeight + 18}
                      fill={step.value >= 0 ? '#10b981' : '#ef4444'}
                      fontSize="10"
                      fontWeight="700"
                      textAnchor="middle"
                    >
                      {formatCurrencyCompact(step.value)}
                    </text>
                  )}
                </g>
              )
            }
          })}
          
          {/* Enhanced Tooltip - Professional Style with Full Rule Logic */}
          {tooltip && (() => {
            const tooltipWidth = 300
            const tooltipHeight = 120
            // Position tooltip centered at the bottom of the chart
            const tooltipX = tooltip.x - tooltipWidth / 2 // Center the tooltip on the X position
            const tooltipY = tooltip.y // Already positioned below chart
            
            return (
              <g>
                {/* Tooltip background with enhanced shadow */}
                <defs>
                  <filter id="shadow-xl" x="-50%" y="-50%" width="200%" height="200%">
                    <feGaussianBlur in="SourceAlpha" stdDeviation="4"/>
                    <feOffset dx="0" dy="4" result="offsetblur"/>
                    <feComponentTransfer>
                      <feFuncA type="linear" slope="0.25"/>
                    </feComponentTransfer>
                    <feMerge>
                      <feMergeNode/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>
                
                {/* Background with white/95 opacity and border */}
                <rect
                  x={tooltipX}
                  y={tooltipY}
                  width={tooltipWidth}
                  height={tooltipHeight}
                  fill="rgba(255, 255, 255, 0.98)"
                  stroke="#e5e7eb"
                  strokeWidth={1.5}
                  rx={8}
                  filter="url(#shadow-xl)"
                />
                
                {/* Header: Full Business Rule Logic (No truncation) */}
                <text
                  x={tooltipX + tooltipWidth / 2}
                  y={tooltipY + 20}
                  fill="#1f2937"
                  fontSize="12"
                  fontWeight="700"
                  textAnchor="middle"
                  style={{ lineHeight: '1.5' }}
                >
                  Business Rule
                </text>
                {/* Full rule name - wrapped if needed */}
                <text
                  x={tooltipX + tooltipWidth / 2}
                  y={tooltipY + 40}
                  fill="#374151"
                  fontSize="11"
                  fontWeight="500"
                  textAnchor="middle"
                  style={{ lineHeight: '1.4' }}
                >
                  {tooltip.fullRuleName.length > 50 
                    ? tooltip.fullRuleName.substring(0, 47) + '...' 
                    : tooltip.fullRuleName}
                </text>
                
                {/* Impact: Exact value with sign */}
                <text
                  x={tooltipX + tooltipWidth / 2}
                  y={tooltipY + 65}
                  fill={tooltip.value >= 0 ? '#10b981' : '#ef4444'}
                  fontSize="13"
                  fontWeight="700"
                  fontFamily="monospace"
                  textAnchor="middle"
                >
                  Impact: {formatCurrencyFull(tooltip.value)}
                </text>
                
                {/* Type: Manual Override or Logic Adjustment */}
                <text
                  x={tooltipX + tooltipWidth / 2}
                  y={tooltipY + 85}
                  fill="#6b7280"
                  fontSize="10"
                  fontWeight="600"
                  textAnchor="middle"
                >
                  Type: {tooltip.ruleType}
                </text>
                
                {/* Contribution Percentage */}
                <text
                  x={tooltipX + tooltipWidth / 2}
                  y={tooltipY + 105}
                  fill="#9ca3af"
                  fontSize="9"
                  textAnchor="middle"
                  fontStyle="italic"
                >
                  {tooltip.contribution.toFixed(1)}% of Total Adjustment • Click to drill down
                </text>
              </g>
            )
          })()}
        </svg>
      </div>
      
      {/* Legend */}
      <div style={{ display: 'flex', gap: '1.5rem', marginTop: '1rem', fontSize: '0.875rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '16px', height: '16px', backgroundColor: '#1e3a8a', borderRadius: '2px' }}></div>
          <span style={{ color: '#6b7280' }}>Original P&L</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '16px', height: '16px', backgroundColor: '#10b981', borderRadius: '2px' }}></div>
          <span style={{ color: '#6b7280' }}>Positive Impact</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '16px', height: '16px', backgroundColor: '#ef4444', borderRadius: '2px' }}></div>
          <span style={{ color: '#6b7280' }}>Negative Impact</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '16px', height: '16px', backgroundColor: '#374151', borderRadius: '2px' }}></div>
          <span style={{ color: '#6b7280' }}>Adjusted P&L</span>
        </div>
      </div>
    </div>
  )
}

export default PnlWaterfallChart

