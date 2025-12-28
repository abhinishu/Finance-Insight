import React, { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'

interface SmartTooltipProps {
  content: React.ReactNode | string
  children: React.ReactNode
  delay?: number
  maxWidth?: string
}

/**
 * SmartTooltip Component
 * Renders tooltip into a React Portal (document.body) with smart positioning
 * Automatically adjusts position to avoid screen edges
 */
const SmartTooltip: React.FC<SmartTooltipProps> = ({
  content,
  children,
  delay = 200,
  maxWidth = '320px'
}) => {
  const [showTooltip, setShowTooltip] = useState(false)
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 })
  const tooltipRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLDivElement>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)

  const calculatePosition = (rect: DOMRect) => {
    const tooltip = tooltipRef.current
    if (!tooltip) return { x: 0, y: 0 }

    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    const tooltipWidth = tooltip.offsetWidth || 320
    const tooltipHeight = tooltip.offsetHeight || 100

    // Default position: above the trigger, centered
    let x = rect.left + rect.width / 2 - tooltipWidth / 2
    let y = rect.top - tooltipHeight - 8

    // Smart positioning: Shift left if goes off right edge
    if (rect.right + tooltipWidth > viewportWidth) {
      x = viewportWidth - tooltipWidth - 10
    }

    // Shift right if goes off left edge
    if (x < 10) {
      x = 10
    }

    // Smart positioning: Shift up if goes off bottom edge
    if (rect.bottom + tooltipHeight > viewportHeight) {
      y = rect.top - tooltipHeight - 8
    }

    // Shift down if goes off top edge
    if (y < 10) {
      y = rect.bottom + 8
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
            zIndex: 9999,
            backgroundColor: '#1e293b', // slate-800
            color: 'white',
            padding: '0.75rem',
            borderRadius: '6px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            border: '1px solid #475569', // slate-600
            pointerEvents: 'none',
            maxWidth: maxWidth,
            fontSize: '0.75rem',
            lineHeight: '1.5'
          }}
        >
          {typeof content === 'string' ? content : content}
        </div>,
        document.body
      )}
    </>
  )
}

export default SmartTooltip


