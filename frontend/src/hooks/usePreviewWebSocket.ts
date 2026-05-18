import { useEffect, useRef, useCallback } from "react"
import { usePreviewDispatch } from "../context/PreviewContext"
import type { AgentTraceEvent } from "../types/preview"

const WS_BASE = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`

export function usePreviewWebSocket(sessionId: string | null) {
  const dispatch = usePreviewDispatch()
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!sessionId) return

    const ws = new WebSocket(`${WS_BASE}/ws/preview/${sessionId}`)
    wsRef.current = ws

    ws.onopen = () => {
      dispatch({ type: "SET_CONNECTED", payload: true })
    }

    ws.onclose = () => {
      dispatch({ type: "SET_CONNECTED", payload: false })
    }

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)

      switch (msg.type) {
        case "preview.run_started":
          dispatch({ type: "RUN_STARTED" })
          break

        case "preview.trace_line": {
          const evt = msg.payload.event as AgentTraceEvent
          dispatch({ type: "APPEND_TRACE", payload: evt })
          break
        }

        case "preview.run_complete":
          dispatch({
            type: "RUN_COMPLETE",
            payload: {
              exit_code: msg.payload.exit_code,
              duration_ms: msg.payload.duration_ms,
              output: msg.payload.output,
            },
          })
          break

        case "preview.run_error":
          dispatch({ type: "RUN_ERROR", payload: msg.payload.message })
          break
      }
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [sessionId, dispatch])

  const requestStream = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "preview.request_stream" }))
    }
  }, [])

  return { requestStream }
}
