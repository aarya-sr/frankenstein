/**
 * Preview reducer unit tests.
 * Run: npx tsx src/preview/__tests__/previewReducer.test.ts
 *
 * Uses simple assert — no test framework needed.
 */

import { previewReducer, initialPreviewState } from "../../context/previewReducer"
import type { AgentTraceEvent, PreviewState } from "../../types/preview"

declare const process: { exit(code: number): never }

function assert(condition: boolean, msg: string) {
  if (!condition) {
    console.error(`FAIL: ${msg}`)
    process.exit(1)
  }
  console.log(`PASS: ${msg}`)
}

// ── SET_FILES ──────────────────────────────────────────────────────

const files = { "main.py": "print('hi')", "agents.py": "class A: pass", "utils.py": "def f(): ..." }
let state = previewReducer(initialPreviewState, { type: "SET_FILES", payload: files })
assert(Object.keys(state.files).length === 3, "SET_FILES stores all files")
assert(state.selectedFile === "main.py", "SET_FILES auto-selects main.py")

const noMain = { "agents.py": "x", "tools.py": "y" }
state = previewReducer(initialPreviewState, { type: "SET_FILES", payload: noMain })
assert(state.selectedFile === "agents.py", "SET_FILES picks first file when no main.py")

state = previewReducer(initialPreviewState, { type: "SET_FILES", payload: {} })
assert(state.selectedFile === null, "SET_FILES null when empty")

// ── SELECT_FILE ────────────────────────────────────────────────────

state = previewReducer(
  { ...initialPreviewState, files, selectedFile: "main.py" },
  { type: "SELECT_FILE", payload: "agents.py" }
)
assert(state.selectedFile === "agents.py", "SELECT_FILE changes selection")

// ── RUN_STARTED ────────────────────────────────────────────────────

state = previewReducer(
  { ...initialPreviewState, traceEvents: [{ kind: "raw", agent: "", tool: "", result: "", text: "old", raw: "old" }], exitCode: 0 },
  { type: "RUN_STARTED" }
)
assert(state.isRunning === true, "RUN_STARTED sets isRunning")
assert(state.traceEvents.length === 0, "RUN_STARTED clears trace")
assert(state.exitCode === null, "RUN_STARTED clears exitCode")
assert(state.runError === null, "RUN_STARTED clears runError")

// ── APPEND_TRACE ───────────────────────────────────────────────────

const event: AgentTraceEvent = { kind: "agent_start", agent: "R", tool: "", result: "", text: "", raw: "raw" }
state = previewReducer({ ...initialPreviewState, isRunning: true }, { type: "APPEND_TRACE", payload: event })
assert(state.traceEvents.length === 1, "APPEND_TRACE adds event")
assert(state.traceEvents[0].kind === "agent_start", "APPEND_TRACE preserves kind")

// Cap at 5000
let bigState: PreviewState = { ...initialPreviewState, traceEvents: Array(5000).fill(event) }
bigState = previewReducer(bigState, { type: "APPEND_TRACE", payload: event })
assert(bigState.traceEvents.length === 5000, "APPEND_TRACE caps at 5000")

// ── RUN_COMPLETE ───────────────────────────────────────────────────

state = previewReducer(
  { ...initialPreviewState, isRunning: true },
  { type: "RUN_COMPLETE", payload: { exit_code: 0, duration_ms: 5000, output: "done" } }
)
assert(state.isRunning === false, "RUN_COMPLETE clears isRunning")
assert(state.exitCode === 0, "RUN_COMPLETE sets exitCode")
assert(state.durationMs === 5000, "RUN_COMPLETE sets durationMs")
assert(state.finalOutput === "done", "RUN_COMPLETE sets finalOutput")

// ── RUN_ERROR ──────────────────────────────────────────────────────

state = previewReducer(
  { ...initialPreviewState, isRunning: true },
  { type: "RUN_ERROR", payload: "Docker exploded" }
)
assert(state.isRunning === false, "RUN_ERROR clears isRunning")
assert(state.runError === "Docker exploded", "RUN_ERROR sets message")

// ── RESET_RUN ──────────────────────────────────────────────────────

state = previewReducer(
  { ...initialPreviewState, traceEvents: [event], exitCode: 1, durationMs: 999, finalOutput: "x", runError: "y" },
  { type: "RESET_RUN" }
)
assert(state.traceEvents.length === 0, "RESET_RUN clears trace")
assert(state.exitCode === null, "RESET_RUN clears exitCode")
assert(state.runError === null, "RESET_RUN clears error")

// ── SET_CONNECTED ──────────────────────────────────────────────────

state = previewReducer(initialPreviewState, { type: "SET_CONNECTED", payload: true })
assert(state.isConnected === true, "SET_CONNECTED true")
state = previewReducer(state, { type: "SET_CONNECTED", payload: false })
assert(state.isConnected === false, "SET_CONNECTED false")

console.log("\nAll preview reducer tests passed!")
