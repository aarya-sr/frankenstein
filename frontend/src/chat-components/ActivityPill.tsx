import type { ChatEntry } from "../types/pipeline"

export function ActivityPill({ entry }: { entry: ChatEntry }) {
  const { agent, text } = entry.payload as { agent: string; text: string }

  return (
    <div className="flex items-center gap-2 py-1.5 px-3 animate-[fadeUp_200ms_ease-out]">
      <div className="w-px h-4 bg-amber-500/40" />
      <span className="text-[11px] font-mono text-amber-500/80 uppercase tracking-wider">
        {agent}
      </span>
      <span className="text-[11px] font-mono text-text-tertiary">
        {text}
      </span>
    </div>
  )
}
