import React from 'react'
import { AttributionItem } from '../utils/pnlAttribution'

interface RuleImpactTableProps {
  attributionData: AttributionItem[]
}

/**
 * Rule Impact Table Component
 * Displays a summary of business rule impacts in a clean, professional table.
 * Uses Tailwind CSS for styling with alternating row colors and right-aligned numbers.
 */
const RuleImpactTable: React.FC<RuleImpactTableProps> = ({ attributionData }) => {
  // Format currency with proper negative handling
  const formatCurrency = (value: number): string => {
    const isNegative = value < 0
    const absValue = Math.abs(value)
    const formatted = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(absValue)
    
    return isNegative ? `(${formatted})` : formatted
  }

  // Truncate long rule names for display
  const truncateRuleName = (name: string, maxLength: number = 60): string => {
    if (name.length <= maxLength) return name
    return name.substring(0, maxLength - 3) + '...'
  }

  if (!attributionData || attributionData.length === 0) {
    return (
      <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-500 text-sm">No rule impacts detected. All values match natural GL baseline.</p>
      </div>
    )
  }

  return (
    <div className="mt-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-3">Adjustment Attribution Analysis</h3>
      <div className="overflow-x-auto bg-white rounded-lg border border-gray-200 shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Rule Name
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Rows Affected
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total Impact
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {attributionData.map((item, index) => {
              const isNegative = item.impact < 0
              const rowColor = index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
              
              return (
                <tr key={item.ruleName} className={rowColor}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900" title={item.ruleName}>
                      {truncateRuleName(item.ruleName)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-700">
                    {item.count}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-right text-sm font-medium ${
                    isNegative ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {formatCurrency(item.impact)}
                  </td>
                </tr>
              )
            })}
          </tbody>
          <tfoot className="bg-gray-100">
            <tr>
              <td className="px-6 py-3 text-sm font-semibold text-gray-900">
                Total
              </td>
              <td className="px-6 py-3 text-right text-sm font-semibold text-gray-700">
                {attributionData.reduce((sum, item) => sum + item.count, 0)}
              </td>
              <td className={`px-6 py-3 text-right text-sm font-semibold ${
                attributionData.reduce((sum, item) => sum + item.impact, 0) < 0 ? 'text-red-600' : 'text-green-600'
              }`}>
                {formatCurrency(attributionData.reduce((sum, item) => sum + item.impact, 0))}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}

export default RuleImpactTable



