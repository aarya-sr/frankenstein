import { useState, useCallback } from "react"
import { Link } from "react-router-dom"
import { downloadAgent, fetchAgentFiles } from "../api/sessions"
import { CodePreview } from "./CodePreview"

interface Props {
  sessionId: string
  framework: string
  summary: string
  allPassed?: boolean
  agentsCount?: number
  testPassed?: number
  testTotal?: number
  fileCount?: number
  buildTimeSeconds?: number
}

export function CompletionCard({
  sessionId,
  framework,
  summary,
  allPassed = true,
  agentsCount,
  testPassed,
  testTotal,
  fileCount,
  buildTimeSeconds,
}: Props) {
  const [downloading, setDownloading] = useState(false)
  const [showCode, setShowCode] = useState(false)
  const [files, setFiles] = useState<Record<string, string> | null>(null)
  const [loadingFiles, setLoadingFiles] = useState(false)

  const handleDownload = useCallback(async () => {
    setDownloading(true)
    try {
      await downloadAgent(sessionId)
    } catch (err) {
      console.error("Download failed:", err)
    } finally {
      setDownloading(false)
    }
  }, [sessionId])

  const handleToggleCode = useCallback(async () => {
    if (showCode) {
      setShowCode(false)
      return
    }
    if (!files) {
      setLoadingFiles(true)
      try {
        const result = await fetchAgentFiles(sessionId)
        setFiles(result)
      } catch (err) {
        console.error("Failed to fetch files:", err)
      } finally {
        setLoadingFiles(false)
      }
    }
    setShowCode(true)
  }, [showCode, files, sessionId])

  const borderClass = allPassed ? "border-green-500/50" : "border-amber-500/50"
  const dotClass = allPassed ? "bg-green-500" : "bg-amber-500"
  const title = allPassed ? "Your agents are ready." : "Your agents are mostly ready."

  return (
    <div className={`bg-surface-elevated rounded-xl border ${borderClass} animate-[fadeUp_250ms_ease-out]`}>
      <div className="px-5 py-4">
        {/* Header with icon */}
        <div className="flex items-center gap-3 mb-3 animate-[fadeUp_200ms_ease-out_both]" style={{ animationDelay: "50ms" }}>
          <div className={`w-10 h-10 rounded-full ${dotClass} flex items-center justify-center shrink-0`}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M4 10L8.5 14.5L16 6" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <h3 className="text-[18px] font-semibold text-text-primary">
            {title}
          </h3>
        </div>

        <p className="text-[13px] text-text-secondary mb-4 animate-[fadeUp_200ms_ease-out_both]" style={{ animationDelay: "100ms" }}>
          {summary}
        </p>

        {/* Summary table */}
        <div
          className="grid grid-cols-2 gap-x-6 gap-y-2 mb-4 animate-[fadeUp_200ms_ease-out_both]"
          style={{ animationDelay: "150ms" }}
        >
          {agentsCount !== undefined && (
            <SummaryRow label="Agents" value={String(agentsCount)} />
          )}
          <SummaryRow label="Framework" value={framework} />
          {testTotal !== undefined && testPassed !== undefined && (
            <SummaryRow
              label="Tests"
              value={`${testPassed}/${testTotal} passed`}
              warn={!allPassed}
            />
          )}
          {fileCount !== undefined && (
            <SummaryRow label="Files" value={String(fileCount)} />
          )}
          {buildTimeSeconds !== undefined && (
            <SummaryRow label="Build time" value={`${buildTimeSeconds}s`} />
          )}
        </div>

        {!allPassed && (
          <p className="text-[12px] text-amber-400 mb-3 animate-[fadeUp_200ms_ease-out_both]" style={{ animationDelay: "200ms" }}>
            Some tests had issues — the download is still available but may need manual fixes.
          </p>
        )}

        <div className="flex items-center gap-3 flex-wrap animate-[fadeUp_200ms_ease-out_both]" style={{ animationDelay: "250ms" }}>
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="bg-amber-500 text-neutral-900 font-semibold px-5 py-2.5 rounded-lg min-h-[44px] transition-transform duration-100 active:scale-[0.97] disabled:opacity-60"
          >
            {downloading ? "Downloading..." : "Download Agent Project"}
          </button>
          <button
            onClick={handleToggleCode}
            disabled={loadingFiles}
            className="bg-surface border border-border text-text-primary font-medium px-4 py-2.5 rounded-lg min-h-[44px] text-[13px] hover:bg-surface-elevated transition-colors disabled:opacity-60"
          >
            {loadingFiles ? "Loading..." : showCode ? "Hide Code" : "View Generated Code"}
          </button>
          <Link
            to={`/preview/${sessionId}`}
            className="bg-surface border border-border text-text-primary font-semibold px-5 py-2.5 rounded-lg min-h-[44px] transition-colors hover:bg-surface-elevated hover:border-accent/50 flex items-center gap-2 text-[14px]"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M2 3h10M2 7h10M2 11h6" strokeLinecap="round" />
            </svg>
            Preview &amp; Run
          </Link>
        </div>

        {showCode && files && (
          <div className="mt-4 animate-[fadeUp_200ms_ease-out]">
            <CodePreview files={files} />
          </div>
        )}
      </div>
    </div>
  )
}

function SummaryRow({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className="flex justify-between">
      <span className="text-[12px] text-text-tertiary">{label}</span>
      <span className={`text-[12px] font-medium ${warn ? "text-amber-400" : "text-text-primary"}`}>
        {value}
      </span>
    </div>
  )
}
