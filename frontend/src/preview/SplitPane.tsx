import { useState, useCallback, useRef, type ReactNode } from "react"

interface Props {
  left: ReactNode
  right: ReactNode
  defaultLeftWidth?: number
  minLeftWidth?: number
  maxLeftWidth?: number
}

export function SplitPane({
  left,
  right,
  defaultLeftWidth = 320,
  minLeftWidth = 200,
  maxLeftWidth = 600,
}: Props) {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth)
  const dragging = useRef(false)

  const handleMouseDown = useCallback(() => {
    dragging.current = true

    const handleMouseMove = (e: MouseEvent) => {
      if (!dragging.current) return
      const newWidth = Math.min(maxLeftWidth, Math.max(minLeftWidth, e.clientX))
      setLeftWidth(newWidth)
    }

    const handleMouseUp = () => {
      dragging.current = false
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseup", handleMouseUp)
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
    }

    document.addEventListener("mousemove", handleMouseMove)
    document.addEventListener("mouseup", handleMouseUp)
    document.body.style.cursor = "col-resize"
    document.body.style.userSelect = "none"
  }, [minLeftWidth, maxLeftWidth])

  return (
    <div className="flex flex-1 overflow-hidden">
      <div className="flex flex-col overflow-hidden" style={{ width: leftWidth, minWidth: minLeftWidth }}>
        {left}
      </div>
      <div
        className="w-1 cursor-col-resize bg-border hover:bg-accent/50 transition-colors shrink-0"
        onMouseDown={handleMouseDown}
      />
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {right}
      </div>
    </div>
  )
}
