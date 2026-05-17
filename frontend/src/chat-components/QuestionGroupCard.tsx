import { useState, useCallback, type Dispatch } from "react"
import type { ChatEntry } from "../types/pipeline"
import type { Action } from "../context/pipelineReducer"
import { SystemAvatar } from "./ChatMessage"

interface Category {
  name: string
  confidence: number
  questions: string[]
}

interface Props {
  entry: ChatEntry
  sendMessage: (data: Record<string, unknown>) => void
  sessionId: string | null
  dispatch: Dispatch<Action>
}

interface FlatQuestion {
  category: string
  question: string
}

export function QuestionGroupCard({ entry, sendMessage, sessionId, dispatch }: Props) {
  const payload = entry.payload as { categories: Category[]; round: number; max_rounds: number }
  const { categories, round, max_rounds } = payload

  // Flatten all questions into a single ordered list
  const flatQuestions: FlatQuestion[] = []
  for (const cat of categories) {
    for (const q of cat.questions) {
      flatQuestions.push({ category: cat.name, question: q })
    }
  }

  const [currentIdx, setCurrentIdx] = useState(0)
  const [answers, setAnswers] = useState<string[]>(() => flatQuestions.map(() => ""))
  const [submitted, setSubmitted] = useState(false)

  const total = flatQuestions.length
  const current = flatQuestions[currentIdx]

  const handleAnswerChange = useCallback(
    (value: string) => {
      setAnswers((prev) => {
        const next = [...prev]
        next[currentIdx] = value
        return next
      })
    },
    [currentIdx]
  )

  const handleSubmit = useCallback(() => {
    if (!sessionId || submitted) return
    setSubmitted(true)

    // Build concatenated answer with category labels
    const parts: string[] = []
    let lastCat = ""
    for (let i = 0; i < flatQuestions.length; i++) {
      const fq = flatQuestions[i]
      const ans = answers[i]?.trim()
      if (!ans) continue
      if (fq.category !== lastCat) {
        parts.push(`[${fq.category}]`)
        lastCat = fq.category
      }
      parts.push(`Q: ${fq.question}\nA: ${ans}`)
    }

    const text = parts.join("\n\n")
    dispatch({ type: "SET_WORKING", payload: true })
    sendMessage({
      type: "control.user_input",
      payload: { text },
      session_id: sessionId,
    })
  }, [sessionId, submitted, flatQuestions, answers, dispatch, sendMessage])

  if (submitted) {
    return (
      <div className="flex items-start gap-3">
        <SystemAvatar />
        <div className="flex-1 bg-surface-elevated rounded-xl border border-border animate-[fadeUp_250ms_ease-out] px-5 py-4">
          <div className="flex items-center gap-2">
            <span className="text-green-400 text-sm">&#10003;</span>
            <span className="text-[13px] text-text-secondary">
              Round {round} answers submitted
            </span>
          </div>
        </div>
      </div>
    )
  }

  if (!current) return null

  const isFirst = currentIdx === 0
  const isLast = currentIdx === total - 1
  const allAnswered = answers.every((a) => a.trim().length > 0)

  return (
    <div className="flex items-start gap-3">
      <SystemAvatar />
      <div className="flex-1 bg-surface-elevated rounded-xl border border-border animate-[fadeUp_250ms_ease-out]">
        <div className="px-5 py-4">
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[15px] font-semibold text-text-primary">
              A few questions to get this right
            </h3>
            <span className="text-[11px] text-text-tertiary">
              Question {currentIdx + 1} of {total} &middot; Round {round}/{max_rounds}
            </span>
          </div>

          {/* Gap coverage indicators */}
          <div className="flex flex-wrap gap-1.5 mb-3">
            {categories.map((cat) => {
              const pct = Math.round(cat.confidence * 100)
              const color = cat.confidence >= 0.8 ? "bg-green-500" : cat.confidence >= 0.5 ? "bg-amber-500" : "bg-red-500"
              const bgColor = cat.confidence >= 0.8 ? "bg-green-500/10" : cat.confidence >= 0.5 ? "bg-amber-500/10" : "bg-red-500/10"
              return (
                <div key={cat.name} className={`flex items-center gap-1.5 px-2 py-1 rounded ${bgColor}`}>
                  <span className="text-[10px] text-text-tertiary truncate max-w-[80px]">{cat.name}</span>
                  <div className="w-8 h-1.5 bg-surface rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${color} transition-all duration-300`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              )
            })}
          </div>

          {/* Progress bar */}
          <div className="w-full h-1 bg-surface rounded-full mb-4 overflow-hidden">
            <div
              className="h-full bg-amber-500 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${((currentIdx + 1) / total) * 100}%` }}
            />
          </div>

          {/* Sliding question area */}
          <div>
            <div
              className="transition-transform duration-300 ease-out"
              key={currentIdx}
            >
              {/* Category badge */}
              <span className="inline-block text-[11px] font-medium uppercase tracking-[0.05em] text-amber-500 mb-2">
                {current.category}
              </span>

              {/* Question */}
              <div className="border-l-2 border-amber-500/40 pl-3 text-[14px] text-text-secondary leading-[1.6] mb-4">
                {current.question}
              </div>

              {/* Answer textarea */}
              <textarea
                value={answers[currentIdx]}
                onChange={(e) => handleAnswerChange(e.target.value)}
                placeholder="Your answer..."
                rows={3}
                className="w-full resize-none bg-surface border border-border rounded-lg px-4 py-3 text-[14px] text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-amber-500"
                autoFocus
              />
            </div>
          </div>

          {/* Navigation */}
          <div className="mt-4 flex items-center justify-between">
            <button
              onClick={() => setCurrentIdx((i) => i - 1)}
              disabled={isFirst}
              className="text-[13px] text-text-secondary hover:text-text-primary disabled:opacity-30 disabled:cursor-not-allowed transition-colors px-3 py-2"
            >
              ← Back
            </button>

            {isLast ? (
              <button
                onClick={handleSubmit}
                disabled={!allAnswered}
                className="bg-amber-500 text-neutral-900 font-semibold px-5 py-2.5 rounded-lg min-h-[44px] transition-all duration-100 active:scale-[0.97] hover:bg-amber-600 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                Submit Answers
              </button>
            ) : (
              <button
                onClick={() => setCurrentIdx((i) => i + 1)}
                className="text-[13px] text-text-primary hover:text-amber-500 transition-colors px-3 py-2"
              >
                Next →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
