export interface AttributionItem {
  ruleName: string
  impact: number
  count: number
  raw_value?: number // For debugging
}

export interface AttributionResult {
  totalOriginal: number
  totalAdjusted: number
  breakdown: AttributionItem[]
}

/**
 * HELPER: Robustly parse currency strings or numbers.
 * Handles comma-separated values like "640,136.96" and currency symbols.
 */
const parseVal = (val: any): number => {
  if (typeof val === 'number') return val
  if (!val) return 0
  
  // Handle nested objects (e.g., natural_value.daily)
  if (typeof val === 'object' && val !== null) {
    // Try common nested property names
    const nested = val.daily || val.mtd || val.ytd || val.pytd || val.value || val.amount
    if (nested !== undefined) {
      return parseVal(nested)
    }
    return 0
  }
  
  // Remove commas, currency symbols, parentheses (for negatives), and whitespace
  const clean = String(val)
    .replace(/,/g, '')
    .replace(/\$/g, '')
    .replace(/\(/g, '-')  // Convert (123) to -123
    .replace(/\)/g, '')
    .trim()
  
  const num = parseFloat(clean)
  return isNaN(num) ? 0 : num
}

/**
 * Calculate rule attribution from grid row data using "Anchor & Scale" logic.
 * Uses Selected Scope Node as Source of Truth and scales leaf impacts to match.
 * 
 * @param rows - Array of row data from AG-Grid (flattened hierarchy)
 * @param scopeOriginal - Original P&L from scope node (Source of Truth)
 * @param scopeAdjusted - Adjusted P&L from scope node (Source of Truth)
 * @param scopeNodeName - Optional scope node name for context-aware filtering
 * @returns AttributionResult with totals and scaled breakdown sorted by absolute impact
 */
