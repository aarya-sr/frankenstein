import { useCallback, useState } from "react"
import { usePreviewState } from "../context/PreviewContext"
import { triggerRun } from "../api/preview"
import { usePreviewWebSocket } from "../hooks/usePreviewWebSocket"
import { AgentTraceLog } from "./AgentTraceLog"

interface Props {
  sessionId: string
}

export function ExecutionPanel({ sessionId }: Props) {
  const state = usePreviewState()
  const { requestStream } = usePreviewWebSocket(sessionId)
  const [runError, setRunError] = useState<string | null>(null)

  const handleRun = useCallback(async () => {
    setRunError(null)
    try {
      await triggerRun(sessionId)
      // Give backend a moment to set up queue, then request stream
      setTimeout(() => requestStream(), 300)
    } catch (err) {
      setRunError(err instanceof Error ? err.message : "Failed to start run")
    }
  }, [sessionId, requestStream])

  return (
    <div className="flex flex-col h-full">
      {/* Header with Run button */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border shrink-0">
        <span className="text-[13px] font-semibold text-text-primary">Execution Output</span>
        <button
          onClick={handleRun}
          disabled={state.isRunning}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-green-600 hover:bg-green-500 disabled:bg-green-600/40 text-white text-[12px] font-semibold transition-colors"
        >
          {state.isRunning ? (
            <>
              <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
              Running...
            </>
          ) : (
            <>
              <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
                <path d="M3 1.5v9l7.5-4.5L3 1.5z" />
              </svg>
              Run
            </>
          )}
        </button>
      </div>

      {/* Error banner */}
      {(runError || state.runError) && (
        <div className="px-4 py-2 bg-red-500/10 border-b border-red-500/30 text-[12px] text-red-400">
          {runError || state.runError}
        </div>
      )}

      {/* Trace log */}
      <AgentTraceLog events={state.traceEvents} />

      {/* Completion footer */}
      {state.exitCode !== null && (
        <div className={`px-4 py-2 border-t text-[12px] font-mono ${
          state.exitCode === 0
            ? "border-green-500/30 text-green-400 bg-green-500/5"
            : "border-red-500/30 text-red-400 bg-red-500/5"
        }`}>
          {state.exitCode === 0 ? "Completed" : `Exited with code ${state.exitCode}`}
          {state.durationMs !== null && ` in ${(state.durationMs / 1000).toFixed(1)}s`}
        </div>
      )}
    </div>
  )
}
