import React, { useState, useEffect } from 'react'
import { X, Key, Wifi, WifiOff, Settings2, Loader2 } from 'lucide-react'
import api from '../lib/api'

const FALLBACK_PROVIDERS = [
  {
    id: 'gemini', label: 'Gemini', subtitle: 'Google AI',
    models: ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-2.5-flash'],
    default_model: 'gemini-2.0-flash', key_placeholder: 'AIzaSy...',
  },
  {
    id: 'groq', label: 'Groq', subtitle: 'Groq Cloud',
    models: ['llama-3.1-70b-versatile', 'llama3-8b-8192', 'mixtral-8x7b-32768'],
    default_model: 'llama-3.1-70b-versatile', key_placeholder: 'gsk_...',
  },
  {
    id: 'anthropic', label: 'Anthropic', subtitle: 'Claude',
    models: ['claude-haiku-4-5-20251001', 'claude-3-5-haiku-20241022', 'claude-3-5-sonnet-20241022'],
    default_model: 'claude-haiku-4-5-20251001', key_placeholder: 'sk-ant-...',
  },
]

export function LLMSettings({ currentStatus, onClose, onSaved }) {
  const [providers, setProviders] = useState(FALLBACK_PROVIDERS)
  const [mode, setMode] = useState(currentStatus?.llm_available ? 'online' : 'offline')
  const [provider, setProvider] = useState(currentStatus?.provider || 'gemini')
  const [model, setModel] = useState(currentStatus?.model || '')
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [loading, setLoading] = useState(false)

  const currentProvider = providers.find(p => p.id === provider) || providers[0]

  // Default model when provider changes
  useEffect(() => {
    if (!model || !currentProvider.models.includes(model)) {
      setModel(currentProvider.default_model)
    }
  }, [provider])

  // Load provider list from backend
  useEffect(() => {
    api.getProviders()
      .then(d => setProviders(d.providers))
      .catch(() => {/* keep fallback */})
  }, [])

  const handleProviderChange = (pid) => {
    setProvider(pid)
    const p = providers.find(x => x.id === pid)
    if (p) setModel(p.default_model)
  }

  const handleSave = async () => {
    setLoading(true)
    try {
      const result = await api.updateLLMMode({
        mode,
        provider: mode === 'online' ? provider : undefined,
        api_key: apiKey.trim() || undefined,
        model: mode === 'online' ? model : undefined,
      })
      onSaved(result)
      onClose()
    } catch (err) {
      onSaved({ success: false, error: err.message })
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative bg-gray-900 border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl mx-4"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-white font-semibold text-sm flex items-center gap-2">
            <Settings2 className="w-4 h-4 text-blue-400" />
            LLM Configuration
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Mode toggle */}
        <div className="mb-5">
          <label className="text-xs text-gray-400 uppercase tracking-wider mb-2 block">Mode</label>
          <div className="flex gap-2">
            {[
              { id: 'online', icon: Wifi, label: 'Online', desc: 'Use AI for enhanced responses' },
              { id: 'offline', icon: WifiOff, label: 'Offline', desc: 'Pure Python, instant responses' },
            ].map(({ id, icon: Icon, label }) => (
              <button
                key={id}
                onClick={() => setMode(id)}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium border transition-all ${
                  mode === id
                    ? id === 'online'
                      ? 'bg-green-500/15 border-green-500/40 text-green-400'
                      : 'bg-yellow-500/15 border-yellow-500/40 text-yellow-400'
                    : 'bg-white/5 border-white/10 text-gray-500 hover:text-gray-300 hover:bg-white/10'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </button>
            ))}
          </div>
        </div>

        {mode === 'online' && (
          <>
            {/* Provider selection */}
            <div className="mb-4">
              <label className="text-xs text-gray-400 uppercase tracking-wider mb-2 block">Provider</label>
              <div className="grid grid-cols-3 gap-2">
                {providers.map(p => (
                  <button
                    key={p.id}
                    onClick={() => handleProviderChange(p.id)}
                    className={`py-2 px-2 rounded-lg text-center border transition-all ${
                      provider === p.id
                        ? 'bg-blue-500/20 border-blue-500/40 text-blue-400'
                        : 'bg-white/5 border-white/10 text-gray-400 hover:text-gray-200 hover:bg-white/10'
                    }`}
                  >
                    <div className="text-xs font-semibold">{p.label}</div>
                    <div className="text-xs opacity-50 mt-0.5">{p.subtitle}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* API Key */}
            <div className="mb-4">
              <label className="text-xs text-gray-400 uppercase tracking-wider mb-2 block">API Key</label>
              <div className="relative">
                <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500 pointer-events-none" />
                <input
                  type={showKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={e => setApiKey(e.target.value)}
                  placeholder={currentProvider.key_placeholder}
                  className="w-full bg-gray-800 border border-white/10 rounded-lg pl-9 pr-16 py-2.5 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-500 hover:text-gray-300 transition-colors"
                >
                  {showKey ? 'Hide' : 'Show'}
                </button>
              </div>
              <p className="text-xs text-gray-600 mt-1.5">
                Leave blank to keep the currently configured key.
              </p>
            </div>

            {/* Model */}
            <div className="mb-5">
              <label className="text-xs text-gray-400 uppercase tracking-wider mb-2 block">Model</label>
              <select
                value={model}
                onChange={e => setModel(e.target.value)}
                className="w-full bg-gray-800 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all appearance-none cursor-pointer"
              >
                {currentProvider.models.map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl border border-white/10 text-sm text-gray-400 hover:text-white hover:bg-white/5 transition-all"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="flex-1 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm font-medium text-white transition-all flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Testing...
              </>
            ) : mode === 'online' ? 'Save & Test LLM' : 'Switch to Offline'}
          </button>
        </div>
      </div>
    </div>
  )
}
