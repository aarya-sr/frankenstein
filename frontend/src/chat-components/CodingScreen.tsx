import { useState, useEffect, useRef } from "react"

const CODE_SNIPPETS = [
  'from crewai import Agent, Task, Crew',
  'def analyze_data(data: dict) -> dict:',
  '    results = process_pipeline(data)',
  '    return {"output": results}',
  '',
  'agent = Agent(',
  '    role="Data Analyst",',
  '    goal="Extract insights from raw data",',
  '    tools=[analyze_data, validate_output],',
  ')',
  '',
  'task = Task(',
  '    description="Analyze {input_data}",',
  '    expected_output="Structured JSON report",',
  '    agent=agent,',
  ')',
  '',
  'crew = Crew(agents=[agent], tasks=[task])',
  'result = crew.kickoff(inputs=load_inputs())',
  '',
  '# Running static validation checks...',
  'import ast',
  'for f in files:',
  '    ast.parse(open(f).read())',
  '',
  '# Building orchestration layer...',
  'graph = StateGraph(AgentState)',
  'graph.add_node("analyst", analyst_fn)',
  'graph.add_node("reviewer", reviewer_fn)',
  'graph.add_edge("analyst", "reviewer")',
  'graph.set_entry_point("analyst")',
  '',
  'def validate_output(data: dict) -> dict:',
  '    schema = data.get("schema", {})',
  '    return {"valid": check(schema)}',
]

const STAGE_MESSAGES: Record<string, { title: string; verb: string }> = {
  builder: { title: "Building Agents", verb: "Generating code" },
  tester: { title: "Testing Agents", verb: "Running sandbox" },
  architect: { title: "Designing Architecture", verb: "Planning spec" },
  critic: { title: "Reviewing Blueprint", verb: "Analyzing" },
}

interface Props {
  currentStage: string
  activity?: string
}

export function CodingScreen({ currentStage, activity }: Props) {
  const [lines, setLines] = useState<string[]>([])
  const [lineOffset, setLineOffset] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)
  const snippetIndex = useRef(0)

  const stageInfo = STAGE_MESSAGES[currentStage] || { title: "Working", verb: "Processing" }

  useEffect(() => {
    setLines([])
    setLineOffset(0)
    snippetIndex.current = Math.floor(Math.random() * 10)

    const interval = setInterval(() => {
      setLines((prev) => {
        const idx = snippetIndex.current % CODE_SNIPPETS.length
        snippetIndex.current++
        const newLines = [...prev, CODE_SNIPPETS[idx]]
        if (newLines.length > 16) {
          setLineOffset((o) => o + 1)
          newLines.shift()
        }
        return newLines
      })
    }, 300)

    return () => clearInterval(interval)
  }, [currentStage])

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [lines])

  return (
    <div className="animate-[fadeUp_200ms_ease-out] max-w-[520px] w-full">
      <div className="rounded-xl overflow-hidden border border-border bg-[#0d1117] shadow-lg">
        {/* Title bar */}
        <div className="flex items-center gap-2 px-3 py-2 bg-[#161b22] border-b border-[#30363d]">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-[#f85149]" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#d29922]" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#3fb950]" />
          </div>
          <span className="text-[10px] text-[#8b949e] font-mono ml-2">{stageInfo.title}</span>
          <div className="ml-auto flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
            <span className="text-[9px] text-amber-500/80 font-mono">{stageInfo.verb}...</span>
          </div>
        </div>

        {/* Code area */}
        <div ref={containerRef} className="px-3 py-2 font-mono text-[11px] leading-[1.7] h-[200px] overflow-hidden">
          {lines.map((line, i) => {
            const lineNum = lineOffset + i + 1
            return (
              <div key={`${lineOffset}-${i}`} className="flex animate-[fadeIn_150ms_ease-out]">
                <span className="w-6 text-right text-[#484f58] select-none mr-3 shrink-0">
                  {lineNum}
                </span>
                <span>
                  <HighlightedCode text={line} />
                  {i === lines.length - 1 && (
                    <span className="inline-block w-[6px] h-[14px] bg-amber-500/80 ml-0.5 align-text-bottom"
                      style={{ animation: "blink 1s step-end infinite" }} />
                  )}
                </span>
              </div>
            )
          })}
        </div>

        {/* Activity bar */}
        {activity && (
          <div className="px-3 py-1.5 border-t border-[#30363d] bg-[#161b22]">
            <div className="flex items-center gap-2">
              <svg className="w-3 h-3 text-amber-500 animate-spin shrink-0" viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" strokeDasharray="28" strokeDashoffset="8" />
              </svg>
              <span className="text-[10px] text-[#8b949e] font-mono truncate">{activity}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function HighlightedCode({ text }: { text: string }) {
  if (!text) return <span className="text-[#8b949e]">&nbsp;</span>

  const parts: { text: string; color: string }[] = []
  let remaining = text

  while (remaining.length > 0) {
    // Comment
    const commentMatch = remaining.match(/^(#.*)/)
    if (commentMatch) {
      parts.push({ text: commentMatch[1], color: "text-[#8b949e]" })
      remaining = remaining.slice(commentMatch[1].length)
      continue
    }

    // String
    const strMatch = remaining.match(/^(["'])(?:(?=(\\?))\2.)*?\1/)
    if (strMatch) {
      parts.push({ text: strMatch[0], color: "text-[#a5d6ff]" })
      remaining = remaining.slice(strMatch[0].length)
      continue
    }

    // Keyword
    const kwMatch = remaining.match(/^(from|import|def|return|class|for|in|if|else|as|True|False|None)\b/)
    if (kwMatch) {
      parts.push({ text: kwMatch[0], color: "text-[#ff7b72]" })
      remaining = remaining.slice(kwMatch[0].length)
      continue
    }

    // Function call
    const fnMatch = remaining.match(/^(\w+)(?=\()/)
    if (fnMatch) {
      parts.push({ text: fnMatch[0], color: "text-[#d2a8ff]" })
      remaining = remaining.slice(fnMatch[0].length)
      continue
    }

    // Default: take one char
    parts.push({ text: remaining[0], color: "text-[#c9d1d9]" })
    remaining = remaining.slice(1)
  }

  return (
    <>
      {parts.map((p, i) => (
        <span key={i} className={p.color}>{p.text}</span>
      ))}
    </>
  )
}
