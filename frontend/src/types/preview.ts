export interface AgentTraceEvent {
  kind: "agent_start" | "agent_end" | "tool_call" | "tool_result" | "output" | "raw"
  agent: string
  tool: string
  result: string
  text: string
  raw: string
}

export interface PreviewState {
  files: Record<string, string>
  selectedFile: string | null
  traceEvents: AgentTraceEvent[]
  isRunning: boolean
  runError: string | null
  exitCode: number | null
  durationMs: number | null
  finalOutput: string | null
  isConnected: boolean
}
