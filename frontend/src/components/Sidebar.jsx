import React from 'react'
import { Building2, Zap, Trash2, Cpu } from 'lucide-react'

const QUICK_QUERIES = [
  'Find top 10 loan candidates this month and generate WhatsApp messages',
  'Show salaried customers with credit score above 720 in Mumbai',
  'Show self-employed customers earning above ₹1,50,000',
  'Why is Arjun Reddy a good candidate? What is the best product for him?',
  'Generate WhatsApp messages for top 5 leads in Bangalore',
  'Regenerate the WhatsApp message for Rahul Kumar but make it more urgent',
]

export function Sidebar({ onSend, isStreaming, hasMessages, onClear }) {
  return (
    <div
      className="flex flex-col h-full select-none"
      style={{ width: '280px', minWidth: '280px', borderRight: '1px solid var(--border)', backgroundColor: 'var(--bg-surface)' }}
    >
      {/* Brand header */}
      <div className="px-4 py-4" style={{ borderBottom: '1px solid var(--border)' }}>
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-purple))' }}
          >
            <Building2 className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>Banking CRM Agent</p>
            <p className="text-xs font-semibold tracking-widest uppercase" style={{ color: 'var(--accent-primary)', fontSize: '0.6rem' }}>
              BUSINESSNEXT
            </p>
          </div>
        </div>
      </div>

      {/* Quick queries */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        <p className="px-3 mb-2 text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-tertiary)' }}>
          Quick Queries
        </p>
        {QUICK_QUERIES.map((q, i) => (
          <button
            key={i}
            onClick={() => !isStreaming && onSend(q)}
            disabled={isStreaming}
            className="sidebar-item disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Zap className="w-3 h-3 flex-shrink-0 mt-0.5" style={{ color: 'var(--accent-primary)' }} />
            <span className="leading-snug">{q}</span>
          </button>
        ))}
      </div>

      {/* Bottom bar */}
      <div className="px-3 py-3 space-y-2" style={{ borderTop: '1px solid var(--border)' }}>
        {hasMessages && (
          <button onClick={onClear} className="sidebar-item w-full">
            <Trash2 className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--accent-danger)' }} />
            <span style={{ color: 'var(--accent-danger)' }}>Clear conversation</span>
          </button>
        )}

        {/* Groq status */}
        <div
          className="flex items-center gap-2 px-3 py-2 rounded-lg"
          style={{ backgroundColor: 'rgba(16,185,129,0.07)', border: '1px solid rgba(16,185,129,0.18)' }}
        >
          <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: 'var(--accent-success)' }} />
          <div className="min-w-0">
            <p className="text-xs font-medium" style={{ color: 'var(--accent-success)' }}>AI Mode · Groq</p>
            <p className="text-xs truncate font-mono" style={{ color: 'var(--text-tertiary)', fontSize: '0.65rem' }}>
              llama-3.1-8b-instant
            </p>
          </div>
          <Cpu className="w-3 h-3 flex-shrink-0 ml-auto" style={{ color: 'var(--accent-success)', opacity: 0.6 }} />
        </div>
      </div>
    </div>
  )
}
