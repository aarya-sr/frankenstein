import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { PreviewProvider, usePreviewState, usePreviewDispatch } from "../context/PreviewContext"
import { fetchFiles } from "../api/preview"
import { SplitPane } from "./SplitPane"
import { FileExplorer } from "./FileExplorer"
import { CodeViewer } from "./CodeViewer"
import { ExecutionPanel } from "./ExecutionPanel"
import { StreamlitPreview } from "./StreamlitPreview"

type Tab = "code" | "app"

function PreviewLayout() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const state = usePreviewState()
  const dispatch = usePreviewDispatch()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>("code")

  useEffect(() => {
    if (!sessionId) return
    setLoading(true)
    fetchFiles(sessionId)
      .then((files) => {
        dispatch({ type: "SET_FILES", payload: files })
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [sessionId, dispatch])

  if (!sessionId) {
    return <div className="min-h-screen flex items-center justify-center text-text-tertiary">No session ID</div>
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-text-tertiary">
        Loading files...
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-red-400 text-[14px]">{error}</p>
        <Link to="/chat" className="text-accent text-[13px] hover:underline">Back to chat</Link>
      </div>
    )
  }

  const selectedCode = state.selectedFile ? state.files[state.selectedFile] ?? "" : ""
  const hasAppPy = "app.py" in state.files

  return (
    <div className="h-screen flex flex-col bg-bg text-text-primary">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-bg/80 backdrop-blur-sm shrink-0">
        <div className="flex items-center gap-3">
          <Link to="/chat" className="text-[12px] text-text-tertiary hover:text-text-primary transition-colors">
            &larr; Back to chat
          </Link>
          <span className="text-[12px] text-text-tertiary">
            {sessionId.slice(0, 8)}
          </span>
        </div>

        {/* Tab bar */}
        {hasAppPy && (
          <div className="flex items-center gap-1 bg-surface rounded-md p-0.5">
            <button
              onClick={() => setTab("code")}
              className={`px-3 py-1 text-[12px] rounded transition-colors ${
                tab === "code"
                  ? "bg-accent text-white"
                  : "text-text-tertiary hover:text-text-primary"
              }`}
            >
              Code &amp; Run
            </button>
            <button
              onClick={() => setTab("app")}
              className={`px-3 py-1 text-[12px] rounded transition-colors ${
                tab === "app"
                  ? "bg-accent text-white"
                  : "text-text-tertiary hover:text-text-primary"
              }`}
            >
              Live App
            </button>
          </div>
        )}
      </div>

      {/* Content */}
      {tab === "code" ? (
        <SplitPane
          left={
            <div className="flex flex-col h-full bg-surface">
              <FileExplorer
                files={state.files}
                selectedFile={state.selectedFile}
                onSelect={(f) => dispatch({ type: "SELECT_FILE", payload: f })}
              />
              {state.selectedFile && (
                <CodeViewer code={selectedCode} filename={state.selectedFile} />
              )}
            </div>
          }
          right={<ExecutionPanel sessionId={sessionId} />}
        />
      ) : (
        <StreamlitPreview sessionId={sessionId} />
      )}
    </div>
  )
}

export default function PreviewApp() {
  return (
    <PreviewProvider>
      <PreviewLayout />
    </PreviewProvider>
  )
}
