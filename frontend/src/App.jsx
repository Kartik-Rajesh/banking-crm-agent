import React, { useState, useEffect, useCallback } from 'react'
import { MessageSquare, Users, CheckCircle, AlertCircle } from 'lucide-react'
import { Sidebar } from './components/Sidebar'
import { ChatInterface } from './components/ChatInterface'
import { CustomerCardList } from './components/CustomerCard'
import { MessagePreview } from './components/MessagePreview'
import { useAgentStream } from './hooks/useAgentStream'

const TABS = [
  { id: 'leads',    label: 'Scored Leads',      icon: Users },
  { id: 'messages', label: 'WhatsApp Messages',  icon: MessageSquare },
]

// ── Toast ────────────────────────────────────────────────────────────────────

function Toast({ toast }) {
  if (!toast) return null
  const ok = toast.type === 'success'
  return (
    <div
      className="fixed top-4 right-4 z-50 flex items-start gap-2.5 px-4 py-3 rounded-xl shadow-2xl text-sm font-medium max-w-xs animate-slide-up"
      style={{
        backgroundColor: ok ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
        border: `1px solid ${ok ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
        color: ok ? 'var(--accent-success)' : 'var(--accent-danger)',
      }}
    >
      {ok
        ? <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
        : <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />}
      <span style={{ color: 'var(--text-primary)' }}>{toast.message}</span>
    </div>
  )
}

// ── Right panel header ───────────────────────────────────────────────────────

function PanelHeader({ activeTab, setActiveTab, customers, generatedMessages }) {
  const customerCount = customers.length
  const messageCount  = generatedMessages.length
  const avgScore      = customerCount > 0
    ? (customers.reduce((s, c) => s + (c.conversion_score || 0), 0) / customerCount).toFixed(1)
    : null

  return (
    <div
      className="flex items-center px-4 h-14 gap-2 flex-shrink-0"
      style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'var(--bg-surface)' }}
    >
      <div className="flex gap-1 flex-1">
        {TABS.map(tab => {
          const Icon  = tab.icon
          const count = tab.id === 'leads' ? customerCount : messageCount
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150"
              style={isActive
                ? {
                    backgroundColor: 'rgba(59,130,246,0.12)',
                    color: 'var(--accent-primary)',
                    border: '1px solid rgba(59,130,246,0.25)',
                  }
                : {
                    color: 'var(--text-tertiary)',
                    border: '1px solid transparent',
                  }
              }
              onMouseEnter={e => !isActive && (e.currentTarget.style.color = 'var(--text-secondary)')}
              onMouseLeave={e => !isActive && (e.currentTarget.style.color = 'var(--text-tertiary)')}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
              {count > 0 && (
                <span
                  className="font-mono text-xs px-1.5 py-0.5 rounded-full"
                  style={{
                    backgroundColor: isActive ? 'rgba(59,130,246,0.2)' : 'rgba(255,255,255,0.07)',
                    color: isActive ? 'var(--accent-primary)' : 'var(--text-tertiary)',
                  }}
                >
                  {count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {avgScore && (
        <div className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
          Avg{' '}
          <span className="font-mono font-semibold" style={{ color: 'var(--text-primary)' }}>
            {avgScore}
          </span>
          {' '}· Top{' '}
          <span className="font-mono font-semibold" style={{ color: 'var(--accent-success)' }}>
            {Math.max(...customers.map(c => c.conversion_score || 0)).toFixed(1)}
          </span>
        </div>
      )}
    </div>
  )
}

// ── App ───────────────────────────────────────────────────────────────────────

export default function App() {
  const [activeTab, setActiveTab] = useState('leads')
  const [toast, setToast]         = useState(null)

  const {
    messages,
    isStreaming,
    customers,
    generatedMessages,
    sendMessage,
    clearConversation,
  } = useAgentStream()

  // Auto-switch to leads tab when customers first arrive
  useEffect(() => {
    if (customers.length > 0 && isStreaming) setActiveTab('leads')
  }, [customers.length, isStreaming])

  // Auto-switch to messages tab when messages arrive (only if we're on leads)
  useEffect(() => {
    if (generatedMessages.length > 0 && !isStreaming) {
      // Don't force-switch; let user stay on leads if they expanded a card
    }
  }, [generatedMessages.length, isStreaming])

  const showToast = useCallback((message, type = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }, [])

  return (
    <div className="flex h-screen overflow-hidden" style={{ backgroundColor: 'var(--bg-base)' }}>
      <Toast toast={toast} />

      {/* ── Left: Sidebar ── */}
      <Sidebar
        onSend={sendMessage}
        isStreaming={isStreaming}
        hasMessages={messages.length > 0}
        onClear={clearConversation}
      />

      {/* ── Centre: Chat ── */}
      <div
        className="flex flex-col flex-1 min-w-0 overflow-hidden"
        style={{ borderRight: '1px solid var(--border)', minWidth: '320px' }}
      >
        {/* Chat header */}
        <div
          className="flex items-center px-5 h-14 flex-shrink-0"
          style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'var(--bg-surface)' }}
        >
          <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Conversation</p>
          {isStreaming && (
            <div className="ml-3 flex items-center gap-1.5 text-xs" style={{ color: 'var(--accent-primary)' }}>
              <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: 'var(--accent-primary)' }} />
              Working…
            </div>
          )}
        </div>

        <div className="flex-1 overflow-hidden">
          <ChatInterface messages={messages} isStreaming={isStreaming} onSend={sendMessage} />
        </div>
      </div>

      {/* ── Right: Results panel ── */}
      <div
        className="flex flex-col overflow-hidden flex-shrink-0"
        style={{ width: '480px' }}
      >
        <PanelHeader
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          customers={customers}
          generatedMessages={generatedMessages}
        />

        <div className="flex-1 overflow-y-auto">
          {activeTab === 'leads' && (
            <CustomerCardList customers={customers} />
          )}

          {activeTab === 'messages' && (
            <div className="p-3">
              {generatedMessages.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center px-6">
                  <MessageSquare className="w-10 h-10 mb-3 opacity-20" style={{ color: 'var(--text-tertiary)' }} />
                  <p className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>No messages yet</p>
                  <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>
                    Ask the agent to find leads and generate WhatsApp messages.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-xs uppercase tracking-widest px-1" style={{ color: 'var(--text-tertiary)' }}>
                    {generatedMessages.length} customers · {generatedMessages.length * 3} messages ready
                  </p>
                  {generatedMessages.map((msg, i) => (
                    <MessagePreview key={`${msg.customer_id ?? i}`} messageData={msg} />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
