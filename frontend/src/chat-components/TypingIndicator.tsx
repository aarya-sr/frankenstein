import { useState, useEffect, useRef } from "react"
import { SystemAvatar } from "./ChatMessage"

const STAGE_LABELS: Record<string, string> = {
  elicitor: "Analyzing your requirements",
  requirements_review: "Preparing requirements review",
  architect: "Designing agent architecture",
  critic: "Running adversarial review",
  spec_review: "Preparing blueprint review",
  builder: "Writing your agent code",
  tester: "Testing in sandbox",
  learner: "Storing build patterns",
}

const FACTS = [
  "6 specialized AI models work on your agent — each picked for what it does best.",
  "The Critic agent deliberately uses a different model family to catch blind spots the Architect might miss.",
  "Your agent code is generated, validated, and repaired automatically — up to 3 repair cycles if needed.",
  "Every build teaches the system. Past failures become guardrails for future agents.",
  "The spec goes through 9 attack vectors — circular deps, dead ends, resource conflicts, and more.",
  "Generated agents come with tools, orchestration, config, and a README. Ready to run.",
  "The Elicitor scores your requirements across 6 dimensions to find gaps before building starts.",
  "Frankenstein stores patterns in a vector database — it literally gets smarter with every build.",
  "Your agent runs in a Docker sandbox first. No untested code ships.",
  "The pipeline can route failures back to the right stage — spec bugs go to Architect, code bugs to Builder.",
  "Two human checkpoints let you approve or redirect before any code gets written.",
  "The Builder plans before it writes — tool signatures, task templates, kickoff inputs. Then generates.",
  "Each tool in the library has a pre-validated schema and code template. No hallucinated APIs.",
  "The Tester classifies failures by root cause — so the fix goes to the right place, not just a retry.",
  "From prompt to working agent: typically under 2 minutes for a 5-agent pipeline.",
  "Frankenstein supports both CrewAI and LangGraph output — picks the best framework for your use case.",
  "The Critic checks that every agent's output schema matches the next agent's expected input.",
  "Your generated agent includes sample data so you can test it immediately.",
]

// Shuffle to avoid always starting the same
function shuffled<T>(arr: T[]): T[] {
  const copy = [...arr]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy
}

export function TypingIndicator({ currentStage }: { currentStage?: string }) {
  const label = (currentStage && STAGE_LABELS[currentStage]) || "Working"
  const [factIndex, setFactIndex] = useState(0)
  const [visible, setVisible] = useState(true)
  const facts = useRef(shuffled(FACTS))

  useEffect(() => {
    const interval = setInterval(() => {
      setVisible(false)
      setTimeout(() => {
        setFactIndex((i) => (i + 1) % facts.current.length)
        setVisible(true)
      }, 300)
    }, 4500)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex items-start gap-3 animate-[fadeUp_200ms_ease-out]">
      <SystemAvatar />
      <div className="flex flex-col gap-2 max-w-[420px]">
        {/* Stage label with dots */}
        <div className="bg-surface rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-text-tertiary animate-[bounce_1.2s_ease-in-out_infinite]" />
            <span className="w-1.5 h-1.5 rounded-full bg-text-tertiary animate-[bounce_1.2s_ease-in-out_0.2s_infinite]" />
            <span className="w-1.5 h-1.5 rounded-full bg-text-tertiary animate-[bounce_1.2s_ease-in-out_0.4s_infinite]" />
          </div>
          <span className="text-[11px] text-text-tertiary ml-1">{label}</span>
        </div>

        {/* Cycling fact */}
        <div
          className="px-4 py-2.5 rounded-xl bg-surface/60 border border-border/40 transition-all duration-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? "translateY(0)" : "translateY(4px)" }}
        >
          <p className="text-[11.5px] leading-relaxed text-text-secondary italic">
            {facts.current[factIndex]}
          </p>
        </div>
      </div>
    </div>
  )
}
