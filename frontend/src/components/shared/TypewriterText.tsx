import { useState, useEffect, useRef } from 'react'

interface TypewriterTextProps {
  text: string
  speed?: number
  delay?: number
  className?: string
  onComplete?: () => void
}

export function TypewriterText({
  text,
  speed = 60,
  delay = 0,
  className = '',
  onComplete,
}: TypewriterTextProps) {
  const [displayed, setDisplayed] = useState('')
  const [started, setStarted] = useState(false)
  const onCompleteRef = useRef(onComplete)
  onCompleteRef.current = onComplete

  useEffect(() => {
    const delayTimeout = setTimeout(() => setStarted(true), delay)
    return () => clearTimeout(delayTimeout)
  }, [delay])

  useEffect(() => {
    if (!started) return

    if (displayed.length < text.length) {
      const timeout = setTimeout(() => {
        setDisplayed(text.slice(0, displayed.length + 1))
      }, speed)
      return () => clearTimeout(timeout)
    } else {
      onCompleteRef.current?.()
    }
  }, [displayed, text, speed, started])

  return (
    <span className={`typewriter-text ${className}`}>
      {displayed}
      {displayed.length < text.length && started && (
        <span className="typewriter-cursor">|</span>
      )}
    </span>
  )
}
