import type { AgentTraceEvent } from "../types/preview"

const KIND_STYLES: Record<string, { badge: string; badgeText: string; indent: boolean }> = {
  agent_start: { badge: "bg-blue-500/20 text-blue-400", badgeText: "Agent", indent: false },
  agent_end: { badge: "bg-blue-500/10 text-blue-400/60", badgeText: "Done", indent: false },
  tool_call: { badge: "bg-purple-500/20 text-purple-400", badgeText: "Tool", indent: true },
  tool_result: { badge: "bg-green-500/20 text-green-400", badgeText: "Result", indent: true },
  output: { badge: "bg-amber-500/20 text-amber-400", badgeText: "Output", indent: false },
  raw: { badge: "", badgeText: "", indent: false },
}

export function AgentTraceRow({ event }: { event: AgentTraceEvent }) {
  const style = KIND_STYLES[event.kind] ?? KIND_STYLES.raw

  if (event.kind === "raw") {
    return (
      <div className="px-3 py-0.5 text-[12px] text-text-tertiary font-mono whitespace-pre-wrap break-all">
        {event.text || event.raw}
      </div>
    )
  }

  const label =
    event.kind === "agent_start" || event.kind === "agent_end"
      ? event.agent
      : event.kind === "tool_call"
        ? `${event.agent ? event.agent + " > " : ""}${event.tool}`
        : event.kind === "tool_result"
          ? event.result.slice(0, 200)
          : event.text

  return (
    <div className={`flex items-start gap-2 px-3 py-1 ${style.indent ? "pl-8" : ""}`}>
      {style.badgeText && (
        <span className={`shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded ${style.badge}`}>
          {style.badgeText}
        </span>
      )}
      <span className="text-[12px] text-text-secondary font-mono whitespace-pre-wrap break-all">
        {label}
      </span>
    </div>
  )
}
