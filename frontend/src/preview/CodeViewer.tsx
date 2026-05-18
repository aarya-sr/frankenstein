import { useEffect, useRef } from "react"
import hljs from "highlight.js/lib/core"
import python from "highlight.js/lib/languages/python"
import "highlight.js/styles/github-dark.min.css"

hljs.registerLanguage("python", python)

interface Props {
  code: string
  filename: string
}

export function CodeViewer({ code, filename }: Props) {
  const codeRef = useRef<HTMLElement>(null)

  const isPython = filename.endsWith(".py")

  useEffect(() => {
    if (codeRef.current && isPython) {
      hljs.highlightElement(codeRef.current)
    }
  }, [code, isPython])

  return (
    <div className="flex-1 overflow-auto bg-[#0d1117]">
      <div className="px-3 py-1.5 text-[11px] text-text-tertiary border-b border-border sticky top-0 bg-[#0d1117] z-10">
        {filename}
      </div>
      <pre className="p-3 text-[12px] leading-[1.6] overflow-x-auto">
        <code
          ref={codeRef}
          className={isPython ? "language-python" : ""}
          key={filename}
        >
          {code}
        </code>
      </pre>
    </div>
  )
}
