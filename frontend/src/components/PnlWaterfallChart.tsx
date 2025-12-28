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
    value: number
    contribution: number
  } | null>(null)
  
  // Calculate total adjustment for contribution percentage
  const totalAdjustment = useMemo(() => {
    return Math.abs(adjustedPnl - originalPnl)
  }, [originalPnl, adjustedPnl])
  // Build waterfall data structure
  const waterfallData = useMemo(() => {
    const steps: Array<{
      name: string
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
      value: originalPnl,
      start: 0,
      end: originalPnl,
      color: '#6b7280', // Gray
      type: 'start'
    })
    
    // Add each rule's impact as a step
    attributionData.forEach((item) => {
      const start = currentValue
      const end = currentValue + item.impact
      const color = item.impact >= 0 ? '#10b981' : '#ef4444' // Green for positive, red for negative
      
      steps.push({
        name: item.ruleName.length > 25 ? item.ruleName.substring(0, 22) + '...' : item.ruleName,
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
      value: adjustedPnl,
      start: 0,
      end: adjustedPnl,
      color: '#3b82f6', // Blue
      type: 'end'
    })
    
    return steps
  }, [attributionData, originalPnl, adjustedPnl])
  
  // Format currency (simplified for axis)
  const formatCurrency = (value: number): string => {
    const isNegative = value < 0
    const absValue = Math.abs(value)
    const formatted = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(absValue)
    return isNegative ? `(${formatted})` : formatted
  }
  
  // Format currency for tooltip (full precision)
  const formatCurrencyFull = (value: number): string => {
    const isNegative = value < 0
    const absValue = Math.abs(value)
    const formatted = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(absValue)
    return isNegative ? `(${formatted})` : formatted
  }
  
  // Format simplified numbers for Y-axis (e.g., "$5M", "$500k")
  const formatAxisLabel = (value: number): string => {
    const absValue = Math.abs(value)
    if (absValue >= 1000000) {
      return `$${(absValue / 1000000).toFixed(1)}M`
    } else if (absValue >= 1000) {
      return `$${(absValue / 1000).toFixed(0)}k`
    } else {
      return `$${absValue.toFixed(0)}`
    }
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
        <svg width={chartWidth} height={chartHeight + 100} style={{ border: '1px solid #e5e7eb' }}>
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
                  <text
                    x={x + barWidth / 2}
                    y={step.value >= 0 ? y - 8 : y + barHeight + 18}
                    fill="#1f2937"
                    fontSize="11"
                    fontWeight="600"
                    textAnchor="middle"
                  >
                    {step.name}
                  </text>
                  <text
                    x={x + barWidth / 2}
                    y={step.value >= 0 ? y + barHeight / 2 : y + barHeight / 2}
                    fill="white"
                    fontSize="10"
                    fontWeight="700"
                    textAnchor="middle"
                    dominantBaseline="middle"
                  >
                    ${formatCurrency(step.value)}
                  </text>
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
              const fullRuleName = attributionData[ruleIndex]?.ruleName || step.name
              
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
                      const rect = e.currentTarget.getBoundingClientRect()
                      const svg = e.currentTarget.closest('svg')
                      if (svg) {
                        const svgRect = svg.getBoundingClientRect()
                        // Calculate contribution percentage
                        const contribution = totalAdjustment > 0 
                          ? (Math.abs(step.value) / totalAdjustment) * 100 
                          : 0
                        setTooltip({
                          x: rect.left - svgRect.left + rect.width / 2,
                          y: rect.top - svgRect.top - 10,
                          ruleName: fullRuleName,
                          value: step.value,
                          contribution
                        })
                      }
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
                  <text
                    x={x + barWidth / 2}
                    y={step.value >= 0 ? stepY - stepHeight - 8 : stepY + stepHeight + 18}
                    fill="#1f2937"
                    fontSize="9"
                    fontWeight="500"
                    textAnchor="middle"
                  >
                    {step.name}
                  </text>
                  <text
                    x={x + barWidth / 2}
                    y={step.value >= 0 ? stepY - stepHeight / 2 : stepY + stepHeight / 2}
                    fill="white"
                    fontSize="9"
                    fontWeight="700"
                    textAnchor="middle"
                    dominantBaseline="middle"
                  >
                    {step.value >= 0 ? '+' : ''}${formatCurrency(step.value)}
                  </text>
                </g>
              )
            }
          })}
          
          {/* Enhanced Tooltip - Clean White Style */}
          {tooltip && (
            <g>
              {/* Tooltip background with enhanced shadow (shadow-xl) */}
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
                {/* Semi-transparent white background (white/95) */}
                <rect id="tooltip-bg" x={tooltip.x - 130} y={tooltip.y - 80} width={260} height={75} rx={8}/>
              </defs>
              {/* Background with white/95 opacity and border */}
              <rect
                x={tooltip.x - 130}
                y={tooltip.y - 80}
                width={260}
                height={75}
                fill="rgba(255, 255, 255, 0.95)"
                stroke="#e5e7eb"
                strokeWidth={1}
                rx={8}
                filter="url(#shadow-xl)"
              />
              {/* Rule Name (Bold) - with leading-relaxed spacing */}
              <text
                x={tooltip.x}
                y={tooltip.y - 55}
                fill="#1f2937"
                fontSize="12"
                fontWeight="700"
                textAnchor="middle"
                style={{ lineHeight: '1.625' }}
              >
                {tooltip.ruleName.length > 40 ? tooltip.ruleName.substring(0, 37) + '...' : tooltip.ruleName}
              </text>
              {/* Impact (Formatted Currency) - with leading-relaxed spacing */}
              <text
                x={tooltip.x}
                y={tooltip.y - 30}
                fill={tooltip.value >= 0 ? '#10b981' : '#ef4444'}
                fontSize="11"
                fontWeight="600"
                fontFamily="monospace"
                textAnchor="middle"
                style={{ lineHeight: '1.625' }}
              >
                Impact: ${formatCurrencyFull(tooltip.value)}
              </text>
              {/* Contribution Percentage - with leading-relaxed spacing */}
              <text
                x={tooltip.x}
                y={tooltip.y - 10}
                fill="#6b7280"
                fontSize="10"
                textAnchor="middle"
                style={{ lineHeight: '1.625' }}
              >
                Contribution: {tooltip.contribution.toFixed(1)}% of Total Adjustment
              </text>
              {/* Click hint - with leading-relaxed spacing */}
              <text
                x={tooltip.x}
                y={tooltip.y + 8}
                fill="#9ca3af"
                fontSize="9"
                fontStyle="italic"
                textAnchor="middle"
                style={{ lineHeight: '1.625' }}
              >
                Click to view breakdown
              </text>
            </g>
          )}
        </svg>
      </div>
      
      {/* Legend */}
      <div style={{ display: 'flex', gap: '1.5rem', marginTop: '1rem', fontSize: '0.875rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '16px', height: '16px', backgroundColor: '#6b7280', borderRadius: '2px' }}></div>
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
          <div style={{ width: '16px', height: '16px', backgroundColor: '#3b82f6', borderRadius: '2px' }}></div>
          <span style={{ color: '#6b7280' }}>Adjusted P&L</span>
        </div>
      </div>
    </div>
  )
}

export default PnlWaterfallChart

