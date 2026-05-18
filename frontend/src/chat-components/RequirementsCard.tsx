import { useState, useCallback } from "react"
import type { RequirementsDoc } from "../types/models"

interface Props {
  requirements: RequirementsDoc
  onApprove: () => Promise<void>
  onEdit: (corrections: string) => void
}

export function RequirementsCard({ requirements, onApprove, onEdit }: Props) {
  const [editMode, setEditMode] = useState(false)
  const [corrections, setCorrections] = useState("")
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

  const handleSubmitCorrections = useCallback(() => {
    if (!corrections.trim()) return
    onEdit(corrections.trim())
    setCorrections("")
    setEditMode(false)
  }, [corrections, onEdit])

  if (collapsed) {
    return (
      <div className="bg-surface-elevated rounded-xl border border-green-500/50 px-5 py-3 flex items-center gap-3">
        <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center shrink-0">
          <svg width="14" height="14" viewBox="0 0 20 20" fill="none">
            <path d="M4 10L8.5 14.5L16 6" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <span className="text-[13px] text-text-primary font-medium">Requirements approved — designing architecture...</span>
      </div>
    )
  }

  return (
    <div
      className={`
        bg-surface-elevated rounded-xl border transition-all duration-300
        ${flashGreen ? "border-green-500" : "border-border"}
        ${!prefersReducedMotion ? "animate-[fadeUp_250ms_ease-out]" : ""}
      `}
    >
      <div className="px-5 py-4">
        <h3 className="text-[15px] font-semibold text-text-primary mb-4">
          Here's what I understood — does this look right?
        </h3>

        <div className="space-y-3">
          <Row label="Domain" value={requirements.domain} />

          {requirements.inputs.length > 0 && (
            <Section label="Inputs">
              {requirements.inputs.map((inp, i) => (
                <div key={i} className="text-[13px] text-text-secondary">
                  <span className="font-medium text-text-primary">{inp.name}</span>
                  {" — "}{inp.description} ({inp.format})
                </div>
              ))}
            </Section>
          )}

          {requirements.outputs.length > 0 && (
            <Section label="Outputs">
              {requirements.outputs.map((out, i) => (
                <div key={i} className="text-[13px] text-text-secondary">
                  <span className="font-medium text-text-primary">{out.name}</span>
                  {" — "}{out.description} ({out.format})
                </div>
              ))}
            </Section>
          )}

          {requirements.process_steps.length > 0 && (
            <Section label="Process Steps">
              {requirements.process_steps.map((step) => (
                <div key={step.step_number} className="text-[13px] text-text-secondary">
                  <span className="font-medium text-text-primary">{step.step_number}.</span>{" "}
                  {step.description}
                </div>
              ))}
            </Section>
          )}

          {requirements.edge_cases.length > 0 && (
            <Section label="Edge Cases">
              {requirements.edge_cases.map((ec, i) => (
                <div key={i} className="text-[13px] text-text-secondary">
                  {ec.description} → {ec.expected_handling}
                </div>
              ))}
            </Section>
          )}

          {requirements.quality_criteria.length > 0 && (
            <Section label="Quality Criteria">
              {requirements.quality_criteria.map((qc, i) => (
                <div key={i} className="text-[13px] text-text-secondary">
                  {qc.criterion} (validated by: {qc.validation_method})
                </div>
              ))}
            </Section>
          )}

          {requirements.constraints.length > 0 && (
            <Section label="Constraints">
              {requirements.constraints.map((c, i) => (
                <div key={i} className="text-[13px] text-text-secondary">{c}</div>
              ))}
            </Section>
          )}

          {requirements.assumptions.length > 0 && (
            <div className="border-l-2 border-amber-500 pl-3">
              <Section label="Assumptions (flagged gaps)">
                {requirements.assumptions.map((a, i) => (
                  <div key={i} className="text-[13px] text-text-secondary">{a}</div>
                ))}
              </Section>
            </div>
          )}
        </div>

        {/* Edit mode textarea */}
        {editMode && (
          <div className="mt-4 space-y-2">
            <textarea
              value={corrections}
              onChange={(e) => setCorrections(e.target.value)}
              placeholder="Describe what needs to change..."
              rows={3}
              className="w-full resize-none bg-surface border border-border rounded-lg px-4 py-3 text-[14px] text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-amber-500"
              autoFocus
            />
          </div>
        )}

        {/* Buttons */}
        <div className="mt-4 flex gap-3">
          {!editMode ? (
            <>
              <button
                onClick={handleApprove}
                disabled={approving}
                className="bg-amber-500 text-neutral-900 font-semibold px-5 py-2.5 rounded-lg min-h-[44px] transition-transform duration-100 active:scale-[0.97] disabled:opacity-60"
              >
                {approving ? "Approving..." : "Approve"}
              </button>
              <button
                onClick={() => setEditMode(true)}
                disabled={approving}
                className="border border-[#2e2e2e] text-text-primary font-medium px-5 py-2.5 rounded-lg min-h-[44px] transition-transform duration-100 active:scale-[0.97] disabled:opacity-60"
              >
                Edit
              </button>
            </>
          ) : (
            <button
              onClick={handleSubmitCorrections}
              disabled={!corrections.trim()}
              className="bg-amber-500 text-neutral-900 font-semibold px-5 py-2.5 rounded-lg min-h-[44px] transition-transform duration-100 active:scale-[0.97] disabled:opacity-60"
            >
              Submit corrections
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3">
      <span className="text-[13px] font-semibold text-text-primary min-w-[120px]">{label}</span>
      <span className="text-[13px] text-text-secondary">{value}</span>
    </div>
  )
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-[13px] font-semibold text-text-primary mb-1">{label}</div>
      <div className="space-y-1 ml-1">{children}</div>
    </div>
  )
}
