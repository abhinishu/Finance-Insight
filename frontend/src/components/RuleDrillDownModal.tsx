import React, { useMemo } from 'react'

interface RuleDrillDownModalProps {
  isOpen: boolean
  onClose: () => void
  ruleName: string
  allRows: any[]
}

/**
 * Rule Drill-Down Modal Component (The Evidence Locker)
 * Shows detailed breakdown of which nodes were affected by a specific rule
 */
const RuleDrillDownModal: React.FC<RuleDrillDownModalProps> = ({
  isOpen,
  onClose,
  ruleName,
  allRows
}) => {
  // Helper to parse currency strings
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
  
  // Format currency
  const formatCurrency = (value: number): string => {
    const isNegative = value < 0
    const absValue = Math.abs(value)
    const formatted = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(absValue)
    return isNegative ? `(${formatted})` : formatted
  }
  
  // Filter and process affected rows
  const affectedData = useMemo(() => {
    if (!allRows || allRows.length === 0) return { rows: [], totalImpact: 0, totalRows: 0 }
    
    const affectedRows = allRows
      .filter((row: any) => {
        // Check if this row is affected by the rule
        let rowRuleName = 'Unexplained / Plug'
        
        if (row.rule?.logic_en) {
          rowRuleName = row.rule.logic_en
        } else if (row.business_rule) {
          rowRuleName = row.business_rule
        } else if (row.is_override) {
          rowRuleName = 'Manual Override'
        } else if (Math.abs(parseVal(row.plug?.daily || row.plug || 0)) > 0.01) {
          rowRuleName = 'Reconciliation Plug'
        }
        
        // Match rule name (handle truncated names)
        const matches = rowRuleName === ruleName || 
                       ruleName.startsWith(rowRuleName) || 
                       rowRuleName.startsWith(ruleName) ||
                       (ruleName.length > 20 && rowRuleName.includes(ruleName.substring(0, 20)))
        
        if (!matches) return false
        
        // Only include leaf nodes with actual impact
        const hasChildren = Array.isArray(row.children) && row.children.length > 0
        const isExplicitLeaf = row.is_leaf === true || row.is_leaf === 'true' || row.is_leaf === 1 || row.is_leaf === '1'
        const nodeName = row.node_name || ''
        const isNameMatch = nodeName && (
          nodeName.startsWith('Cost Center') ||
          nodeName.startsWith('Trade') ||
          nodeName.includes('Americas Cash NY')
        )
        const isSummary = [
          "Global Trading P&L",
          "Americas",
          "Cash Equities",
          "High Touch Trading",
          "EMEA",
          "APAC",
          "UK"
        ].includes(nodeName)
        
        const isLeaf = !isSummary && (isExplicitLeaf || !hasChildren || isNameMatch)
        
        if (!isLeaf) return false
        
        // Only include rows with actual impact
        const original = parseVal(
          row.natural_value?.daily ||
          row.natural_value ||
          row.daily_pnl ||
          0
        )
        const adjusted = parseVal(
          row.adjusted_value?.daily ||
          row.adjusted_value ||
          row.adjusted_daily ||
          0
        )
        const delta = adjusted - original
        
        return Math.abs(delta) > 0.01
      })
      .map((row: any) => {
        const original = parseVal(
          row.natural_value?.daily ||
          row.natural_value ||
          row.daily_pnl ||
          0
        )
        const adjusted = parseVal(
          row.adjusted_value?.daily ||
          row.adjusted_value ||
          row.adjusted_daily ||
          0
        )
        const impact = adjusted - original
        
        return {
          nodeName: row.node_name || row.node_id || 'Unknown',
          nodeId: row.node_id || 'Unknown',
          original,
          adjusted,
          impact
        }
      })
      .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact)) // Sort by absolute impact
    
    const totalImpact = affectedRows.reduce((sum: number, row: any) => sum + row.impact, 0)
    
    return {
      rows: affectedRows.slice(0, 10), // Top 10
      totalImpact,
      totalRows: affectedRows.length
    }
  }, [allRows, ruleName])
  
  if (!isOpen) return null
  
  return (
    <div 
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
        zIndex: 1000
      }}
      onClick={onClose}
    >
      <div 
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '0',
          maxWidth: '900px',
          width: '90%',
          maxHeight: '85vh',
          overflow: 'auto',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: '1.5rem',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white'
        }}>
          <div style={{ flex: 1 }}>
            <h3 style={{ margin: 0, fontSize: '1.5rem', fontWeight: '700', color: 'white', marginBottom: '0.5rem' }}>
              Forensic Drill-Down: Rule Impact Analysis
            </h3>
            <p style={{ margin: 0, fontSize: '0.875rem', color: 'rgba(255, 255, 255, 0.9)', fontStyle: 'italic' }}>
              {ruleName}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.2)',
              border: 'none',
              fontSize: '1.5rem',
              cursor: 'pointer',
              color: 'white',
              padding: '0.25rem 0.75rem',
              borderRadius: '4px',
              lineHeight: 1,
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.3)'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'}
          >
            ×
          </button>
        </div>
        
        {/* Hero Stats */}
        <div style={{
          padding: '1.5rem',
          backgroundColor: '#f9fafb',
          borderBottom: '1px solid #e5e7eb'
        }}>
          <div style={{
            display: 'flex',
            gap: '2rem',
            alignItems: 'center',
            flexWrap: 'wrap'
          }}>
            <div>
              <div style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Total Impact
              </div>
              <div style={{
                fontSize: '1.75rem',
                fontWeight: '700',
                color: affectedData.totalImpact >= 0 ? '#10b981' : '#ef4444',
                fontFamily: 'monospace'
              }}>
                ${formatCurrency(affectedData.totalImpact)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Rows Affected
              </div>
              <div style={{
                fontSize: '1.75rem',
                fontWeight: '700',
                color: '#374151',
                fontFamily: 'monospace'
              }}>
                {affectedData.totalRows.toLocaleString()}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Top Items Shown
              </div>
              <div style={{
                fontSize: '1.75rem',
                fontWeight: '700',
                color: '#374151',
                fontFamily: 'monospace'
              }}>
                {Math.min(10, affectedData.rows.length)}
              </div>
            </div>
          </div>
        </div>
        
        {/* Table */}
        <div style={{ padding: '1.5rem' }}>
          {affectedData.rows.length > 0 ? (
            <>
              <h4 style={{ 
                marginBottom: '1rem', 
                fontSize: '1rem', 
                fontWeight: '600', 
                color: '#374151' 
              }}>
                Top 10 Most Impacted Items
              </h4>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                      <th style={{ 
                        padding: '0.75rem', 
                        textAlign: 'left', 
                        fontSize: '0.875rem', 
                        fontWeight: '600', 
                        color: '#374151',
                        borderRight: '1px solid #e5e7eb'
                      }}>
                        Node Name
                      </th>
                      <th style={{ 
                        padding: '0.75rem', 
                        textAlign: 'right', 
                        fontSize: '0.875rem', 
                        fontWeight: '600', 
                        color: '#374151',
                        borderRight: '1px solid #e5e7eb'
                      }}>
                        Original P&L
                      </th>
                      <th style={{ 
                        padding: '0.75rem', 
                        textAlign: 'right', 
                        fontSize: '0.875rem', 
                        fontWeight: '600', 
                        color: '#374151',
                        borderRight: '1px solid #e5e7eb'
                      }}>
                        Adjusted P&L
                      </th>
                      <th style={{ 
                        padding: '0.75rem', 
                        textAlign: 'right', 
                        fontSize: '0.875rem', 
                        fontWeight: '600', 
                        color: '#374151'
                      }}>
                        Impact
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {affectedData.rows.map((row: any, index: number) => (
                      <tr 
                        key={row.nodeId || index}
                        style={{
                          borderBottom: '1px solid #e5e7eb',
                          backgroundColor: index % 2 === 0 ? 'white' : '#f9fafb',
                          transition: 'background-color 0.1s'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = index % 2 === 0 ? 'white' : '#f9fafb'}
                      >
                        <td style={{ 
                          padding: '0.75rem', 
                          fontSize: '0.875rem', 
                          color: '#1f2937',
                          borderRight: '1px solid #e5e7eb',
                          fontWeight: '500'
                        }}>
                          {row.nodeName}
                        </td>
                        <td style={{ 
                          padding: '0.75rem', 
                          textAlign: 'right', 
                          fontSize: '0.875rem', 
                          color: '#6b7280',
                          fontFamily: 'monospace',
                          borderRight: '1px solid #e5e7eb'
                        }}>
                          ${formatCurrency(row.original)}
                        </td>
                        <td style={{ 
                          padding: '0.75rem', 
                          textAlign: 'right', 
                          fontSize: '0.875rem', 
                          color: '#6b7280',
                          fontFamily: 'monospace',
                          borderRight: '1px solid #e5e7eb'
                        }}>
                          ${formatCurrency(row.adjusted)}
                        </td>
                        <td style={{ 
                          padding: '0.75rem', 
                          textAlign: 'right', 
                          fontSize: '0.875rem', 
                          fontWeight: '600',
                          fontFamily: 'monospace',
                          color: row.impact >= 0 ? '#10b981' : '#ef4444'
                        }}>
                          ${formatCurrency(row.impact)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {affectedData.totalRows > 10 && (
                <div style={{
                  marginTop: '1rem',
                  padding: '0.75rem',
                  backgroundColor: '#fef3c7',
                  border: '1px solid #fbbf24',
                  borderRadius: '6px',
                  fontSize: '0.875rem',
                  color: '#92400e',
                  textAlign: 'center'
                }}>
                  Showing top 10 of {affectedData.totalRows} affected items. Total impact: ${formatCurrency(affectedData.totalImpact)}
                </div>
              )}
            </>
          ) : (
            <div style={{ 
              padding: '3rem', 
              textAlign: 'center', 
              color: '#6b7280' 
            }}>
              <p style={{ margin: 0, fontSize: '1rem', fontWeight: '500' }}>
                No affected nodes found for this rule.
              </p>
              <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.875rem' }}>
                This rule may not have been applied to any leaf nodes, or all impacts were below the threshold.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default RuleDrillDownModal



