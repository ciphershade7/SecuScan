import { useEffect, useRef, useState, useCallback } from 'react'
import { WS_BASE, getStoredApiKey } from '../api'

export interface WSMessage {
  task_id: string
  event: string
  data: unknown
}

export interface UseWebSocketOptions {
  /** Task IDs to subscribe to immediately on connect */
  taskIds?: string[]
  /** Called for every incoming message */
  onMessage?: (msg: WSMessage) => void
  /** Called on connection open */
  onOpen?: () => void
  /** Called on connection close */
  onClose?: () => void
  /** Max reconnection attempts before giving up */
  maxReconnectAttempts?: number
  /** Base delay in ms for exponential backoff */
  reconnectBaseDelay?: number
  /** Whether the hook should be active */
  enabled?: boolean
}

export interface UseWebSocketResult {
  isConnected: boolean
  /** Send a subscribe message to the WebSocket */
  subscribe: (taskIds: string[]) => void
  /** Send an unsubscribe message */
  unsubscribe: (taskIds: string[]) => void
  /** Send a raw JSON message */
  send: (msg: Record<string, unknown>) => void
}

/**
 * Hook for managing a persistent WebSocket connection to the SecuScan
 * real-time feed at /ws/feed.
 *
 * Handles:
 * - Auth handshake (sends API key as first message)
 * - Auto-reconnect with exponential backoff
 * - Task subscription management
 * - Keepalive pings
 */
export function useWebSocket({
  taskIds = [],
  onMessage,
  onOpen,
  onClose,
  maxReconnectAttempts = 8,
  reconnectBaseDelay = 1000,
  enabled = true,
}: UseWebSocketOptions): UseWebSocketResult {
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptRef = useRef(0)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const cleanupRef = useRef(false)
  const taskIdsRef = useRef(taskIds)
  const onMessageRef = useRef(onMessage)
  const onOpenRef = useRef(onOpen)
  const onCloseRef = useRef(onClose)

  // Keep refs in sync
  onMessageRef.current = onMessage
  onOpenRef.current = onOpen
  onCloseRef.current = onClose
  taskIdsRef.current = taskIds

  const cleanup = useCallback(() => {
    cleanupRef.current = true
    if (pingTimerRef.current) {
      clearInterval(pingTimerRef.current)
      pingTimerRef.current = null
    }
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  const sendRaw = useCallback((msg: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }, [])

  const subscribeFn = useCallback((ids: string[]) => {
    if (ids.length > 0) {
      sendRaw({ subscribe: ids })
    }
  }, [sendRaw])

  const unsubscribeFn = useCallback((ids: string[]) => {
    if (ids.length > 0) {
      sendRaw({ unsubscribe: ids })
    }
  }, [sendRaw])

  const connect = useCallback(() => {
    if (cleanupRef.current) return

    const apiKey = getStoredApiKey()
    if (!apiKey) return // Can't auth without a key

    const url = `${WS_BASE}/ws/feed`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      if (cleanupRef.current) return
      // Send auth as first message
      ws.send(JSON.stringify({ auth: apiKey }))
    }

    ws.onmessage = (ev) => {
      if (cleanupRef.current) return

      let msg: Record<string, unknown>
      try {
        msg = JSON.parse(ev.data)
      } catch {
        return
      }

      // Handle auth response
      if (msg.event === 'authenticated') {
        reconnectAttemptRef.current = 0
        setIsConnected(true)
        onOpenRef.current?.()

        // Subscribe to initial task IDs
        if (taskIdsRef.current.length > 0) {
          ws.send(JSON.stringify({ subscribe: taskIdsRef.current }))
        }

        // Start keepalive pings every 30s
        if (pingTimerRef.current) clearInterval(pingTimerRef.current)
        pingTimerRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ ping: true }))
          }
        }, 30000)
        return
      }

      // Handle auth errors
      if (msg.error) {
        setIsConnected(false)
        return
      }

      // Handle pong (keepalive response) — just ignore it
      if (msg.pong) return

      // Forward all other messages (task events)
      if (msg.task_id && msg.event) {
        onMessageRef.current?.(msg as unknown as WSMessage)
      }
    }

    ws.onerror = () => {
      // onclose will fire after this
    }

    ws.onclose = () => {
      if (cleanupRef.current) return
      setIsConnected(false)
      onCloseRef.current?.()

      if (pingTimerRef.current) {
        clearInterval(pingTimerRef.current)
        pingTimerRef.current = null
      }

      // Reconnect with exponential backoff
      if (reconnectAttemptRef.current < maxReconnectAttempts) {
        const delay = reconnectBaseDelay * Math.pow(2, reconnectAttemptRef.current)
        reconnectAttemptRef.current++
        reconnectTimerRef.current = setTimeout(() => {
          if (!cleanupRef.current) connect()
        }, delay)
      }
    }
  }, [maxReconnectAttempts, reconnectBaseDelay])

  useEffect(() => {
    if (!enabled) {
      cleanup()
      return
    }

    cleanupRef.current = false
    reconnectAttemptRef.current = 0
    connect()

    return () => {
      cleanup()
    }
  }, [enabled, connect, cleanup])

  // Re-subscribe when taskIds change while connected
  useEffect(() => {
    if (isConnected && taskIds.length > 0) {
      subscribeFn(taskIds)
    }
  }, [taskIds, isConnected, subscribeFn])

  return {
    isConnected,
    subscribe: subscribeFn,
    unsubscribe: unsubscribeFn,
    send: sendRaw,
  }
}
