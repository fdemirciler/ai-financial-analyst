// Number formatting utilities for financial data
export const formatNumber = (value, type = 'auto') => {
  if (value === null || value === undefined || isNaN(value)) return value

  const num = Number(value)

  switch (type) {
    case 'percentage':
      return `${num.toFixed(1)}%`
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(num)
    case 'decimal':
      return num.toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
      })
    default:
      // Auto-detect format based on value and context
      if (Math.abs(num) >= 1000) {
        // Large numbers - format with thousands separator
        return num.toLocaleString('en-US', {
          minimumFractionDigits: 0,
          maximumFractionDigits: 0
        })
      } else if (Math.abs(num) < 1 && Math.abs(num) > 0.001) {
        // Small decimals - likely percentages
        return `${(num * 100).toFixed(1)}%`
      } else {
        // Regular numbers
        return num.toLocaleString('en-US', {
          minimumFractionDigits: 0,
          maximumFractionDigits: 2
        })
      }
  }
}

export const detectColumnType = (columnName) => {
  const name = columnName.toLowerCase()

  // Percentage detection
  if (name.includes('percentage') || name.includes('%') || name.includes('percent')) {
    return 'percentage'
  }

  // Currency detection
  if (name.includes('currency') || name.includes('cash') || name.includes('revenue') ||
    name.includes('income') || name.includes('sales') || name.includes('expenses') ||
    name.includes('cost') || name.includes('price') || name.includes('amount')) {
    return 'currency'
  }

  // Default to decimal for numeric values
  return 'decimal'
}

export const formatCellValue = (value, columnName) => {
  if (typeof value === 'number') {
    const columnType = detectColumnType(columnName)
    return formatNumber(value, columnType)
  }
  return value
}
