import { useState } from "react"
import { usePipelineState } from "../context/PipelineContext"
import { PipelineGraph } from "./PipelineGraph"

export function PipelineSidebar() {
  const { stages, hasStarted, isConnected } = usePipelineState()
  const [mobileOpen, setMobileOpen] = useState(false)

  if (!hasStarted) return null

  const sidebarContent = (
    <>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-[11px] font-medium uppercase tracking-[0.05em] text-text-tertiary">
          Pipeline
        </h2>
        <div className="flex items-center gap-1.5">
          <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`} />
          <span className="text-[10px] text-text-tertiary">
            {isConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </div>
      <PipelineGraph stages={stages} />
    </>
  )

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="border-l border-border p-5 animate-[slideInRight_300ms_ease-out] hidden min-[1024px]:block h-full overflow-y-auto">
        {sidebarContent}
      </aside>

      {/* Mobile floating button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="min-[1024px]:hidden fixed bottom-20 right-4 z-30 w-10 h-10 rounded-full bg-surface-elevated border border-border shadow-lg flex items-center justify-center"
        title="Show pipeline"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="8" cy="3" r="2" />
          <circle cx="8" cy="13" r="2" />
          <line x1="8" y1="5" x2="8" y2="11" />
        </svg>
      </button>

      {/* Mobile bottom sheet */}
      {mobileOpen && (
        <div className="min-[1024px]:hidden fixed inset-0 z-40">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute bottom-0 left-0 right-0 bg-bg border-t border-border rounded-t-2xl p-5 max-h-[70vh] overflow-y-auto animate-[slideUp_200ms_ease-out]">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-[13px] font-medium text-text-primary">Pipeline Status</h2>
              <button
                onClick={() => setMobileOpen(false)}
                className="text-text-tertiary hover:text-text-primary transition-colors p-1"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 4L12 12M12 4L4 12" strokeLinecap="round" />
                </svg>
              </button>
            </div>
            <PipelineGraph stages={stages} compact />
          </div>
        </div>
      )}
    </>
  )
}
