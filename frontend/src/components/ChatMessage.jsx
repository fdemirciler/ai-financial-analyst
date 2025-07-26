import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const ChatMessage = ({ message, isUser }) => {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-3xl rounded-lg px-4 py-3 ${isUser
        ? 'bg-primary-600 text-white'
        : 'bg-white border border-gray-200 text-gray-800'
        }`}>
        {isUser ? (
          <div className="text-white">{message}</div>
        ) : (
          <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-strong:text-gray-900 prose-table:text-gray-900">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {typeof message === 'string' ? message : JSON.stringify(message, null, 2)}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatMessage