import React, { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'

interface PortalTooltipProps {
  content: {
    title: string
    logic?: string | null
    impact?: number
  }
  children: React.ReactNode
  delay?: number
}

/**
 * PortalTooltip Component
 * Renders tooltip into a React Portal (document.body) to avoid clipping
 * Automatically adjusts position to stay within viewport bounds
 */
const PortalTooltip: React.FC<PortalTooltipProps> = ({
  content,
  children,
  delay = 200
}) => {
  const [showTooltip, setShowTooltip] = useState(false)
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 })
  const tooltipRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  const formatCurrency = (value: number): string => {
    const isNegative = value < 0
    const absValue = Math.abs(value)
    const formatted = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(absValue)
    return isNegative ? `(${formatted})` : formatted
  }

  const calculatePosition = (rect: DOMRect) => {
    const tooltip = tooltipRef.current
    if (!tooltip) return { x: 0, y: 0 }

    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    const tooltipWidth = tooltip.offsetWidth || 300
    const tooltipHeight = tooltip.offsetHeight || 100

    // Default position: above the trigger, centered
    let x = rect.left + rect.width / 2 - tooltipWidth / 2
    let y = rect.top - tooltipHeight - 8

    // Adjust if tooltip goes off left edge
    if (x < 10) {
      x = 10
    }

    // Adjust if tooltip goes off right edge
    if (x + tooltipWidth > viewportWidth - 10) {
      x = viewportWidth - tooltipWidth - 10
    }

    // Adjust if tooltip goes off top edge
    if (y < 10) {
      y = rect.bottom + 8
    }

    // Adjust if tooltip goes off bottom edge
    if (y + tooltipHeight > viewportHeight - 10) {
      y = viewportHeight - tooltipHeight - 10
    }

    return { x, y }
  }

  const handleMouseEnter = (e: React.MouseEvent) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    
    timeoutRef.current = setTimeout(() => {
      if (triggerRef.current) {
        const rect = triggerRef.current.getBoundingClientRect()
        setTooltipPosition({ x: rect.left, y: rect.top })
        setShowTooltip(true)
      }
    }, delay)
  }

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setShowTooltip(false)
  }

  useEffect(() => {
    if (showTooltip && tooltipRef.current && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      const position = calculatePosition(rect)
      
      // Use requestAnimationFrame to ensure DOM is updated
      requestAnimationFrame(() => {
        if (tooltipRef.current) {
          tooltipRef.current.style.left = `${position.x}px`
          tooltipRef.current.style.top = `${position.y}px`
        }
      })
    }
  }, [showTooltip])

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return (
    <>
      <div
        ref={triggerRef}
        style={{ display: 'inline-block' }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {children}
      </div>
      {showTooltip && createPortal(
        <div
          ref={tooltipRef}
          style={{
            position: 'fixed',
            zIndex: 10000,
            backgroundColor: 'white',
            color: '#1f2937',
            padding: '0.75rem',
            borderRadius: '8px',
            border: '1px solid #e5e7eb',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
            pointerEvents: 'none',
            maxWidth: '320px',
            lineHeight: '1.5',
            fontSize: '0.75rem'
          }}
        >
          {/* Title */}
          <div style={{
            fontWeight: '700',
            fontSize: '0.875rem',
            color: '#111827',
            marginBottom: '0.375rem',
            lineHeight: '1.25'
          }}>
            {content.title}
          </div>
          
          {/* Logic */}
          {content.logic && (
            <div style={{
              color: '#4b5563',
              fontSize: '0.75rem',
              marginBottom: '0.375rem',
              wordBreak: 'break-word'
            }}>
              Logic: {content.logic.length > 100 ? content.logic.substring(0, 97) + '...' : content.logic}
            </div>
          )}
          
          {/* Impact */}
          {content.impact !== undefined && (
            <div style={{
              color: content.impact >= 0 ? '#10b981' : '#ef4444',
              fontFamily: 'monospace',
              fontWeight: '700',
              fontSize: '0.875rem'
            }}>
              Impact: ${formatCurrency(content.impact)}
            </div>
          )}
        </div>,
        document.body
      )}
    </>
  )
}

export default PortalTooltip


