interface Props {
  stage: string
  message: string
  recoverable: boolean
  onReset: () => void
  onRetry?: () => void
}

export function ErrorCard({ stage, message, recoverable, onReset, onRetry }: Props) {
  return (
    <div className="bg-surface-elevated rounded-xl border border-red-500/50 animate-[fadeUp_250ms_ease-out]">
      <div className="px-5 py-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-red-500 flex items-center justify-center shrink-0">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M6 6L14 14M14 6L6 14" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
            </svg>
          </div>
          <div>
            <h3 className="text-[16px] font-semibold text-text-primary">
              Pipeline Error
            </h3>
            <span className="text-[11px] text-text-tertiary uppercase tracking-wider">
              Stage: {stage}
            </span>
          </div>
        </div>

        <p className="text-[13px] text-red-400 font-mono bg-surface rounded-lg px-3 py-2 mb-4 break-words">
          {message}
        </p>

        <div className="flex items-center gap-3">
          <button
            onClick={onReset}
            className="bg-surface border border-border text-text-primary font-semibold px-4 py-2 rounded-lg text-[13px] hover:bg-surface-elevated transition-colors min-h-[40px]"
          >
            Start Over
          </button>
          {recoverable && onRetry && (
            <button
              onClick={onRetry}
              className="bg-amber-500 text-neutral-900 font-semibold px-4 py-2 rounded-lg text-[13px] hover:bg-amber-600 transition-colors min-h-[40px]"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
