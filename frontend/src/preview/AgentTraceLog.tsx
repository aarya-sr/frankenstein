import { useEffect, useRef } from "react"
import type { AgentTraceEvent } from "../types/preview"
import { AgentTraceRow } from "./AgentTraceRow"

interface Props {
  events: AgentTraceEvent[]
}

export function AgentTraceLog({ events }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [events.length])

  if (events.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-text-tertiary text-[13px]">
        Click Run to execute the agent
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto font-mono">
      {events.map((event, i) => (
        <AgentTraceRow key={i} event={event} />
      ))}
      {events.length >= 5000 && (
        <div className="px-3 py-2 text-[11px] text-amber-400">
          Output truncated at 5000 lines
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
