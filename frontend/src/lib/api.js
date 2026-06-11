const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export const api = {
  async getCustomers(params = {}) {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== '') query.set(k, v)
    })
    const res = await fetch(`${API_BASE}/api/customers?${query}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  async getCustomer(id) {
    const res = await fetch(`${API_BASE}/api/customers/${id}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  async generateMessages(customerId, product = null) {
    const res = await fetch(`${API_BASE}/api/messages/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ customer_id: customerId, product }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  async chatRest(message, sessionId = 'default') {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  async getStatus() {
    const res = await fetch(`${API_BASE}/api/status`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  async getProviders() {
    const res = await fetch(`${API_BASE}/api/settings/providers`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  async updateLLMMode({ mode, provider, api_key, model }) {
    const res = await fetch(`${API_BASE}/api/settings/llm-mode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode, provider, api_key, model }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },

  getWebSocketUrl() {
    return `${WS_BASE}/ws/chat`
  },
}

export default api
