import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

const FileUpload = ({ onFileUpload, sessionId, isUploading }) => {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onFileUpload(acceptedFiles[0])
    }
  }, [onFileUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024, // 50MB
  })

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} disabled={isUploading} />
        <div className="space-y-4">
          <div className="mx-auto w-12 h-12 text-gray-400">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <div>
            <p className="text-lg font-medium text-gray-900">
              {isDragActive ? 'Drop the file here' : 'Drag & drop your file here'}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              or click to browse
            </p>
            <p className="text-xs text-gray-400 mt-2">
              Supports CSV, XLSX, XLS files (max 50MB)
            </p>
          </div>
        </div>
      </div>

      {isUploading && (
        <div className="mt-4 text-center">
          <div className="inline-flex items-center px-4 py-2 bg-primary-100 text-primary-800 rounded-lg">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-primary-800" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Processing your file...
          </div>
        </div>
      )}
    </div>
  )
}

export default FileUpload