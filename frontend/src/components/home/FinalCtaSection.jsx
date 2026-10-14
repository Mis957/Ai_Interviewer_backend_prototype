import useScrollReveal from './useScrollReveal'
import HandwrittenHighlight from './HandwrittenHighlight'
import { Link } from 'react-router-dom'

const scrollTo = (id) => {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth' })
}

export default function FinalCtaSection() {
  const ref = useScrollReveal({ threshold: 0.15 })

  return (
    <section className="final-cta-section" ref={ref} aria-labelledby="cta-heading">
      <div className="shell">
        <div className="final-cta-card">
          <div className="final-cta-glow" aria-hidden="true" />
          <div className="final-cta-content">
            <div className="final-cta-eyebrow-wrapper">
              <span className="final-cta-handwritten-tag">
                <span className="final-cta-handwritten-text">Ready for your next opportunity?</span>
                <svg className="crisp-swoop-svg" viewBox="0 0 160 14" fill="none" aria-hidden="true" preserveAspectRatio="none">
                  <path d="M2 9 C 45 2, 115 2, 158 8" stroke="#ffffff" strokeWidth="2.4" strokeLinecap="round" />
                </svg>
              </span>
            </div>
            <h2 id="cta-heading" className="final-cta-heading">
              From first placement<br />
              to every next room.
            </h2>
            <p className="final-cta-sub">
              Stop guessing how you sound. Step into a realistic voice rehearsal with Vedanta and build the poise, structure, and confidence top teams look for.
            </p>
            <div className="final-cta-actions">
              <Link to="/setup" className="btn btn-primary final-cta-btn">
                Start Practicing Free
                <svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="btn-arrow">
                  <path d="M2.5 8h10M8.5 3.5l4.5 4.5-4.5 4.5" />
                </svg>
              </Link>
              <button
                type="button"
                className="btn btn-secondary final-cta-btn-secondary"
                onClick={() => scrollTo('pricing')}
              >
                View Plans & Pricing
              </button>
            </div>
            <div className="final-cta-badges" aria-label="Key guarantees">
              <span>✓ No credit card required</span>
              <span className="dot">•</span>
              <span>✓ Tailored to your resume</span>
              <span className="dot">•</span>
              <span>✓ Instant rubric feedback</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
