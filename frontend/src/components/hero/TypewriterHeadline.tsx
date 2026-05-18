import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

type HeadlinePhase = 'empty' | 'it' | 'was' | 'alive' | 'strike' | 'is' | 'complete'

export function TypewriterHeadline() {
  const [phase, setPhase] = useState<HeadlinePhase>('empty')

  useEffect(() => {
    const timeline: { phase: HeadlinePhase; delay: number }[] = [
      { phase: 'it', delay: 400 },
      { phase: 'was', delay: 1200 },
      { phase: 'alive', delay: 2000 },
      { phase: 'strike', delay: 3200 },
      { phase: 'is', delay: 3600 },
      { phase: 'complete', delay: 4200 },
    ]

    const timeouts = timeline.map(({ phase: p, delay }) =>
      setTimeout(() => setPhase(p), delay)
    )

    return () => timeouts.forEach(clearTimeout)
  }, [])

  const phaseIndex = ['empty', 'it', 'was', 'alive', 'strike', 'is', 'complete'].indexOf(phase)

  const showIt = phaseIndex >= 1
  const showMiddle = phaseIndex >= 2
  const showAlive = phaseIndex >= 3
  const isStruck = phaseIndex >= 4
  const showIs = phaseIndex >= 5
  const isComplete = phaseIndex >= 6

  return (
    <div className="headline-container">
      <h1 className="headline">
        {/* IT */}
        <motion.span
          className="headline-word"
          initial={{ opacity: 0, y: 30 }}
          animate={showIt ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.4 }}
        >
          IT
        </motion.span>

        {/* WAS / IS */}
        <span className="headline-word headline-middle">
          {/* WAS — fades out when IS appears */}
          <motion.span
            className="headline-was"
            initial={{ opacity: 0, y: 30 }}
            animate={
              showIs
                ? { opacity: 0, y: 0, display: 'none' }
                : showMiddle
                ? { opacity: isStruck ? 0.4 : 1, y: 0 }
                : { opacity: 0, y: 30 }
            }
            transition={{ duration: 0.3 }}
            style={{ position: 'relative' }}
          >
            WAS
            {isStruck && !showIs && (
              <motion.span
                className="strikethrough"
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ duration: 0.2 }}
              />
            )}
          </motion.span>

          {/* IS — appears after strike */}
          {showIs && (
            <motion.span
              className="headline-is"
              initial={{ opacity: 0, scale: 1.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.25, type: 'spring', stiffness: 400, damping: 15 }}
            >
              IS
              <motion.span
                className="spark"
                initial={{ opacity: 1, scale: 1 }}
                animate={{ opacity: 0, scale: 2 }}
                transition={{ duration: 0.6 }}
              />
            </motion.span>
          )}
        </span>

        {/* ALIVE */}
        <motion.span
          className="headline-word"
          initial={{ opacity: 0, y: 30 }}
          animate={showAlive ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.4 }}
        >
          ALIVE.
        </motion.span>
      </h1>

      <motion.p
        className="headline-subtitle"
        initial={{ opacity: 0 }}
        animate={isComplete ? { opacity: 1 } : {}}
        transition={{ duration: 1, delay: 0.2 }}
      >
        <span className="specimen-label">frankenstein / build agents from language</span>
      </motion.p>

      <style>{`
        .headline-container {
          text-align: center;
          position: relative;
          z-index: 2;
        }
        .headline {
          font-family: var(--font-display);
          font-size: clamp(3rem, 8vw, 7rem);
          color: var(--bone);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.25em;
          line-height: 1;
          min-height: 1.2em;
          text-shadow: 0 2px 20px rgba(0,0,0,0.8), 0 0 40px rgba(0,0,0,0.5);
        }
        .headline-word {
          display: inline-block;
        }
        .headline-middle {
          position: relative;
          min-width: 2ch;
          display: inline-flex;
          align-items: center;
          justify-content: center;
        }
        .headline-was {
          position: relative;
          display: inline-block;
        }
        .strikethrough {
          position: absolute;
          left: -5%;
          right: -5%;
          top: 50%;
          height: 4px;
          background: var(--formaldehyde);
          transform: translateY(-50%);
          transform-origin: left center;
          box-shadow: 0 0 10px var(--formaldehyde), 0 0 20px var(--formaldehyde-glow);
        }
        .headline-is {
          color: var(--formaldehyde);
          text-shadow: 0 0 30px var(--formaldehyde-glow), 0 0 60px var(--formaldehyde-dim);
          position: relative;
          display: inline-block;
        }
        .spark {
          position: absolute;
          top: 50%;
          left: 50%;
          width: 40px;
          height: 40px;
          margin: -20px 0 0 -20px;
          background: radial-gradient(circle, #fff 0%, var(--formaldehyde) 30%, transparent 70%);
          border-radius: 50%;
          pointer-events: none;
        }
        .headline-subtitle {
          margin-top: 1.5rem;
          text-shadow: 0 1px 10px rgba(0,0,0,0.6);
        }
      `}</style>
    </div>
  )
}
