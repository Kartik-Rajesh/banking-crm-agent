import React, { useState } from 'react'
import { ChevronDown, ChevronUp, TrendingUp, User, MapPin, Briefcase } from 'lucide-react'
import { ScoreCard } from './ScoreCard'

function ScoreBadge({ score }) {
  const color =
    score >= 70 ? 'bg-green-500/20 text-green-400 border-green-500/30' :
    score >= 50 ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' :
                  'bg-red-500/20 text-red-400 border-red-500/30'

  return (
    <span className={`badge border ${color} font-mono font-bold`}>
      {score.toFixed(1)}
    </span>
  )
}

function ProbabilityBar({ value }) {
  const color = value >= 70 ? '#10b981' : value >= 50 ? '#f59e0b' : '#ef4444'
  return (
    <div className="flex items-center gap-2 min-w-[80px]">
      <div className="flex-1 bg-gray-700 rounded-full h-1.5 overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${value}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs text-gray-400 w-9">{value.toFixed(0)}%</span>
    </div>
  )
}

function CustomerRow({ customer, isExpanded, onToggle }) {
  const totalEmi = (customer.existing_loans || []).reduce((s, l) => s + (l.emi || 0), 0)
  const dti = customer.monthly_income > 0 ? (totalEmi / customer.monthly_income * 100).toFixed(0) : 0

  return (
    <>
      <tr
        className="border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors"
        onClick={onToggle}
      >
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
              <User className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">{customer.name}</p>
              <p className="text-xs text-gray-500 flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {customer.city}
              </p>
            </div>
          </div>
        </td>
        <td className="px-4 py-3">
          <ScoreBadge score={customer.conversion_score || 0} />
        </td>
        <td className="px-4 py-3">
          <ProbabilityBar value={customer.conversion_probability || 0} />
        </td>
        <td className="px-4 py-3">
          <p className="text-sm text-white">₹{(customer.monthly_income / 1000).toFixed(0)}K</p>
          <p className="text-xs text-gray-500">/month</p>
        </td>
        <td className="px-4 py-3">
          <span className={`badge ${
            customer.credit_score >= 750
              ? 'bg-green-500/20 text-green-400'
              : customer.credit_score >= 700
              ? 'bg-yellow-500/20 text-yellow-400'
              : 'bg-red-500/20 text-red-400'
          }`}>
            {customer.credit_score}
          </span>
        </td>
        <td className="px-4 py-3 hidden md:table-cell">
          <p className="text-xs text-gray-300 max-w-[160px] truncate">
            {customer.recommended_product || '—'}
          </p>
        </td>
        <td className="px-4 py-3 hidden lg:table-cell">
          <span className={`badge ${
            customer.occupation === 'SALARIED'
              ? 'bg-blue-500/20 text-blue-400'
              : 'bg-purple-500/20 text-purple-400'
          }`}>
            <Briefcase className="w-3 h-3 mr-1" />
            {customer.occupation === 'SALARIED' ? 'Salaried' : 'Self-Emp'}
          </span>
        </td>
        <td className="px-4 py-3">
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          )}
        </td>
      </tr>

      {isExpanded && (
        <tr className="bg-gray-900/50">
          <td colSpan={8} className="px-4 py-4">
            <ScoreCard customer={customer} />
          </td>
        </tr>
      )}
    </>
  )
}

export function CustomerTable({ customers = [] }) {
  const [expandedId, setExpandedId] = useState(null)
  const [sortField, setSortField] = useState('conversion_score')
  const [sortDir, setSortDir] = useState('desc')

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDir('desc')
    }
  }

  const sorted = [...customers].sort((a, b) => {
    const aVal = a[sortField] ?? 0
    const bVal = b[sortField] ?? 0
    return sortDir === 'desc' ? bVal - aVal : aVal - bVal
  })

  if (customers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-gray-500">
        <TrendingUp className="w-10 h-10 mb-3 opacity-30" />
        <p className="text-sm">No customers scored yet.</p>
        <p className="text-xs mt-1">Send a query to the agent to find leads.</p>
      </div>
    )
  }

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <ChevronDown className="w-3 h-3 opacity-30" />
    return sortDir === 'desc' ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10">
            <th className="px-4 py-3 text-left text-xs text-gray-400 uppercase tracking-wider">Customer</th>
            <th
              className="px-4 py-3 text-left text-xs text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white"
              onClick={() => handleSort('conversion_score')}
            >
              <div className="flex items-center gap-1">Score <SortIcon field="conversion_score" /></div>
            </th>
            <th
              className="px-4 py-3 text-left text-xs text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white"
              onClick={() => handleSort('conversion_probability')}
            >
              <div className="flex items-center gap-1">Probability <SortIcon field="conversion_probability" /></div>
            </th>
            <th
              className="px-4 py-3 text-left text-xs text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white"
              onClick={() => handleSort('monthly_income')}
            >
              <div className="flex items-center gap-1">Income <SortIcon field="monthly_income" /></div>
            </th>
            <th
              className="px-4 py-3 text-left text-xs text-gray-400 uppercase tracking-wider cursor-pointer hover:text-white"
              onClick={() => handleSort('credit_score')}
            >
              <div className="flex items-center gap-1">Credit <SortIcon field="credit_score" /></div>
            </th>
            <th className="px-4 py-3 text-left text-xs text-gray-400 uppercase tracking-wider hidden md:table-cell">Product</th>
            <th className="px-4 py-3 text-left text-xs text-gray-400 uppercase tracking-wider hidden lg:table-cell">Type</th>
            <th className="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          {sorted.map(customer => (
            <CustomerRow
              key={customer.id}
              customer={customer}
              isExpanded={expandedId === customer.id}
              onToggle={() => setExpandedId(prev => prev === customer.id ? null : customer.id)}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}
