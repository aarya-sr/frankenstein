import { useState, useEffect, useRef } from 'react'
import { useControls, Leva } from 'leva'
import { motion, useScroll, useTransform, useInView } from 'framer-motion'
import { HeroSection } from './components/hero/HeroSection'
import { DissectionTable } from './components/pipeline/DissectionTable'
import { LabJournalSection } from './components/demo/LabJournalSection'
import { SpecimenCabinet } from './components/specimens/SpecimenCabinet'
import { PowerSection } from './components/cta/PowerSection'
import { VoltageCounter } from './components/shared/VoltageCounter'
import { NecropsisBench } from './components/comparison/NecropsisBench'
import { ResearchNotes } from './components/social/ResearchNotes'
import { SectionDivider } from './components/shared/SectionDivider'
import { LabStickyNav } from './components/shared/LabStickyNav'
import { useScrollProgress } from './hooks/useScrollProgress'
import { useLabStore } from './store/labState'
import './styles/globals.css'
import './styles/typography.css'
import './styles/cursor.css'

function LabControls() {
  const setUniform = useLabStore((s) => s.setUniform)

  const values = useControls('LAB CONTROLS', {
    ASSEMBLY_SPEED: { value: 1.0, min: 0.1, max: 3.0, step: 0.1 },
    VOLTAGE_INTENSITY: { value: 1.0, min: 0.1, max: 5.0, step: 0.1 },
    NEURAL_DENSITY: { value: 1.0, min: 0.1, max: 3.0, step: 0.1 },
    FORMALDEHYDE_CONCENTRATION: { value: 0.5, min: 0.0, max: 1.0, step: 0.05 },
  })

  useEffect(() => {
    setUniform('assemblySpeed', values.ASSEMBLY_SPEED)
    setUniform('voltageIntensity', values.VOLTAGE_INTENSITY)
    setUniform('neuralDensity', values.NEURAL_DENSITY)
    setUniform('formaldehydeConcentration', values.FORMALDEHYDE_CONCENTRATION)
  }, [values, setUniform])

  return null
}

function ScrollProgressBar() {
  const scrollProgress = useLabStore((s) => s.scrollProgress)

  return (
    <motion.div
      className="scroll-progress-bar"
      style={{ scaleX: scrollProgress, transformOrigin: 'left' }}
    />
  )
}

function FrankensteinFooter() {
  const ref = useRef<HTMLElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-50px' })
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start end', 'end end'],
  })

  const glowIntensity = useTransform(scrollYProgress, [0.3, 0.8], [0, 1])

  const LETTERS = 'FRANKENSTEIN'.split('')

  return (
    <footer ref={ref} className="monster-footer">
      {/* Giant title */}
      <div className="monster-title-row">
        {LETTERS.map((letter, i) => (
          <motion.span
            key={i}
            className="monster-letter"
            initial={{ opacity: 0, y: 60, rotateZ: (Math.random() - 0.5) * 20 }}
            animate={isInView ? { opacity: 1, y: 0, rotateZ: 0 } : {}}
            transition={{
              delay: i * 0.06,
              duration: 0.5,
              type: 'spring',
              stiffness: 200,
              damping: 15,
            }}
          >
            {letter}
          </motion.span>
        ))}
      </div>

      {/* Monster face SVG */}
      <motion.div
        className="monster-face-wrapper"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={isInView ? { opacity: 1, scale: 1 } : {}}
        transition={{ delay: 0.7, duration: 0.6 }}
      >
        <svg viewBox="0 0 200 180" className="monster-face" aria-label="Frankenstein's monster">
          {/* Head shape */}
          <rect x="40" y="10" width="120" height="140" rx="12" fill="none" stroke="var(--formaldehyde)" strokeWidth="2" opacity="0.6" />

          {/* Flat top */}
          <line x1="40" y1="10" x2="160" y2="10" stroke="var(--formaldehyde)" strokeWidth="3" opacity="0.8" />

          {/* Neck bolts */}
          <motion.circle
            cx="28" cy="90" r="8"
            fill="none" stroke="var(--copper)" strokeWidth="2"
            animate={isInView ? { opacity: [0.4, 1, 0.4] } : {}}
            transition={{ duration: 2, repeat: Infinity, delay: 1 }}
          />
          <circle cx="28" cy="90" r="3" fill="var(--copper)" opacity="0.6" />
          <motion.circle
            cx="172" cy="90" r="8"
            fill="none" stroke="var(--copper)" strokeWidth="2"
            animate={isInView ? { opacity: [0.4, 1, 0.4] } : {}}
            transition={{ duration: 2, repeat: Infinity, delay: 1.3 }}
          />
          <circle cx="172" cy="90" r="3" fill="var(--copper)" opacity="0.6" />

          {/* Eyes */}
          <motion.circle
            cx="75" cy="60" r="10"
            fill="none" stroke="var(--formaldehyde)" strokeWidth="1.5"
            style={{ opacity: glowIntensity }}
          />
          <motion.circle
            cx="75" cy="60" r="4"
            fill="var(--formaldehyde)"
            style={{ opacity: glowIntensity }}
          />
          <motion.circle
            cx="125" cy="60" r="10"
            fill="none" stroke="var(--formaldehyde)" strokeWidth="1.5"
            style={{ opacity: glowIntensity }}
          />
          <motion.circle
            cx="125" cy="60" r="4"
            fill="var(--formaldehyde)"
            style={{ opacity: glowIntensity }}
          />

          {/* Forehead stitches */}
          <motion.path
            d="M 65 30 L 70 22 L 75 30 L 80 22 L 85 30 L 90 22 L 95 30 L 100 22 L 105 30 L 110 22 L 115 30 L 120 22 L 125 30 L 130 22 L 135 30"
            stroke="var(--copper)" strokeWidth="1.5" fill="none" opacity="0.5"
            initial={{ pathLength: 0 }}
            animate={isInView ? { pathLength: 1 } : {}}
            transition={{ delay: 1, duration: 1.2 }}
          />

          {/* Cheek scar */}
          <motion.path
            d="M 55 75 L 62 85 L 55 95"
            stroke="var(--crimson)" strokeWidth="1.5" fill="none" opacity="0.4"
            initial={{ pathLength: 0 }}
            animate={isInView ? { pathLength: 1 } : {}}
            transition={{ delay: 1.5, duration: 0.6 }}
          />

          {/* Mouth — stitched shut */}
          <line x1="75" y1="115" x2="125" y2="115" stroke="var(--bone-dim)" strokeWidth="1.5" opacity="0.4" />
          {[0, 1, 2, 3, 4].map((i) => (
            <motion.line
              key={i}
              x1={80 + i * 10} y1="110"
              x2={80 + i * 10} y2="120"
              stroke="var(--copper)" strokeWidth="1"
              opacity="0.5"
              initial={{ pathLength: 0 }}
              animate={isInView ? { pathLength: 1 } : {}}
              transition={{ delay: 1.8 + i * 0.1, duration: 0.2 }}
            />
          ))}
        </svg>

        {/* Electricity arcs from bolts */}
        <motion.div
          className="bolt-spark bolt-spark--left"
          animate={isInView ? { opacity: [0, 0.8, 0] } : {}}
          transition={{ duration: 0.3, repeat: Infinity, repeatDelay: 2.5, delay: 2 }}
        />
        <motion.div
          className="bolt-spark bolt-spark--right"
          animate={isInView ? { opacity: [0, 0.8, 0] } : {}}
          transition={{ duration: 0.3, repeat: Infinity, repeatDelay: 3, delay: 2.5 }}
        />
      </motion.div>

      {/* Subtitle */}
      <motion.p
        className="monster-subtitle"
        initial={{ opacity: 0 }}
        animate={isInView ? { opacity: 1 } : {}}
        transition={{ delay: 1.5, duration: 0.8 }}
      >
        IT'S ALIVE. MOSTLY.
      </motion.p>

      {/* Bottom bar */}
      <div className="footer-bottom">
        <span className="lab-label">PS-03 HACKATHON</span>
        <span className="lab-label footer-hint">Ctrl+Shift+L for lab controls</span>
      </div>
    </footer>
  )
}

