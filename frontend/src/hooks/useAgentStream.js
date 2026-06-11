import { useState, useRef, useCallback } from 'react'
import api from '../lib/api'

const STREAM_TIMEOUT_MS = 60_000

export function useAgentStream() {
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [thinkingSteps, setThinkingSteps] = useState([])
  const [customers, setCustomers] = useState([])
  const [generatedMessages, setGeneratedMessages] = useState([])
  const wsRef = useRef(null)
  const timeoutRef = useRef(null)
  const sessionId = useRef(`session_${Date.now()}`)

  const sendMessage = useCallback(async (query) => {
    if (!query.trim() || isStreaming) return

    const userMsg = { role: 'user', content: query, id: Date.now() }
    setMessages(prev => [...prev, userMsg])
    setIsStreaming(true)
    setThinkingSteps([])

    const agentMsgId = Date.now() + 1
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: '',
      id: agentMsgId,
      isStreaming: true,
      thinkingSteps: [],
    }])

    // Close any existing connection + timeout
    if (wsRef.current) wsRef.current.close()
    if (timeoutRef.current) clearTimeout(timeoutRef.current)

    const ws = new WebSocket(api.getWebSocketUrl())
    wsRef.current = ws

    let accumulatedText = ''
    const steps = []

    const clearStreamTimeout = () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
    }

    // Safety net: show error if backend goes silent for 60 seconds
    timeoutRef.current = setTimeout(() => {
      ws.close()
      setMessages(prev => prev.map(m =>
        m.id === agentMsgId
          ? {
              ...m,
              content: '⏱️ **Request timed out after 60 seconds.**\n\nThe agent did not respond in time. Please try again.',
              isStreaming: false,
              isError: true,
            }
          : m
      ))
      setIsStreaming(false)
    }, STREAM_TIMEOUT_MS)

    ws.onopen = () => {
      ws.send(JSON.stringify({ message: query, session_id: sessionId.current }))
    }

    ws.onmessage = (event) => {
      try {
        const chunk = JSON.parse(event.data)

        if (chunk.type === 'thinking') {
          const step = {
            step: chunk.step,
            message: chunk.message,
            tool_call: chunk.tool_call,
            id: Date.now() + Math.random(),
          }
          steps.push(step)
          setThinkingSteps([...steps])
          setMessages(prev => prev.map(m =>
            m.id === agentMsgId ? { ...m, thinkingSteps: [...steps] } : m
          ))

        } else if (chunk.type === 'customers_ready') {
          // Scored leads available — populate table immediately, before messages arrive
          setCustomers(chunk.customers)

        } else if (chunk.type === 'partial_result') {
          // Messages ready
          if (chunk.customers !== undefined) setCustomers(chunk.customers)
          if (chunk.messages !== undefined) setGeneratedMessages(chunk.messages)

        } else if (chunk.type === 'result') {
          // Final consolidated state — ensure consistency
          if (chunk.customers) setCustomers(chunk.customers)
          if (chunk.messages) setGeneratedMessages(chunk.messages)

        } else if (chunk.type === 'text') {
          accumulatedText += chunk.content
          setMessages(prev => prev.map(m =>
            m.id === agentMsgId ? { ...m, content: accumulatedText } : m
          ))

        } else if (chunk.type === 'done') {
          clearStreamTimeout()
          setMessages(prev => prev.map(m =>
            m.id === agentMsgId
              ? { ...m, isStreaming: false, content: accumulatedText }
              : m
          ))
          setIsStreaming(false)
          ws.close()

        } else if (chunk.type === 'error') {
          clearStreamTimeout()
          setMessages(prev => prev.map(m =>
            m.id === agentMsgId
              ? { ...m, content: `⚠️ Error: ${chunk.message}`, isStreaming: false, isError: true }
              : m
          ))
          setIsStreaming(false)
          ws.close()
        }
      } catch (e) {
        console.error('Parse error:', e)
      }
    }

    ws.onerror = (err) => {
      clearStreamTimeout()
      console.error('WebSocket error:', err)
      setMessages(prev => prev.map(m =>
        m.id === agentMsgId
          ? { ...m, content: '⚠️ Connection error. Please check if the backend is running.', isStreaming: false, isError: true }
          : m
      ))
      setIsStreaming(false)
    }

    ws.onclose = () => {
      clearStreamTimeout()
      setIsStreaming(false)
    }
  }, [isStreaming])

  const clearConversation = useCallback(() => {
    setMessages([])
    setThinkingSteps([])
    setCustomers([])
    setGeneratedMessages([])
  }, [])

  return {
    messages,
    isStreaming,
    thinkingSteps,
    customers,
    generatedMessages,
    sendMessage,
    clearConversation,
  }
}
