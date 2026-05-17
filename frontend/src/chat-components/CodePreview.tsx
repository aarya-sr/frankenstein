import { useState, useCallback } from "react"

interface Props {
  files: Record<string, string>
}

function getLanguage(filename: string): string {
  if (filename.endsWith(".py")) return "python"
  if (filename.endsWith(".json")) return "json"
  if (filename.endsWith(".txt")) return "text"
  if (filename.endsWith(".md")) return "markdown"
  if (filename.endsWith(".env") || filename.endsWith(".env.example")) return "env"
  if (filename.endsWith(".yaml") || filename.endsWith(".yml")) return "yaml"
  return "text"
}

function highlightPython(code: string): string {
  // Simple regex-based Python syntax highlighting via CSS classes
  return code
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    // Strings (double and single quoted)
    .replace(/("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')/g, '<span class="syn-str">$1</span>')
    // Comments
    .replace(/(#.*$)/gm, '<span class="syn-cmt">$1</span>')
    // Keywords
    .replace(/\b(def|class|import|from|return|if|elif|else|for|while|try|except|finally|with|as|yield|raise|pass|break|continue|and|or|not|in|is|None|True|False|self|async|await|lambda)\b/g, '<span class="syn-kw">$1</span>')
    // Decorators
    .replace(/^(\s*@\w+)/gm, '<span class="syn-dec">$1</span>')
    // Numbers
    .replace(/\b(\d+\.?\d*)\b/g, '<span class="syn-num">$1</span>')
}

function highlightCode(code: string, language: string): string {
  if (language === "python") return highlightPython(code)
  // For other languages, just escape HTML
  return code.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
}

export function CodePreview({ files }: Props) {
  const fileNames = Object.keys(files)
  const [selected, setSelected] = useState(fileNames[0] || "")
  const [copied, setCopied] = useState(false)

  const content = files[selected] || ""
  const language = getLanguage(selected)

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [content])

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <style>{`
        .syn-str { color: #a8db8a; }
        .syn-cmt { color: #6a737d; font-style: italic; }
        .syn-kw { color: #c792ea; font-weight: 500; }
        .syn-dec { color: #f9a825; }
        .syn-num { color: #f78c6c; }
      `}</style>
      <div className="flex min-h-[300px] max-h-[500px]">
        {/* File tree */}
        <div className="w-[160px] shrink-0 border-r border-border bg-surface overflow-y-auto">
          <div className="px-3 py-2 text-[10px] font-medium uppercase tracking-wider text-text-tertiary border-b border-border">
            Files
          </div>
          {fileNames.map((name) => (
            <button
              key={name}
              onClick={() => setSelected(name)}
              className={`w-full text-left px-3 py-1.5 text-[12px] font-mono truncate transition-colors ${
                name === selected
                  ? "bg-amber-500/10 text-amber-500 border-l-2 border-amber-500"
                  : "text-text-secondary hover:bg-surface-elevated hover:text-text-primary border-l-2 border-transparent"
              }`}
            >
              {name}
            </button>
          ))}
        </div>

        {/* Code panel */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-border bg-surface">
            <span className="text-[11px] font-mono text-text-tertiary truncate">{selected}</span>
            <button
              onClick={handleCopy}
              className="text-[11px] text-text-tertiary hover:text-text-primary transition-colors px-2 py-0.5 rounded"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
          <pre className="flex-1 overflow-auto p-3 text-[12px] leading-[1.6] font-mono text-text-primary bg-bg">
            <code dangerouslySetInnerHTML={{ __html: highlightCode(content, language) }} />
          </pre>
        </div>
      </div>
    </div>
  )
}
