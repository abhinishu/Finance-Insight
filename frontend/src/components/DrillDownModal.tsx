import React from 'react'

interface DrillDownModalProps {
  ruleName: string
  rows: any[]
  onClose: () => void
}

/**
 * Drill-Down Modal Component
 * Shows which leaf nodes (e.g., Cost Centers) are affected by a specific rule
 */
const DrillDownModal: React.FC<DrillDownModalProps> = ({
  ruleName,
  rows,
  onClose
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
  
  // Filter rows to find leaf nodes affected by this rule
  const affectedRows = rows
    .filter(row => {
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
                     rowRuleName.startsWith(ruleName)
      
      if (!matches) return false
      
      // Only include leaf nodes
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
    .map(row => {
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
      
      return {
        nodeName: row.node_name || row.node_id || 'Unknown',
        original,
        adjusted,
        impact: delta
      }
    })
    .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact)) // Sort by absolute impact
    .slice(0, 10) // Top 10
  
  return (
    <div 
      className="drawer-overlay" 
      onClick={onClose}
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
    >
      <div 
        className="drawer-content" 
        onClick={(e) => e.stopPropagation()}
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '0',
          maxWidth: '700px',
          width: '90%',
          maxHeight: '80vh',
          overflow: 'auto',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)'
        }}
      >
        <div style={{
          padding: '1.5rem',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: '600', color: '#1f2937' }}>
              Rule Impact Drill-Down
            </h3>
            <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.875rem', color: '#6b7280' }}>
              {ruleName}
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.5rem',
              cursor: 'pointer',
              color: '#6b7280',
              padding: '0.25rem 0.5rem',
              lineHeight: 1
            }}
          >
            ×
          </button>
        </div>
        
        <div style={{ padding: '1.5rem' }}>
          {affectedRows.length > 0 ? (
            <>
              <p style={{ marginBottom: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
                Top {affectedRows.length} affected nodes (sorted by impact):
              </p>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                      <th style={{ padding: '0.75rem', textAlign: 'left', fontSize: '0.875rem', fontWeight: '600', color: '#374151' }}>
                        Node Name
                      </th>
                      <th style={{ padding: '0.75rem', textAlign: 'right', fontSize: '0.875rem', fontWeight: '600', color: '#374151' }}>
                        Original P&L
                      </th>
                      <th style={{ padding: '0.75rem', textAlign: 'right', fontSize: '0.875rem', fontWeight: '600', color: '#374151' }}>
                        Adjusted P&L
                      </th>
                      <th style={{ padding: '0.75rem', textAlign: 'right', fontSize: '0.875rem', fontWeight: '600', color: '#374151' }}>
                        Impact
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {affectedRows.map((row, index) => (
                      <tr 
                        key={index}
                        style={{
                          borderBottom: '1px solid #e5e7eb',
                          backgroundColor: index % 2 === 0 ? 'white' : '#f9fafb'
                        }}
                      >
                        <td style={{ padding: '0.75rem', fontSize: '0.875rem', color: '#1f2937' }}>
                          {row.nodeName}
                        </td>
                        <td style={{ padding: '0.75rem', textAlign: 'right', fontSize: '0.875rem', color: '#6b7280' }}>
                          ${formatCurrency(row.original)}
                        </td>
                        <td style={{ padding: '0.75rem', textAlign: 'right', fontSize: '0.875rem', color: '#6b7280' }}>
                          ${formatCurrency(row.adjusted)}
                        </td>
                        <td style={{ 
                          padding: '0.75rem', 
                          textAlign: 'right', 
                          fontSize: '0.875rem', 
                          fontWeight: '600',
                          color: row.impact >= 0 ? '#10b981' : '#ef4444'
                        }}>
                          ${formatCurrency(row.impact)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#6b7280' }}>
              <p>No affected leaf nodes found for this rule.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DrillDownModal


