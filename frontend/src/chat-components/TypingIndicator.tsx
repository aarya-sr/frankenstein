import { SystemAvatar } from "./ChatMessage"

const STAGE_LABELS: Record<string, string> = {
  elicitor: "Analyzing your requirements...",
  requirements_review: "Preparing requirements review...",
  architect: "Designing agent architecture...",
  critic: "Running adversarial review...",
  spec_review: "Preparing blueprint review...",
  builder: "Writing your agent code...",
  tester: "Testing in sandbox...",
  learner: "Storing build patterns...",
}

export function TypingIndicator({ currentStage }: { currentStage?: string }) {
  const label = (currentStage && STAGE_LABELS[currentStage]) || null

  return (
    <div className="flex items-start gap-3 animate-[fadeUp_200ms_ease-out]">
      <SystemAvatar />
      <div className="bg-surface rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-2">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-text-tertiary animate-[bounce_1.2s_ease-in-out_infinite]" />
          <span className="w-1.5 h-1.5 rounded-full bg-text-tertiary animate-[bounce_1.2s_ease-in-out_0.2s_infinite]" />
          <span className="w-1.5 h-1.5 rounded-full bg-text-tertiary animate-[bounce_1.2s_ease-in-out_0.4s_infinite]" />
        </div>
        {label && (
          <span className="text-[11px] text-text-tertiary ml-1">{label}</span>
        )}
      </div>
    </div>
  )
}
