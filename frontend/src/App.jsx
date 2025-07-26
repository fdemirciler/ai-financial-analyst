import React, { useState, useEffect, useRef } from 'react'
import FileUpload from './components/FileUpload'
import ChatMessage from './components/ChatMessage'
import DataDisplay from './components/DataDisplay'
import { uploadFile, sendMessage } from './utils/api'

function App() {
  const [sessionId, setSessionId] = useState('')
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [hasFile, setHasFile] = useState(false)
  const messagesEndRef = useRef(null)

  // Initialize session
  useEffect(() => {
    const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    setSessionId(newSessionId)
  }, [])

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleFileUpload = async (file) => {
    if (!sessionId) return

    setIsUploading(true)
    try {
      const result = await uploadFile(sessionId, file)
      setHasFile(true)

      // Add success message
      setMessages(prev => [...prev, {
        id: Date.now(),
        content: `File "${file.name}" uploaded successfully. Ready for analysis!`,
        isUser: false
      }])
    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now(),
        content: `Error uploading file: ${error.response?.data?.detail || error.message}`,
        isUser: false
      }])
    } finally {
      setIsUploading(false)
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!inputMessage.trim() || !sessionId || isProcessing) return

    const userMessage = inputMessage.trim()
    setInputMessage('')

    // Add user message to chat
    setMessages(prev => [...prev, {
      id: Date.now(),
      content: userMessage,
      isUser: true
    }])

    setIsProcessing(true)

    try {
      const response = await sendMessage(sessionId, userMessage)

      // Add AI response to chat
      setMessages(prev => [...prev, {
        id: Date.now(),
        content: response.response,
        isUser: false,
        data: response.data
      }])
    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now(),
        content: `Error processing your request: ${error.response?.data?.detail || error.message}`,
        isUser: false
      }])
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </div>
              <h1 className="ml-3 text-xl font-semibold text-gray-900">Analysis Agent</h1>
            </div>
            <div className="text-sm text-gray-500">
              Session: {sessionId.substring(0, 12)}...
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!hasFile ? (
          // File Upload Section
          <div className="text-center py-12">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Your Data</h2>
              <p className="text-gray-600">Start by uploading a CSV or Excel file for analysis</p>
            </div>
            <FileUpload
              onFileUpload={handleFileUpload}
              sessionId={sessionId}
              isUploading={isUploading}
            />
          </div>
        ) : (
          // Chat Interface
          <div className="flex flex-col h-[calc(100vh-200px)]">
            {/* Messages Container */}
            <div className="flex-1 overflow-y-auto mb-4 space-y-4">
              {messages.map((message) => (
                <div key={message.id}>
                  <ChatMessage
                    message={message.content}
                    isUser={message.isUser}
                  />
                  {message.data && (
                    <div className="max-w-3xl mx-auto">
                      <DataDisplay data={message.data} />
                    </div>
                  )}
                </div>
              ))}
              {isProcessing && (
                <div className="flex justify-start mb-4">
                  <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                    <div className="flex items-center">
                      <div className="animate-pulse flex space-x-2">
                        <div className="h-2 w-2 bg-gray-400 rounded-full"></div>
                        <div className="h-2 w-2 bg-gray-400 rounded-full"></div>
                        <div className="h-2 w-2 bg-gray-400 rounded-full"></div>
                      </div>
                      <span className="ml-2 text-sm text-gray-500">Analyzing...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Form */}
            <form onSubmit={handleSendMessage} className="border-t border-gray-200 pt-4">
              <div className="flex space-x-3">
                <div className="flex-1">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Ask a question about your data..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    disabled={isProcessing}
                  />
                </div>
                <button
                  type="submit"
                  disabled={!inputMessage.trim() || isProcessing}
                  className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
              <div className="mt-2 text-xs text-gray-500 text-center">
                Example: "Compare last two periods and prepare a variance analysis"
              </div>
            </form>
          </div>
        )}
      </main>
    </div>
  )
}

export default App