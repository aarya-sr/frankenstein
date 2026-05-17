import type { PipelineStage } from "../types/pipeline"

interface Props {
  stages: PipelineStage[]
  compact?: boolean // reserved for mobile compact mode
}

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M2.5 6L5 8.5L9.5 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function XIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M3 3L9 9M9 3L3 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

// Define which stages have loop-back arrows
const LOOP_BACKS: Record<string, string> = {
  critic: "architect",
  tester: "builder",
}

const NODE_CONFIG: Record<string, { label: string; short: string }> = {
  elicitor: { label: "Elicitor", short: "EL" },
  requirements_review: { label: "Req Review", short: "RR" },
  architect: { label: "Architect", short: "AR" },
  critic: { label: "Critic", short: "CR" },
  spec_review: { label: "Spec Review", short: "SR" },
  builder: { label: "Builder", short: "BU" },
  tester: { label: "Tester", short: "TE" },
  learner: { label: "Learner", short: "LE" },
}

export function PipelineGraph({ stages, compact }: Props) {
  return (
    <div className="flex flex-col gap-0">
      {stages.map((stage, i) => {
        const config = NODE_CONFIG[stage.id] || { label: stage.name, short: stage.id.slice(0, 2).toUpperCase() }
        const isLast = i === stages.length - 1
        const hasLoop = stage.id in LOOP_BACKS
        const isComplete = stage.status === "complete"
        const isActive = stage.status === "active"
        const isError = stage.status === "error"
        const isCheckpoint = stage.id === "requirements_review" || stage.id === "spec_review"

        // Node styling
        const nodeClasses = [
          `w-full flex items-center gap-2.5 rounded-lg transition-all duration-300 relative ${compact ? "px-2 py-1.5" : "px-3 py-2"}`,
          isActive && "bg-amber-500/10 ring-1 ring-amber-500/40",
          isComplete && "bg-green-500/5",
          isError && "bg-red-500/5",
          !isActive && !isComplete && !isError && "opacity-50",
        ].filter(Boolean).join(" ")

        // Dot styling
        const dotClasses = [
          "w-5 h-5 rounded-full shrink-0 flex items-center justify-center text-white transition-all duration-300",
          isActive && "bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)] animate-[pulse_2s_ease-in-out_infinite]",
          isComplete && "bg-green-500",
          isError && "bg-red-500",
          !isActive && !isComplete && !isError && "bg-[#404040] border border-[#555] border-dashed",
        ].filter(Boolean).join(" ")

        return (
          <div key={stage.id}>
            <div className={nodeClasses}>
              <div className={dotClasses}>
                {isComplete && <CheckIcon />}
                {isError && <XIcon />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className={`text-[12px] font-medium truncate ${
                    isActive ? "text-amber-500" : isComplete ? "text-green-400" : isError ? "text-red-400" : "text-text-tertiary"
                  }`}>
                    {config.label}
                  </span>
                  {isCheckpoint && (
                    <span className="text-[9px] px-1 py-0.5 rounded bg-surface border border-border text-text-tertiary">
                      HUMAN
                    </span>
                  )}
                </div>
                {isActive && (
                  <p className="text-[10px] text-text-tertiary mt-0.5 truncate">{stage.description}</p>
                )}
              </div>
              {hasLoop && (isActive || isComplete) && (
                <div className="absolute -right-1 top-1/2 -translate-y-1/2">
                  <svg width="16" height="24" viewBox="0 0 16 24" className={`${isActive ? "text-amber-500/60 animate-[pulse_1.5s_ease-in-out_infinite]" : "text-green-500/30"}`}>
                    <path d="M2 4C10 4 12 8 12 12C12 16 10 20 2 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                    <path d="M4 17L2 20L5 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
              )}
            </div>
            {/* Connector line */}
            {!isLast && (
              <div className="flex justify-start pl-[21px]">
                <div className={`w-px h-2 transition-colors duration-300 ${isComplete ? "bg-green-500/50" : "bg-border"}`} />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
