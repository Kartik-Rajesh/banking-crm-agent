import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Send, Bot, User, Sparkles } from 'lucide-react'
import { AgentThinking } from './AgentThinking'

const SUGGESTED_QUERIES = [
  'Find top 10 loan candidates this month and generate WhatsApp messages',
  'Show salaried customers with credit score above 720 in Mumbai',
  'Show self-employed customers earning above ₹1,50,000',
  'Why is Arjun Reddy a good candidate? What is the best product for him?',
  'Generate WhatsApp messages for top 5 leads in Bangalore',
  'Regenerate the WhatsApp message for Rahul Kumar but make it more urgent',
]

function UserBubble({ content }) {
  return (
    <div className="flex justify-end gap-2.5 animate-slide-up">
      <div
        className="max-w-[82%] px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm leading-relaxed"
        style={{ backgroundColor: 'var(--accent-primary)', color: 'var(--text-primary)' }}
      >
        {content}
      </div>
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
        style={{ backgroundColor: 'var(--accent-primary)' }}
      >
        <User className="w-3.5 h-3.5 text-white" />
      </div>
    </div>
  )
}

function AgentBubble({ message }) {
  const hasThinking = (message.thinkingSteps || []).length > 0
  const isError     = message.isError

  return (
    <div className="flex gap-2.5 animate-slide-up">
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
        style={{ background: 'linear-gradient(135deg, var(--accent-purple), var(--accent-primary))' }}
      >
        <Bot className="w-3.5 h-3.5 text-white" />
      </div>

      <div
        className="flex-1 min-w-0 px-4 py-3 rounded-2xl rounded-tl-sm"
        style={{
          backgroundColor: isError ? 'rgba(239,68,68,0.08)' : 'var(--bg-elevated)',
          border: `1px solid ${isError ? 'rgba(239,68,68,0.25)' : 'var(--border)'}`,
          maxWidth: '88%',
        }}
      >
        {/* Thinking steps */}
        {hasThinking && (
          <AgentThinking steps={message.thinkingSteps} isStreaming={message.isStreaming} />
        )}

        {/* Dots while loading with no content yet */}
        {message.isStreaming && !message.content && !hasThinking && (
          <div className="dot-pulse flex items-center gap-0 py-0.5">
            <span /><span /><span />
          </div>
        )}

        {/* Response text */}
        {message.content && (
          <div className={`prose-banking ${hasThinking ? 'mt-3 pt-3' : ''}`} style={hasThinking ? { borderTop: '1px solid var(--border)' } : {}}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}

export function ChatInterface({ onSend, messages, isStreaming }) {
  const [input, setInput]     = useState('')
  const messagesEndRef        = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!input.trim() || isStreaming) return
    onSend(input.trim())
    setInput('')
  }

  const isEmpty = messages.length === 0

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-4">
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full text-center px-6 pb-8">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4 shadow-lg"
              style={{
                background: 'linear-gradient(135deg, var(--accent-purple), var(--accent-primary))',
                boxShadow: '0 8px 32px rgba(59,130,246,0.2)',
              }}
            >
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-lg font-bold mb-1.5" style={{ color: 'var(--text-primary)' }}>
              What can I help you with?
            </h2>
            <p className="text-sm mb-6" style={{ color: 'var(--text-secondary)' }}>
              Find high-value loan candidates, score them with AI, and generate personalized outreach.
            </p>

            <div className="w-full space-y-1.5">
              <p className="text-xs uppercase tracking-widest mb-2" style={{ color: 'var(--text-tertiary)' }}>
                Try asking
              </p>
              {SUGGESTED_QUERIES.map((q, i) => (
                <button
                  key={i}
                  onClick={() => !isStreaming && onSend(q)}
                  className="w-full text-left px-4 py-2.5 rounded-xl text-xs leading-snug transition-all duration-150"
                  style={{
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    color: 'var(--text-secondary)',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = 'var(--accent-primary)'
                    e.currentTarget.style.color = 'var(--text-primary)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = 'var(--border)'
                    e.currentTarget.style.color = 'var(--text-secondary)'
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(msg => (
          msg.role === 'user'
            ? <UserBubble key={msg.id} content={msg.content} />
            : <AgentBubble key={msg.id} message={msg} />
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick-chips when conversation is active */}
      {!isEmpty && !isStreaming && (
        <div className="px-4 py-2" style={{ borderTop: '1px solid var(--border)' }}>
          <div className="flex gap-1.5 overflow-x-auto scrollbar-none pb-0.5">
            {SUGGESTED_QUERIES.slice(0, 3).map((q, i) => (
              <button
                key={i}
                onClick={() => onSend(q)}
                className="flex-shrink-0 px-3 py-1.5 rounded-full text-xs transition-all duration-150"
                style={{
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-tertiary)',
                }}
                onMouseEnter={e => { e.currentTarget.style.color = 'var(--text-primary)' }}
                onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-tertiary)' }}
              >
                {q.length > 44 ? q.slice(0, 44) + '…' : q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input bar */}
      <div className="px-4 py-3" style={{ borderTop: '1px solid var(--border)' }}>
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={isStreaming ? 'Agent is working…' : 'Ask the agent…'}
            disabled={isStreaming}
            className="chat-input"
          />
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="btn-primary flex-shrink-0 px-4"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  )
}
