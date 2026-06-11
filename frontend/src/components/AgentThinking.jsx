import React from 'react'
import { Search, BarChart2, Filter, MessageSquare, CheckCircle, Loader2, Database } from 'lucide-react'

const STEP_CONFIG = {
  start:                  { icon: Loader2,       label: 'Starting Agent',           color: 'var(--accent-primary)' },
  understand_intent:      { icon: Search,        label: 'Understanding Query',       color: 'var(--accent-purple)' },
  retrieve_customers:     { icon: Database,      label: 'Retrieving Customers',      color: 'var(--accent-primary)' },
  score_customers:        { icon: BarChart2,     label: 'Scoring Leads',             color: 'var(--accent-warning)' },
  filter_top_candidates:  { icon: Filter,        label: 'Filtering Top Candidates',  color: '#f97316' },
  generate_messages:      { icon: MessageSquare, label: 'Crafting Messages',          color: 'var(--accent-success)' },
  synthesize_response:    { icon: CheckCircle,   label: 'Synthesizing Response',      color: 'var(--accent-success)' },
}

export function AgentThinking({ steps = [], isStreaming }) {
  if (!isStreaming && steps.length === 0) return null

  return (
    <div className="py-2 space-y-0">
      {isStreaming && steps.length === 0 && (
        <div
          className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg animate-fade-in"
          style={{ backgroundColor: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.18)' }}
        >
          <Loader2 className="w-3.5 h-3.5 animate-spin flex-shrink-0" style={{ color: 'var(--accent-primary)' }} />
          <span className="text-xs font-medium" style={{ color: 'var(--accent-primary)' }}>Agent is thinking…</span>
        </div>
      )}

      {steps.map((step, i) => {
        const isLast   = i === steps.length - 1
        const isActive = isLast && isStreaming
        const cfg      = STEP_CONFIG[step.step] || STEP_CONFIG.start
        const Icon     = cfg.icon
        const isFirst  = i === 0

        return (
          <div key={step.id || i} className="flex gap-3 animate-slide-up" style={{ paddingTop: isFirst ? 0 : '2px' }}>
            {/* Timeline spine */}
            <div className="flex flex-col items-center" style={{ width: '20px', flexShrink: 0 }}>
              <div
                className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 z-10"
                style={{
                  backgroundColor: isActive ? `${cfg.color}1a` : 'rgba(255,255,255,0.06)',
                  border: `1px solid ${isActive ? cfg.color : 'var(--border)'}`,
                }}
              >
                {isActive
                  ? <Loader2 className="w-2.5 h-2.5 animate-spin" style={{ color: cfg.color }} />
                  : <CheckCircle className="w-2.5 h-2.5" style={{ color: 'var(--accent-success)' }} />
                }
              </div>
              {i < steps.length - 1 && (
                <div className="w-px flex-1 mt-0.5" style={{ backgroundColor: 'var(--border)', minHeight: '12px' }} />
              )}
            </div>

            {/* Step content */}
            <div className="pb-3 min-w-0 flex-1" style={{ paddingBottom: i < steps.length - 1 ? '0' : '4px' }}>
              <p className="text-xs font-semibold leading-5" style={{ color: isActive ? cfg.color : 'var(--text-secondary)' }}>
                {cfg.label}
              </p>
              {step.message && (
                <p className="text-xs mt-0.5 leading-relaxed" style={{ color: 'var(--text-tertiary)' }}>
                  {step.message}
                </p>
              )}
              {step.tool_call && (
                <code
                  className="inline-block mt-1 text-xs px-2 py-0.5 rounded font-mono"
                  style={{
                    backgroundColor: 'var(--bg-elevated)',
                    color: 'var(--accent-primary)',
                    fontSize: '0.65rem',
                  }}
                >
                  {step.tool_call}
                </code>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
