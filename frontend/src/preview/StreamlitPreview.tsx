import { useState, useEffect, useCallback, useRef } from "react"
import { startStreamlit, stopStreamlit, getStreamlitStatus } from "../api/streamlit"

type State = "idle" | "starting" | "polling" | "running" | "error"

export function StreamlitPreview({ sessionId }: { sessionId: string }) {
  const [state, setState] = useState<State>("idle")
  const [url, setUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Check if already running on mount
  useEffect(() => {
    getStreamlitStatus(sessionId).then((s) => {
      if (s.running && s.url) {
        setUrl(s.url)
        setState("running")
      }
    }).catch(() => {})
  }, [sessionId])

  const clearPoll = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  useEffect(() => () => clearPoll(), [clearPoll])

  const handleLaunch = useCallback(async () => {
    setState("starting")
    setError(null)
    try {
      const result = await startStreamlit(sessionId)
      setUrl(result.url)
      setState("polling")

      // Poll until Streamlit is responsive (up to 30s)
      let attempts = 0
      pollRef.current = setInterval(async () => {
        attempts++
        try {
          await fetch(result.url, { mode: "no-cors" })
          // no-cors always gives opaque response, but if it doesn't throw, server is up
          clearPoll()
          setState("running")
        } catch {
          if (attempts > 60) {
            clearPoll()
            setError("Streamlit took too long to start")
            setState("error")
          }
        }
      }, 500)
    } catch (e) {
      setError((e as Error).message)
      setState("error")
    }
  }, [sessionId, clearPoll])

  const handleStop = useCallback(async () => {
    clearPoll()
    try {
      await stopStreamlit(sessionId)
    } catch {}
    setUrl(null)
    setState("idle")
  }, [sessionId, clearPoll])

  return (
    <div className="flex flex-col h-full">
      {/* Controls bar */}
      <div className="flex items-center gap-3 px-4 py-2 border-b border-border bg-surface shrink-0">
        {state === "idle" || state === "error" ? (
          <button
            onClick={handleLaunch}
            className="px-3 py-1.5 text-[12px] font-medium bg-accent text-white rounded hover:bg-accent/90 transition-colors"
          >
            Launch App
          </button>
        ) : state === "starting" || state === "polling" ? (
          <span className="text-[12px] text-text-tertiary animate-pulse">
            Starting Streamlit...
          </span>
        ) : null}

        {state === "running" && (
          <>
            <button
              onClick={handleStop}
              className="px-3 py-1.5 text-[12px] font-medium bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition-colors"
            >
              Stop
            </button>
            {url && (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[12px] text-accent hover:underline"
              >
                Open in new tab
              </a>
            )}
          </>
        )}

        {error && <span className="text-[12px] text-red-400">{error}</span>}
      </div>

      {/* Iframe or placeholder */}
      {state === "running" && url ? (
        <iframe
          src={url}
          className="flex-1 w-full border-0"
          allow="clipboard-read; clipboard-write"
          title="Streamlit App"
        />
      ) : (
        <div className="flex-1 flex items-center justify-center text-text-tertiary text-[13px]">
          {state === "starting" || state === "polling"
            ? "Waiting for Streamlit to start..."
            : "Click \"Launch App\" to preview the generated agent"}
        </div>
      )}
    </div>
  )
}
