import React, { useState } from 'react'
import { Copy, Check, Send, MessageCircle } from 'lucide-react'

const TONE_CONFIG = {
  formal: { label: 'Formal', emoji: '💼', activeStyle: { backgroundColor: 'rgba(59,130,246,0.15)', color: 'var(--accent-primary)', border: '1px solid rgba(59,130,246,0.3)' } },
  casual: { label: 'Casual', emoji: '😊', activeStyle: { backgroundColor: 'rgba(16,185,129,0.15)', color: 'var(--accent-success)', border: '1px solid rgba(16,185,129,0.3)' } },
  urgent: { label: 'Urgent', emoji: '⚡', activeStyle: { backgroundColor: 'rgba(245,158,11,0.15)', color: 'var(--accent-warning)', border: '1px solid rgba(245,158,11,0.3)' } },
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      const el = document.createElement('textarea')
      el.value = text
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-all duration-150"
      style={{
        backgroundColor: copied ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.05)',
        color: copied ? 'var(--accent-success)' : 'var(--text-secondary)',
        border: `1px solid ${copied ? 'rgba(16,185,129,0.3)' : 'var(--border)'}`,
      }}
    >
      {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}

function MockSendButton() {
  const [sent, setSent] = useState(false)

  return (
    <button
      onClick={() => { setSent(true); setTimeout(() => setSent(false), 3000) }}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150"
      style={{
        backgroundColor: sent ? 'var(--accent-success)' : 'rgba(16,185,129,0.12)',
        color: sent ? '#fff' : 'var(--accent-success)',
        border: `1px solid ${sent ? 'var(--accent-success)' : 'rgba(16,185,129,0.3)'}`,
      }}
    >
      <Send className="w-3.5 h-3.5" />
      {sent ? 'Sent ✓' : 'Approve & Send'}
    </button>
  )
}

export function MessagePreview({ messageData }) {
  const [activeTone, setActiveTone] = useState('formal')
  const { customer_name, product, variants = [] } = messageData
  const activeVariant = variants.find(v => v.tone === activeTone) || variants[0]

  if (!activeVariant) return null

  return (
    <div className="card overflow-hidden animate-fade-in">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <div>
          <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{customer_name}</p>
          {product && <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>{product}</p>}
        </div>
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ backgroundColor: 'rgba(37,211,102,0.1)' }}
        >
          <MessageCircle className="w-4 h-4" style={{ color: '#25D366' }} />
        </div>
      </div>

      {/* Tone selector */}
      <div className="flex gap-2 px-4 pt-3">
        {variants.map(v => {
          const cfg      = TONE_CONFIG[v.tone] || { label: v.tone, emoji: '💬', activeStyle: {} }
          const isActive = activeTone === v.tone
          return (
            <button
              key={v.tone}
              onClick={() => setActiveTone(v.tone)}
              className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all duration-150"
              style={isActive
                ? cfg.activeStyle
                : { color: 'var(--text-tertiary)', border: '1px solid transparent' }
              }
            >
              <span>{cfg.emoji}</span>
              <span>{cfg.label}</span>
            </button>
          )
        })}
      </div>

      {/* WhatsApp preview */}
      <div className="p-4">
        <div
          className="rounded-xl p-3"
          style={{ backgroundColor: 'var(--bg-elevated)' }}
        >
          {/* Chat header */}
          <div className="flex items-center gap-2.5 pb-2.5 mb-2.5" style={{ borderBottom: '1px solid var(--border)' }}>
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: 'rgba(37,211,102,0.12)' }}
            >
              <MessageCircle className="w-3.5 h-3.5" style={{ color: '#25D366' }} />
            </div>
            <div>
              <p className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>Relationship Manager</p>
              <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>WhatsApp · just now</p>
            </div>
          </div>

          {/* Bubble */}
          <div
            className="rounded-xl rounded-tl-none px-3.5 py-2.5 text-xs leading-relaxed inline-block max-w-full"
            style={{ backgroundColor: '#dcf8c6', color: '#111' }}
          >
            {activeVariant.content}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 px-4 pb-4">
        <CopyButton text={activeVariant.content} />
        <MockSendButton />
      </div>
    </div>
  )
}
