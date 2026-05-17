import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'

const NOTES = [
  {
    quote: "I described a loan underwriting workflow in plain English. Ten minutes later I had a working multi-agent pipeline with proper validation and error handling.",
    author: 'Subject #0031',
    role: 'Financial Services Engineer',
  },
  {
    quote: "The critic agent found three edge cases in my spec that would have taken days to discover in production. Cross-model adversarial review is no joke.",
    author: 'Subject #0047',
    role: 'ML Platform Lead',
  },
  {
    quote: "We went from 'I have an idea for automating supplier scoring' to a testable CrewAI project in under 15 minutes. The learning loop means each build gets smarter.",
    author: 'Subject #0082',
    role: 'Operations Analyst',
  },
]

const ROTATIONS = [-2, 1.5, -1]

export function ResearchNotes() {
  const ref = useRef<HTMLElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-100px' })

  return (
    <section ref={ref} className="research-notes-section">
      <div className="research-notes-header">
        <h2>Field Notes</h2>
        <p className="lab-label">From Early Subjects</p>
      </div>

      <div className="notes-grid">
        {NOTES.map((note, i) => (
          <motion.div
            key={i}
            className="research-note"
            initial={{ opacity: 0, y: 60 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: i * 0.2, duration: 0.5, ease: 'easeOut' }}
            whileHover={{ y: -8, rotate: 0, scale: 1.03 }}
            style={{ rotate: ROTATIONS[i] }}
          >
            <p className="note-quote">"{note.quote}"</p>
            <div className="note-footer">
              <div className="note-author">
                <span className="note-name">{note.author}</span>
                <span className="note-role">{note.role}</span>
              </div>
              <span className="note-stamp">VERIFIED SUBJECT</span>
            </div>
          </motion.div>
        ))}
      </div>

      <style>{`
        .research-notes-section {
          min-height: 60vh;
          padding: var(--section-pad) clamp(1rem, 5vw, 4rem);
        }
        .research-notes-header {
          text-align: center;
          margin-bottom: 3rem;
        }
        .research-notes-header h2 {
          margin-bottom: 0.5rem;
        }
        .notes-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 2rem;
          max-width: 900px;
          margin: 0 auto;
        }
        .research-note {
          background: linear-gradient(135deg, #f5f0e8 0%, #ebe5d8 50%, #e0d8c8 100%);
          color: #2a2520;
          padding: 1.5rem;
          border-radius: 2px;
          box-shadow: 2px 4px 12px rgba(0,0,0,0.3);
          position: relative;
          cursor: default;
          transition: box-shadow 0.3s;
        }
        .research-note:hover {
          box-shadow: 4px 8px 20px rgba(0,0,0,0.4);
        }
        .note-quote {
          font-family: var(--font-body);
          font-size: 0.95rem;
          line-height: 1.6;
          font-style: italic;
          margin-bottom: 1rem;
        }
        .note-footer {
          display: flex;
          align-items: flex-end;
          justify-content: space-between;
          gap: 0.5rem;
        }
        .note-author {
          display: flex;
          flex-direction: column;
        }
        .note-name {
          font-family: var(--font-mono);
          font-size: 0.65rem;
          letter-spacing: 0.1em;
          color: #2a2520;
        }
        .note-role {
          font-family: var(--font-body);
          font-size: 0.75rem;
          color: rgba(42,37,32,0.5);
        }
        .note-stamp {
          font-family: var(--font-mono);
          font-size: 0.5rem;
          letter-spacing: 0.1em;
          color: var(--crimson);
          border: 1px solid var(--crimson);
          padding: 0.15rem 0.4rem;
          opacity: 0.4;
          transform: rotate(3deg);
          white-space: nowrap;
        }
        @media (max-width: 768px) {
          .notes-grid {
            grid-template-columns: 1fr;
            max-width: 400px;
          }
        }
      `}</style>
    </section>
  )
}
