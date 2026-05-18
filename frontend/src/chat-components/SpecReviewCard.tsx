import { useState, useCallback } from "react"
import type { AgentSpec, CritiqueReport, AgentDef, ToolRef } from "../types/models"
import { FlowDiagram } from "./FlowDiagram"
import { CritiqueFindingList } from "./CritiqueFindingList"

interface Props {
  spec: AgentSpec
  critique: CritiqueReport | null
  reasoning: string
  onApprove: () => Promise<void>
  onFeedback: (feedback: string) => void
}

export function SpecReviewCard({ spec, critique, reasoning, onApprove, onFeedback }: Props) {
  const [editMode, setEditMode] = useState(false)
  const [feedback, setFeedback] = useState("")
  const [approving, setApproving] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const [flashGreen, setFlashGreen] = useState(false)

  const prefersReducedMotion =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches

  const [approved, setApproved] = useState(false)

  const handleApprove = useCallback(async () => {
    if (approving || approved) return
    setApproving(true)
    try {
      await onApprove()
      setApproved(true)
      if (prefersReducedMotion) {
        setCollapsed(true)
      } else {
        setFlashGreen(true)
        setTimeout(() => setCollapsed(true), 300)
      }
    } catch {
      setApproving(false)
    }
  }, [onApprove, prefersReducedMotion, approving, approved])

  const handleSubmitFeedback = useCallback(() => {
    if (!feedback.trim()) return
    onFeedback(feedback.trim())
    setFeedback("")
    setEditMode(false)
  }, [feedback, onFeedback])

  // Build tool name lookup: tool id -> human-readable name
  const toolNameMap = new Map<string, ToolRef>()
  for (const t of spec.tools) {
    toolNameMap.set(t.id, t)
  }

  if (collapsed) {
    return (
      <div className="bg-surface-elevated rounded-xl border border-green-500/50 px-5 py-3 flex items-center gap-3">
        <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center shrink-0">
          <svg width="14" height="14" viewBox="0 0 20 20" fill="none">
            <path d="M4 10L8.5 14.5L16 6" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <span className="text-[13px] text-text-primary font-medium">Blueprint approved — building your agents...</span>
      </div>
    )
  }

  return (
    <div
      className={`
        max-w-[840px] bg-surface-elevated rounded-xl border transition-all duration-300
        ${flashGreen ? "border-green-500" : "border-border"}
        ${!prefersReducedMotion ? "animate-[fadeUp_250ms_ease-out]" : ""}
      `}
    >
      <div className="px-6 py-5">
        <h3 className="text-[15px] font-semibold text-text-primary mb-4">
          Your Agent Blueprint
        </h3>

        {/* Decision rationale */}
        {reasoning && (
          <div className="border-l-2 border-amber-500 pl-3 mb-5">
            <p className="text-[13px] text-text-tertiary italic leading-[1.6]">
              {reasoning}
            </p>
          </div>
        )}

        {/* Agent cards grid */}
        {spec.agents.length > 0 ? (
          <div
            className="grid gap-4 mb-5"
            style={{ gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))" }}
          >
            {spec.agents.map((agent, i) => (
              <AgentCard
                key={agent.id}
                agent={agent}
                toolNameMap={toolNameMap}
                index={i}
                animate={!prefersReducedMotion}
              />
            ))}
          </div>
        ) : (
          <p className="text-[13px] text-text-tertiary mb-5">No agents defined</p>
        )}

        {/* Flow diagram */}
        <FlowDiagram executionFlow={spec.execution_flow} agents={spec.agents} />

        {/* Critique findings */}
        {critique && critique.findings.length > 0 && (
          <div className="mt-5">
            <CritiqueFindingList findings={critique.findings} />
          </div>
        )}

        {/* Feedback textarea */}
        {editMode && (
          <div className="mt-4 space-y-2">
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Describe what you'd like changed in the blueprint..."
              rows={3}
              className="w-full resize-none bg-surface border border-border rounded-lg px-4 py-3 text-[14px] text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-amber-500"
              autoFocus
            />
          </div>
        )}

        {/* Action buttons */}
        <div className="mt-5 flex gap-3">
          {!editMode ? (
            <>
              <button
                onClick={handleApprove}
                disabled={approving}
                className="bg-amber-500 text-neutral-900 font-semibold px-5 py-2.5 rounded-lg min-h-[44px] transition-transform duration-100 active:scale-[0.97] disabled:opacity-60 hover:bg-amber-600"
              >
                {approving ? "Approving..." : "Approve Blueprint"}
              </button>
              <button
                onClick={() => setEditMode(true)}
                disabled={approving}
                className="border border-[#2e2e2e] text-text-primary font-medium px-5 py-2.5 rounded-lg min-h-[44px] transition-transform duration-100 active:scale-[0.97] disabled:opacity-60 hover:border-[#404040]"
              >
                Request Changes
              </button>
            </>
          ) : (
            <button
              onClick={handleSubmitFeedback}
              disabled={!feedback.trim()}
              className="bg-amber-500 text-neutral-900 font-semibold px-5 py-2.5 rounded-lg min-h-[44px] transition-transform duration-100 active:scale-[0.97] disabled:opacity-60 hover:bg-amber-600"
            >
              Submit feedback
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function AgentCard({
  agent,
  toolNameMap,
  index,
  animate,
}: {
  agent: AgentDef
  toolNameMap: Map<string, ToolRef>
  index: number
  animate: boolean
}) {
  return (
    <div
      className={`
        bg-surface-elevated border border-border rounded-[10px] px-5 py-4
        hover:border-[#404040] transition-colors
        ${animate ? "animate-[fadeUp_250ms_ease-out_both]" : ""}
      `}
      style={animate ? { animationDelay: `${index * 50}ms` } : undefined}
    >
      <div className="text-[14px] font-semibold text-text-primary mb-1">
        {agent.role}
      </div>
      <div className="text-[13px] text-text-secondary leading-[1.5] mb-3">
        {agent.goal}
      </div>
      {agent.tools.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {agent.tools.map((toolId) => {
            const tool = toolNameMap.get(toolId)
            const displayName = tool ? toolId.replace(/_/g, " ") : toolId
            const tooltip = tool
              ? `${tool.library_ref}\nAccepts: ${tool.accepts.join(", ")}\nOutputs: ${tool.outputs.join(", ")}`
              : toolId
            return (
              <span
                key={toolId}
                title={tooltip}
                className="font-mono text-[11px] text-text-secondary bg-surface border border-border rounded px-1.5 py-0.5 cursor-default"
              >
                {displayName}
              </span>
            )
          })}
        </div>
      )}
    </div>
  )
}
