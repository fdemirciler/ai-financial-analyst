import React from 'react'

const ChatMessage = ({ message, isUser }) => {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-3xl rounded-lg px-4 py-3 ${isUser
          ? 'bg-primary-600 text-white'
          : 'bg-white border border-gray-200 text-gray-800'
        }`}>
        <div className="prose prose-sm max-w-none">
          {typeof message === 'string' ? (
            <div dangerouslySetInnerHTML={{ __html: message.replace(/\n/g, '<br />') }} />
          ) : (
            <pre className="whitespace-pre-wrap">{JSON.stringify(message, null, 2)}</pre>
          )}
        </div>
      </div>
    </div>
  )
}

export default ChatMessage