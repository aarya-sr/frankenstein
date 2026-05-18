import { useState, useEffect, useCallback, Suspense } from 'react'
import { useNavigate } from 'react-router-dom'
import { Canvas } from '@react-three/fiber'
import { EffectComposer, Bloom } from '@react-three/postprocessing'
import { motion, AnimatePresence } from 'framer-motion'
import { TypewriterHeadline } from './TypewriterHeadline'
import { OrganismFragments } from './OrganismFragments'
import { AssemblyAnimation } from './AssemblyAnimation'
import { LaboratoryVoid } from './LaboratoryVoid'
import { EnergyConnections } from '../three/EnergyConnections'
import { useAssemblyTrigger } from '../../hooks/useAssemblyTrigger'
import { useLabStore } from '../../store/labState'
import { useAudio } from '../../hooks/useAudio'

const PLACEHOLDERS = [
  'A loan underwriting co-pilot that reads PDFs and assesses risk...',
  'A supplier reliability scorer that processes CSV data...',
  'A customer support agent that routes and resolves tickets...',
  'An invoice processor that extracts line items and validates...',
  'A legal document reviewer that flags compliance issues...',
]

export function HeroSection() {
  const navigate = useNavigate()
  const { triggerAssembly, assemblyPhase } = useAssemblyTrigger()
  const { userPrompt, setUserPrompt } = useLabStore()
  const { initAudio, play } = useAudio()
  const [placeholderIndex, setPlaceholderIndex] = useState(0)
  const [curtainOpen, setCurtainOpen] = useState(false)
  const [showContent, setShowContent] = useState(false)

  // Opening curtain sequence — fast reveal
  useEffect(() => {
    const t1 = setTimeout(() => setCurtainOpen(true), 100)
    const t2 = setTimeout(() => setShowContent(true), 300)
    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [])

  // Cycle placeholders
  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholderIndex((i) => (i + 1) % PLACEHOLDERS.length)
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      const prompt = userPrompt.trim()
      if (!prompt) return
      initAudio()
      play('assembly')
      triggerAssembly()
      // Navigate to /chat with prompt after a brief animation beat
      setTimeout(() => {
        navigate('/chat', { state: { prompt } })
      }, 800)
    },
    [userPrompt, triggerAssembly, initAudio, play, navigate]
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSubmit(e as unknown as React.FormEvent)
      }
    },
    [handleSubmit]
  )

  const isActivelyAssembling = assemblyPhase === 'pulling' || assemblyPhase === 'stitching' || assemblyPhase === 'lightning'

  return (
    <section className="hero-section" data-section="hero">
      {/* Opening curtain */}
      <AnimatePresence>
        {!curtainOpen && (
          <>
            <motion.div
              className="curtain curtain--left"
              initial={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ duration: 0.3, ease: [0.76, 0, 0.24, 1] }}
            />
            <motion.div
              className="curtain curtain--right"
              initial={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ duration: 0.3, ease: [0.76, 0, 0.24, 1] }}
            />
          </>
        )}
      </AnimatePresence>

      {/* 3D Canvas — background */}
      <div className="hero-canvas">
        <Canvas
          camera={{ position: [0, 0, 6], fov: 45 }}
          dpr={[1, 1.5]}
          gl={{ antialias: true, alpha: true }}
        >
          <Suspense fallback={null}>
            <LaboratoryVoid />
            <ambientLight intensity={0.15} />
            <pointLight
              position={[0, -3, 3]}
              intensity={0.8}
              color="#39ff14"
              distance={12}
            />
            <OrganismFragments />
            <EnergyConnections />
            <EffectComposer>
              <Bloom
                luminanceThreshold={0.2}
                luminanceSmoothing={0.9}
                intensity={0.8}
                mipmapBlur
              />
            </EffectComposer>
          </Suspense>
        </Canvas>
      </div>

      {/* EKG line across the top */}
      <svg className="hero-ekg" viewBox="0 0 1200 80" preserveAspectRatio="none">
        <motion.path
          d="M 0 40 L 200 40 L 250 40 L 280 40 L 320 40 L 400 40 L 500 40 L 550 40 L 560 15 L 570 65 L 580 10 L 590 70 L 600 40 L 650 40 L 700 40 L 800 40 L 900 40 L 1000 40 L 1200 40"
          stroke="var(--formaldehyde)"
          strokeWidth="2"
          fill="none"
          opacity="0.15"
          initial={{ pathLength: 0 }}
          animate={showContent ? { pathLength: 1 } : {}}
          transition={{ duration: 2, delay: 0.5, ease: 'easeInOut' }}
        />
      </svg>

      {/* Overlay content */}
      <motion.div
        className="hero-content"
        initial={{ opacity: 0 }}
        animate={showContent ? { opacity: 1 } : {}}
        transition={{ duration: 0.6 }}
      >
        <TypewriterHeadline />

        {/* Prompt input */}
        <motion.form
          className="prompt-box"
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 30 }}
          animate={showContent ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 1, duration: 0.6 }}
        >
          <label className="prompt-label">DESCRIBE YOUR WORKFLOW —</label>
          <div className="prompt-input-wrapper">
            <textarea
              className="prompt-input typewriter-input"
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              onClick={initAudio}
              placeholder={PLACEHOLDERS[placeholderIndex]}
              disabled={isActivelyAssembling}
              rows={2}
            />
            <button
              type="submit"
              className="prompt-submit clickable"
              disabled={isActivelyAssembling || !userPrompt.trim()}
            >
              ASSEMBLE
            </button>
          </div>
        </motion.form>
      </motion.div>

      {/* Assembly overlays */}
      <AssemblyAnimation />

      <style>{`
        .hero-section {
          position: relative;
          height: 100vh;
          min-height: 600px;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
        }

        /* Curtain */
        .curtain {
          position: absolute;
          top: 0;
          bottom: 0;
          width: 50%;
          background: #030504;
          z-index: 90;
        }
        .curtain--left { left: 0; }
        .curtain--right { right: 0; }

        /* Screen flicker */
        .screen-flicker {
          position: absolute;
          inset: 0;
          background: var(--formaldehyde);
          pointer-events: none;
          z-index: 80;
          mix-blend-mode: overlay;
        }

        /* EKG */
        .hero-ekg {
          position: absolute;
          bottom: 20%;
          left: 0;
          right: 0;
          width: 100%;
          height: 60px;
          z-index: 1;
          pointer-events: none;
          opacity: 0.3;
        }

        .hero-canvas {
          position: absolute;
          inset: 0;
          z-index: 0;
        }
        .hero-content {
          position: relative;
          z-index: 2;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 2.5rem;
          padding: 2rem;
          max-width: 700px;
          width: 100%;
          background: radial-gradient(ellipse at center, rgba(10,13,8,0.75) 0%, transparent 70%);
          border-radius: 24px;
        }

        /* Scroll indicator */
        .scroll-indicator {
          position: absolute;
          bottom: 2rem;
          left: 50%;
          transform: translateX(-50%);
          z-index: 3;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.4rem;
        }
        .scroll-indicator-text {
          font-family: var(--font-mono);
          font-size: 0.55rem;
          letter-spacing: 0.2em;
          color: var(--bone-dim);
          opacity: 0.5;
        }
        .scroll-indicator-arrow {
          opacity: 0.5;
        }

        /* Prompt Box */
        .prompt-box {
          width: 100%;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .prompt-label {
          font-family: var(--font-mono);
          font-size: 0.7rem;
          letter-spacing: 0.15em;
          color: var(--formaldehyde);
          text-transform: uppercase;
        }
        .prompt-input-wrapper {
          display: flex;
          gap: 0.75rem;
          align-items: flex-end;
        }
        .prompt-input {
          flex: 1;
          background: linear-gradient(135deg, #f5f0e8 0%, #e8e0d0 100%);
          border: 2px solid var(--copper);
          border-radius: 2px;
          padding: 0.75rem 1rem;
          font-family: var(--font-display);
          font-size: 1rem;
          color: #1a1a1a;
          resize: none;
          outline: none;
          box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }
        .prompt-input::placeholder {
          color: #999;
          font-style: italic;
        }
        .prompt-input:focus {
          border-color: var(--formaldehyde);
          box-shadow: inset 0 2px 4px rgba(0,0,0,0.1), 0 0 10px var(--formaldehyde-dim);
        }
        .prompt-submit {
          background: transparent;
          border: 1px solid var(--formaldehyde);
          color: var(--formaldehyde);
          font-family: var(--font-mono);
          font-size: 0.75rem;
          letter-spacing: 0.1em;
          padding: 0.6rem 1.2rem;
          text-transform: uppercase;
          transition: all 0.2s;
        }
        .prompt-submit:hover:not(:disabled) {
          background: var(--formaldehyde-dim);
          box-shadow: 0 0 15px var(--formaldehyde-dim);
        }
        .prompt-submit:disabled {
          opacity: 0.3;
        }

        @media (max-width: 640px) {
          .prompt-input-wrapper {
            flex-direction: column;
          }
          .prompt-submit {
            width: 100%;
          }
        }
      `}</style>
    </section>
  )
}
