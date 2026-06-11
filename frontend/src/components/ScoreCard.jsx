import React from 'react'
import { TrendingUp, CreditCard, DollarSign, Wallet, Activity, Bell } from 'lucide-react'

const FACTORS = [
  { key: 'income_stability',      label: 'Income Stability',    icon: TrendingUp, color: 'var(--accent-primary)',  weight: '25%' },
  { key: 'credit_score',          label: 'Credit Score',        icon: CreditCard, color: 'var(--accent-purple)',   weight: '20%' },
  { key: 'debt_to_income_ratio',  label: 'Debt-to-Income',      icon: DollarSign, color: 'var(--accent-warning)',  weight: '20%' },
  { key: 'account_balance',       label: 'Account Balance',     icon: Wallet,     color: 'var(--accent-success)',  weight: '15%' },
  { key: 'transaction_regularity',label: 'Transaction Activity', icon: Activity,   color: '#06b6d4',                weight: '10%' },
  { key: 'loan_enquiry_recency',  label: 'Recent Enquiry',      icon: Bell,       color: '#f43f5e',                weight: '10%' },
]

function FactorBar({ value, color, index }) {
  const pct = Math.round(value * 100)
  const barClass = pct >= 75 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-red-500'

  return (
    <div className="flex items-center gap-2.5">
      <div className="score-bar-track">
        <div
          className={`score-bar-fill ${barClass}`}
          style={{ '--bar-width': `${pct}%`, animationDelay: `${index * 80}ms` }}
        />
      </div>
      <span
        className="text-xs font-mono font-medium flex-shrink-0"
        style={{ color: 'var(--text-secondary)', width: '32px', textAlign: 'right' }}
      >
        {pct}%
      </span>
    </div>
  )
}

export function ScoreCard({ customer, barBaseDelay = 0 }) {
  const breakdown  = customer.score_breakdown || {}
  const score      = customer.conversion_score || 0
  const probability = customer.conversion_probability || 0

  const scoreColor =
    score >= 75 ? 'var(--accent-success)' :
    score >= 50 ? 'var(--accent-warning)' :
                  'var(--accent-danger)'

  return (
    <div
      className="rounded-xl p-4 animate-fade-in"
      style={{ backgroundColor: 'var(--bg-elevated)', border: '1px solid var(--border)' }}
    >
      {/* Score header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-xs uppercase tracking-widest mb-1" style={{ color: 'var(--text-tertiary)' }}>
            Conversion Score
          </p>
          <div className="flex items-baseline gap-1.5">
            <span className="text-3xl font-bold font-mono" style={{ color: scoreColor }}>
              {score.toFixed(1)}
            </span>
            <span className="text-sm" style={{ color: 'var(--text-tertiary)' }}>/100</span>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs uppercase tracking-widest mb-1" style={{ color: 'var(--text-tertiary)' }}>
            Probability
          </p>
          <p className="text-xl font-bold font-mono" style={{ color: scoreColor }}>
            {probability.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Factor breakdown */}
      <div className="space-y-3">
        {FACTORS.map(({ key, label, icon: Icon, color, weight }, i) => {
          const value = breakdown[key] ?? 0
          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-1.5">
                  <Icon className="w-3 h-3 flex-shrink-0" style={{ color }} />
                  <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{label}</span>
                </div>
                <span className="text-xs font-mono" style={{ color: 'var(--text-tertiary)' }}>{weight}</span>
              </div>
              <FactorBar value={value} color={color} index={barBaseDelay + i} />
            </div>
          )
        })}
      </div>

      {/* Reasoning */}
      {customer.score_reasoning && (
        <div className="mt-4 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
          <p className="text-xs uppercase tracking-widest mb-1.5" style={{ color: 'var(--text-tertiary)' }}>
            Analysis
          </p>
          <p className="text-xs italic leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            {customer.score_reasoning}
          </p>
        </div>
      )}
    </div>
  )
}