export default function App() {
  useScrollProgress()
  const [levaHidden, setLevaHidden] = useState(true)

  // Leva panel toggle via Ctrl+Shift+L
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'L') {
        e.preventDefault()
        setLevaHidden((h) => !h)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <div className="lab-landing">
      {import.meta.env.DEV && <Leva hidden={levaHidden} />}
      {import.meta.env.DEV && <LabControls />}
      <ScrollProgressBar />
      <LabStickyNav />

      <main>
        <HeroSection />

        <SectionDivider label="ACT II" />
        <VoltageCounter />
        <DissectionTable />

        <SectionDivider label="ACT III" />
        <NecropsisBench />
        <LabJournalSection />

        <SectionDivider label="ACT IV" />
        <SpecimenCabinet />

        <SectionDivider label="ACT V" />
        <ResearchNotes />
        <PowerSection />
      </main>

      <FrankensteinFooter />

      <style>{`
        .scroll-progress-bar {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          height: 2px;
          background: linear-gradient(90deg, var(--copper), var(--formaldehyde));
          z-index: 100;
          pointer-events: none;
        }

        /* Monster footer */
        .monster-footer {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2rem;
          padding: clamp(3rem, 8vh, 6rem) 1rem 2rem;
          border-top: 1px solid var(--copper-dim);
          overflow: hidden;
          position: relative;
        }
        .monster-title-row {
          display: flex;
          gap: 0;
          justify-content: center;
          flex-wrap: nowrap;
        }
        .monster-letter {
          font-family: var(--font-display);
          font-size: clamp(3rem, 10vw, 8rem);
          color: var(--bone);
          line-height: 1;
          text-shadow:
            0 0 20px var(--formaldehyde-glow),
            0 0 60px rgba(57, 255, 20, 0.15);
          display: inline-block;
        }
        .monster-face-wrapper {
          position: relative;
          width: 160px;
          height: 160px;
        }
        .monster-face {
          width: 100%;
          height: 100%;
        }
        .bolt-spark {
          position: absolute;
          width: 20px;
          height: 2px;
          background: var(--formaldehyde);
          box-shadow: 0 0 8px var(--formaldehyde-glow);
          top: 50%;
        }
        .bolt-spark--left {
          left: -10px;
          transform: rotate(-15deg);
        }
        .bolt-spark--right {
          right: -10px;
          transform: rotate(15deg);
        }
        .monster-subtitle {
          font-family: var(--font-mono);
          font-size: 0.75rem;
          letter-spacing: 0.25em;
          color: var(--formaldehyde);
          text-shadow: 0 0 12px var(--formaldehyde-glow);
          opacity: 0.7;
        }
        .footer-bottom {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 1rem clamp(1rem, 5vw, 3rem);
          border-top: 1px solid var(--copper-dim);
          margin-top: 1rem;
        }
        .footer-hint {
          opacity: 0.3;
        }

        @media (max-width: 600px) {
          .monster-letter {
            font-size: clamp(2rem, 8vw, 4rem);
          }
          .monster-face-wrapper {
            width: 120px;
            height: 120px;
          }
        }
      `}</style>
    </div>
  )
}
