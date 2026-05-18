import type { AgentTraceEvent, PreviewState } from "../types/preview"

const MAX_TRACE_LINES = 5000

export const initialPreviewState: PreviewState = {
  files: {},
  selectedFile: null,
  traceEvents: [],
  isRunning: false,
  runError: null,
  exitCode: null,
  durationMs: null,
  finalOutput: null,
  isConnected: false,
}

export type PreviewAction =
  | { type: "SET_FILES"; payload: Record<string, string> }
  | { type: "SELECT_FILE"; payload: string }
  | { type: "RUN_STARTED" }
  | { type: "APPEND_TRACE"; payload: AgentTraceEvent }
  | { type: "RUN_COMPLETE"; payload: { exit_code: number; duration_ms: number; output: string } }
  | { type: "RUN_ERROR"; payload: string }
  | { type: "RESET_RUN" }
  | { type: "SET_CONNECTED"; payload: boolean }

export function previewReducer(state: PreviewState, action: PreviewAction): PreviewState {
  switch (action.type) {
    case "SET_FILES": {
      const files = action.payload
      const fileNames = Object.keys(files)
      const selected = fileNames.includes("main.py")
        ? "main.py"
        : fileNames[0] ?? null
      return { ...state, files, selectedFile: selected }
    }

    case "SELECT_FILE":
      return { ...state, selectedFile: action.payload }

    case "RUN_STARTED":
      return {
        ...state,
        isRunning: true,
        traceEvents: [],
        runError: null,
        exitCode: null,
        durationMs: null,
        finalOutput: null,
      }

    case "APPEND_TRACE": {
      if (state.traceEvents.length >= MAX_TRACE_LINES) return state
      return { ...state, traceEvents: [...state.traceEvents, action.payload] }
    }

    case "RUN_COMPLETE":
      return {
        ...state,
        isRunning: false,
        exitCode: action.payload.exit_code,
        durationMs: action.payload.duration_ms,
        finalOutput: action.payload.output,
      }

    case "RUN_ERROR":
      return { ...state, isRunning: false, runError: action.payload }

    case "RESET_RUN":
      return {
        ...state,
        traceEvents: [],
        isRunning: false,
        runError: null,
        exitCode: null,
        durationMs: null,
        finalOutput: null,
      }

    case "SET_CONNECTED":
      return { ...state, isConnected: action.payload }

    default:
      return state
  }
}
