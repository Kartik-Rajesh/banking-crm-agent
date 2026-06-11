import React, { useState } from 'react'
import { ChevronDown, ChevronUp, MapPin, Briefcase, TrendingUp } from 'lucide-react'
import { ScoreCard } from './ScoreCard'

function getScoreClass(score) {
  if (score >= 75) return 'badge-green'
  if (score >= 50) return 'badge-amber'
  return 'badge-red'
}

function getBarClass(pct) {
  if (pct >= 75) return 'bg-emerald-500'
  if (pct >= 50) return 'bg-amber-500'
  return 'bg-red-500'
}

function Initials({ name, score }) {
  const parts    = (name || 'U').split(' ')
  const initials = parts.length >= 2
    ? parts[0][0] + parts[parts.length - 1][0]
    : parts[0].slice(0, 2)
  const bg =
    score >= 75 ? 'rgba(16,185,129,0.18)' :
    score >= 50 ? 'rgba(245,158,11,0.18)' :
                  'rgba(239,68,68,0.18)'
  const fg =
    score >= 75 ? 'var(--accent-success)' :
    score >= 50 ? 'var(--accent-warning)' :
                  'var(--accent-danger)'

  return (
    <div
      className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 text-sm font-bold font-mono"
      style={{ backgroundColor: bg, color: fg }}
    >
      {initials.toUpperCase()}
    </div>
  )
}

export function CustomerCard({ customer, index }) {
  const [expanded, setExpanded] = useState(false)

  const score       = customer.conversion_score || 0
  const probability = customer.conversion_probability || 0
  const income      = customer.monthly_income || 0
  const pct         = Math.round(probability)
  const barClass    = getBarClass(pct)
  const scoreClass  = getScoreClass(score)

  const occBadge = customer.occupation === 'SALARIED' ? 'badge-blue' : 'badge-purple'
  const occLabel = customer.occupation === 'SALARIED' ? 'Salaried' : 'Self-Emp'

  return (
    <div
      className="card animate-slide-up overflow-hidden"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      {/* Card header row */}
      <button
        className="w-full flex items-center gap-3 px-4 py-3 text-left transition-colors duration-150"
        style={{ backgroundColor: expanded ? 'var(--bg-elevated)' : 'transparent' }}
        onMouseEnter={e => !expanded && (e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.03)')}
        onMouseLeave={e => !expanded && (e.currentTarget.style.backgroundColor = 'transparent')}
        onClick={() => setExpanded(v => !v)}
      >
        <Initials name={customer.name} score={score} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <p className="text-sm font-semibold truncate" style={{ color: 'var(--text-primary)' }}>
              {customer.name}
            </p>
            <span className={`badge ${scoreClass} flex-shrink-0`}>
              {score.toFixed(1)}
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-tertiary)' }}>
            <MapPin className="w-3 h-3 flex-shrink-0" />
            <span>{customer.city}</span>
            <span className="opacity-40">·</span>
            <span className={`badge ${occBadge} py-0`}>{occLabel}</span>
          </div>
        </div>

        <div className="flex-shrink-0" style={{ color: 'var(--text-tertiary)' }}>
          {expanded
            ? <ChevronUp className="w-4 h-4" />
            : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Animated score bar + stats row */}
      <div className="px-4 pb-3" style={{ borderTop: `1px solid var(--border)` }}>
        {/* Progress bar */}
        <div className="flex items-center gap-2.5 py-2.5">
          <div className="score-bar-track">
            <div
              className={`score-bar-fill ${barClass}`}
              style={{ '--bar-width': `${pct}%`, animationDelay: `${index * 80}ms` }}
            />
          </div>
          <span
            className="text-xs font-mono font-semibold flex-shrink-0"
            style={{ color: pct >= 75 ? 'var(--accent-success)' : pct >= 50 ? 'var(--accent-warning)' : 'var(--accent-danger)', width: '34px' }}
          >
            {pct}%
          </span>
        </div>

        {/* Stats row */}
        <div className="flex items-center gap-4 text-xs" style={{ color: 'var(--text-secondary)' }}>
          <span>
            <span className="font-mono font-semibold" style={{ color: 'var(--text-primary)' }}>
              ₹{income >= 100000
                ? `${(income / 100000).toFixed(1)}L`
                : `${(income / 1000).toFixed(0)}K`}
            </span>
            <span style={{ color: 'var(--text-tertiary)' }}>/mo</span>
          </span>
          <span style={{ color: 'var(--border)' }}>|</span>
          <span>
            CIBIL{' '}
            <span
              className="font-mono font-semibold"
              style={{
                color: customer.credit_score >= 750
                  ? 'var(--accent-success)'
                  : customer.credit_score >= 700
                  ? 'var(--accent-warning)'
                  : 'var(--accent-danger)',
              }}
            >
              {customer.credit_score}
            </span>
          </span>
          {customer.recommended_product && (
            <>
              <span style={{ color: 'var(--border)' }}>|</span>
              <span className="truncate" style={{ color: 'var(--text-tertiary)' }}>
                {customer.recommended_product}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Expanded: full ScoreCard */}
      {expanded && (
        <div className="px-4 pb-4 animate-fade-in" style={{ borderTop: `1px solid var(--border)` }}>
          <ScoreCard customer={customer} barBaseDelay={0} />
        </div>
      )}
    </div>
  )
}

export function CustomerCardList({ customers = [] }) {
  if (customers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center px-6">
        <TrendingUp className="w-10 h-10 mb-3 opacity-20" style={{ color: 'var(--text-tertiary)' }} />
        <p className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>No leads scored yet</p>
        <p className="text-xs mt-1" style={{ color: 'var(--text-tertiary)' }}>Ask the agent to find and rank loan candidates.</p>
      </div>
    )
  }

  const sorted = [...customers].sort((a, b) => (b.conversion_score || 0) - (a.conversion_score || 0))

  return (
    <div className="p-3 space-y-2">
      {sorted.map((customer, i) => (
        <CustomerCard key={customer.id} customer={customer} index={i} />
      ))}
    </div>
  )
}