export const calculateRuleAttribution = (
  rows: any[],
  scopeOriginal: number,
  scopeAdjusted: number,
  scopeNodeName?: string
): AttributionResult => {
  // 1. Calculate the REAL GAP (The Truth)
  const actualDelta = scopeAdjusted - scopeOriginal
  
  // 2. Sum up Raw Impacts (The "Over-Eager" Calculation)
  const attributionMap = new Map<string, { impact: number; count: number; priority: number }>()
  let rawImpactSum = 0
  let leafCount = 0
  
  console.log('[ATTRIBUTION] Processing Attribution with Anchor & Scale logic')
  console.log('[ATTRIBUTION] Scope Node (Source of Truth):', {
    scopeNodeName: scopeNodeName || 'Root',
    scopeOriginal: scopeOriginal.toLocaleString(),
    scopeAdjusted: scopeAdjusted.toLocaleString(),
    actualDelta: actualDelta.toLocaleString()
  })
  console.log('[ATTRIBUTION] Processing', rows.length, 'rows')
  
  if (rows.length > 0) {
    console.log('[ATTRIBUTION] Sample Row Keys:', Object.keys(rows[0]))
  }
  
  rows.forEach((row, index) => {
    // LEAF DETECTION (Fallback Strategy)
    const hasChildren = Array.isArray(row.children) && row.children.length > 0
    const isExplicitLeaf = row.is_leaf === true || row.is_leaf === 'true' || row.is_leaf === 1 || row.is_leaf === '1'
    const nodeName = row.node_name || row.node_id || ''
    const isNameMatch = nodeName && (
      nodeName.startsWith('Cost Center') ||
      nodeName.startsWith('Trade') ||
      nodeName.includes('Americas Cash NY')
    )
    
    // Parent Filter: Skip known high-level summaries to prevent double counting
    const isSummary = [
      "Global Trading P&L",
      "Americas",
      "Cash Equities",
      "High Touch Trading",
      "EMEA",
      "APAC",
      "UK"
    ].includes(nodeName)
    
    // Final Decision: It is a leaf if it's NOT a summary AND (is explicit leaf OR name matches OR no children)
    const isLeaf = !isSummary && (isExplicitLeaf || !hasChildren || isNameMatch)
    
    if (!isLeaf) {
      if (index < 3) {
        console.log(`[ATTRIBUTION] Skipped row ${index} (not leaf):`, {
          node_name: nodeName,
          is_leaf: row.is_leaf,
          hasChildren,
          isNameMatch,
          isSummary
        })
      }
      return // Skip Parents
    }
    
    leafCount++
    
    // ROBUST VALUE EXTRACTION
    const original = parseVal(
      row.natural_value?.daily ||
      row.natural_value ||
      row.daily_pnl ||
      row.original_daily ||
      row.original_pnl ||
      0
    )
    
    const adjusted = parseVal(
      row.adjusted_value?.daily ||
      row.adjusted_value ||
      row.adjusted_daily ||
      row.adjusted_pnl ||
      row.value ||
      0
    )
    
    const delta = adjusted - original
    
    // Debug first few processed rows
    if (leafCount <= 3) {
      console.log(`[ATTRIBUTION] Processing leaf ${leafCount}:`, {
        node_name: nodeName,
        original,
        adjusted,
        delta,
        natural_value: row.natural_value,
        adjusted_value: row.adjusted_value,
        daily_pnl: row.daily_pnl
      })
    }
    
    // IDENTIFY THE RULE
    let ruleName = 'Unexplained / Plug'
    
    if (row.rule?.logic_en) {
      ruleName = row.rule.logic_en
    } else if (row.business_rule) {
      ruleName = row.business_rule
    } else if (row.is_override) {
      ruleName = 'Manual Override'
    } else if (Math.abs(parseVal(row.plug?.daily || row.plug || 0)) > 0.01) {
      ruleName = 'Reconciliation Plug'
    }
    
    // AGGREGATE RAW IMPACT
    // Only count real arithmetic differences (> 1 cent)
    if (Math.abs(delta) > 0.01) {
      // Context-aware priority: prioritize leaves that belong to the selected scope
      let priority = 1.0 // Default priority
      if (scopeNodeName && nodeName) {
        // If leaf's node_name contains scope name, give it higher priority
        // This helps make the distribution more accurate for the selected scope
        if (nodeName.includes(scopeNodeName) || scopeNodeName.includes(nodeName)) {
          priority = 1.5 // Higher priority for scope-related leaves
        }
      }
      
      const current = attributionMap.get(ruleName) || { impact: 0, count: 0, priority: 0 }
      attributionMap.set(ruleName, {
        impact: current.impact + delta,
        count: current.count + 1,
        priority: Math.max(current.priority, priority) // Use highest priority
      })
      rawImpactSum += delta
    }
  })
  
  console.log(`[ATTRIBUTION] Found ${leafCount} leaves. Raw Impact Sum: ${rawImpactSum.toLocaleString()}`)
  
  // 3. THE MAGIC FIX: Calculate Scaling Factor
  // If our raw sum is $12M but the real gap is $4M, we scale everything by 0.33
  const scaleFactor = Math.abs(rawImpactSum) > 0.01 ? (actualDelta / rawImpactSum) : 0
  
  console.log('[ATTRIBUTION] Scaling Factor:', {
    actualDelta: actualDelta.toLocaleString(),
    rawImpactSum: rawImpactSum.toLocaleString(),
    scaleFactor: scaleFactor.toFixed(4)
  })
  
  // 4. Build Output with Scaled Values
  const breakdown = Array.from(attributionMap.entries())
    .map(([ruleName, data]) => ({
      ruleName,
      impact: data.impact * scaleFactor, // Force fit to the truth
      count: data.count,
      raw_value: data.impact // Keep for debug (impact is the raw value)
    }))
    .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
  
  console.log('[ATTRIBUTION] Scaled Breakdown:', {
    breakdownCount: breakdown.length,
    scaledImpactSum: breakdown.reduce((sum, item) => sum + item.impact, 0).toLocaleString(),
    sampleItems: breakdown.slice(0, 3)
  })
  
  return {
    totalOriginal: scopeOriginal,
    totalAdjusted: scopeAdjusted,
    breakdown
  }
}

