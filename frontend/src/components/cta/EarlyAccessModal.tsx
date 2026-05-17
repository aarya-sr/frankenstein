import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface EarlyAccessModalProps {
  isOpen: boolean
  onClose: () => void
  targetInterest?: string
}

export function EarlyAccessModal({ isOpen, onClose, targetInterest }: EarlyAccessModalProps) {
  const [email, setEmail] = useState('')
  const [interest, setInterest] = useState(targetInterest || '')
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return
    setSubmitting(true)
    setError('')

    const formspreeId = import.meta.env.VITE_FORMSPREE_ID
    if (formspreeId) {
      try {
        const res = await fetch(`https://formspree.io/f/${formspreeId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, interest }),
        })
        if (!res.ok) throw new Error('Submission failed')
      } catch {
        setError('Something went wrong. Please try again.')
        setSubmitting(false)
        return
      }
    }
    setSubmitting(false)
    setSubmitted(true)
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="modal-content"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Medical form header */}
            <div className="form-header">
              <div className="form-stamp">
                <span className="form-stamp-text">CONFIDENTIAL</span>
              </div>
              <h3 className="form-title">YOUR LABORATORY IS READY.</h3>
              <p className="form-id">INTAKE FORM — SUBJECT #{Math.floor(Math.random() * 9000 + 1000)}</p>
            </div>

            {!submitted ? (
              <form className="intake-form" onSubmit={handleSubmit}>
                {/* Form fields styled as medical intake */}
                <div className="form-field">
                  <label className="form-label">SUBJECT IDENTIFICATION (EMAIL)</label>
                  <input
                    type="email"
                    className="form-input typewriter-input"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="researcher@laboratory.io"
                    required
                    autoFocus
                  />
                </div>

                <div className="form-field">
                  <label className="form-label">PRIMARY RESEARCH INTEREST</label>
                  <select className="form-input form-select" value={interest} onChange={(e) => setInterest(e.target.value)}>
                    <option value="" disabled>Select area of study...</option>
                    <option value="finance">Financial Services</option>
                    <option value="healthcare">Healthcare</option>
                    <option value="legal">Legal</option>
                    <option value="operations">Operations</option>
                    <option value="other">Other Experiments</option>
                  </select>
                </div>

                {error && <p style={{ color: 'var(--crimson)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{error}</p>}

                <button type="submit" className="form-submit clickable" disabled={submitting}>
                  {submitting ? 'REGISTERING...' : 'REGISTER FOR EARLY ACCESS'}
                </button>

                <p className="form-disclaimer">
                  By registering, you consent to receive laboratory dispatches.
                  No specimens will be harmed.
                </p>
              </form>
            ) : (
              <div className="form-success">
                <p className="success-icon">&#x2713;</p>
                <p className="success-text">SUBJECT REGISTERED.</p>
                <p className="success-subtext">You will be contacted when the laboratory opens.</p>
              </div>
            )}

            {/* Close button */}
            <button className="modal-close clickable" onClick={onClose} aria-label="Close">
              &times;
            </button>
          </motion.div>

          <style>{`
            .modal-overlay {
              position: fixed;
              inset: 0;
              background: rgba(10,13,8,0.85);
              display: flex;
              align-items: center;
              justify-content: center;
              z-index: 200;
              padding: 1rem;
            }
            .modal-content {
              position: relative;
              background: linear-gradient(135deg, #f5f0e8 0%, #e8e0d0 100%);
              color: #2a2520;
              max-width: 480px;
              width: 100%;
              padding: 2.5rem 2rem;
              border-radius: 2px;
              box-shadow:
                0 20px 60px rgba(0,0,0,0.5),
                inset 0 0 80px rgba(0,0,0,0.03);
            }
            .form-header {
              text-align: center;
              margin-bottom: 2rem;
              position: relative;
            }
            .form-stamp {
              position: absolute;
              top: -10px;
              right: -10px;
              transform: rotate(12deg);
              border: 2px solid var(--crimson);
              padding: 0.2rem 0.5rem;
              opacity: 0.3;
            }
            .form-stamp-text {
              font-family: var(--font-mono);
              font-size: 0.6rem;
              color: var(--crimson);
              letter-spacing: 0.15em;
            }
            .form-title {
              font-family: var(--font-display);
              font-size: 1.5rem;
              color: #2a2520;
              margin-bottom: 0.3rem;
            }
            .form-id {
              font-family: var(--font-mono);
              font-size: 0.65rem;
              color: rgba(0,0,0,0.3);
              letter-spacing: 0.1em;
            }
            .intake-form {
              display: flex;
              flex-direction: column;
              gap: 1.2rem;
            }
            .form-field {
              display: flex;
              flex-direction: column;
              gap: 0.3rem;
            }
            .form-label {
              font-family: var(--font-mono);
              font-size: 0.65rem;
              letter-spacing: 0.1em;
              color: rgba(0,0,0,0.5);
            }
            .form-input {
              font-family: var(--font-display);
              font-size: 1rem;
              padding: 0.6rem 0.8rem;
              border: none;
              border-bottom: 2px solid var(--copper);
              background: transparent;
              color: #2a2520;
              outline: none;
            }
            .form-input:focus {
              border-bottom-color: var(--formaldehyde);
            }
            .form-select {
              appearance: none;
              background: transparent;
              cursor: pointer;
            }
            .form-submit {
              margin-top: 0.5rem;
              padding: 0.8rem;
              background: var(--bg);
              color: var(--formaldehyde);
              border: 1px solid var(--formaldehyde);
              font-family: var(--font-mono);
              font-size: 0.75rem;
              letter-spacing: 0.1em;
              transition: all 0.2s;
            }
            .form-submit:hover {
              background: #111a0d;
              box-shadow: 0 0 20px rgba(57,255,20,0.2);
            }
            .form-disclaimer {
              font-family: var(--font-body);
              font-size: 0.75rem;
              color: rgba(0,0,0,0.3);
              text-align: center;
              font-style: italic;
            }
            .form-success {
              text-align: center;
              padding: 2rem 0;
            }
            .success-icon {
              font-size: 3rem;
              color: #39ff14;
              text-shadow: 0 0 20px rgba(57,255,20,0.5);
              margin-bottom: 1rem;
            }
            .success-text {
              font-family: var(--font-mono);
              font-size: 1.1rem;
              letter-spacing: 0.1em;
              color: #2a2520;
              margin-bottom: 0.5rem;
            }
            .success-subtext {
              font-family: var(--font-body);
              font-size: 0.9rem;
              color: rgba(0,0,0,0.5);
            }
            .modal-close {
              position: absolute;
              top: 1rem;
              right: 1rem;
              background: none;
              border: none;
              font-size: 1.5rem;
              color: rgba(0,0,0,0.3);
              line-height: 1;
              padding: 0.2rem;
            }
            .modal-close:hover {
              color: rgba(0,0,0,0.6);
            }
          `}</style>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
