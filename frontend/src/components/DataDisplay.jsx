import React from 'react'
import { formatCellValue } from '../utils/formatters'

const DataDisplay = ({ data, columnOrder }) => {
  if (!data) return null

  // If it's an array of objects (like variance results)
  if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
    // Use explicit column order if provided, otherwise use object keys
    const columns = columnOrder || Object.keys(data[0])

    // Debug logging
    console.log('DataDisplay props:', { data: data.length, columnOrder, columns })

    return (
      <div className="overflow-x-auto rounded-lg border border-gray-200 mt-4">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((column) => (
                <th
                  key={column}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {column.replace(/_/g, ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((row, index) => (
              <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                {columns.map((column) => (
                  <td key={column} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCellValue(row[column], column)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  // If it's a simple object
  if (typeof data === 'object' && !Array.isArray(data)) {
    return (
      <div className="bg-gray-50 rounded-lg p-4 mt-4">
        <pre className="text-sm text-gray-700 overflow-x-auto">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    )
  }

  // For other data types
  return (
    <div className="bg-gray-50 rounded-lg p-4 mt-4">
      <pre className="text-sm text-gray-700 whitespace-pre-wrap">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  )
}

export default DataDisplay