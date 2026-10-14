import useScrollReveal from './useScrollReveal'
import HandwrittenHighlight from './HandwrittenHighlight'

export default function FeaturesSection() {
  const ref = useScrollReveal({ threshold: 0.08 })

  return (
    <section className="feat-section" id="features" aria-labelledby="feat-heading" ref={ref}>
      <div className="feat-shell shell">

        {/* Header row */}
        <header className="feat-header">
          <div className="feat-eyebrow-wrapper">
            <HandwrittenHighlight size="32px">
              Everything you need to practice properly
            </HandwrittenHighlight>
          </div>
          <h2 className="feat-heading" id="feat-heading">
            Your interview.<br />
            Not a random<br />
            question set.
          </h2>
          <p className="feat-sub">
            Parisamvad builds your session directly from your resume and the role you're targeting—so every question is grounded in context that actually matters.
          </p>
        </header>

        {/* Balanced, clean 3-card grid */}
        <div className="feat-grid-clean" aria-label="Key features">

          {/* Card 1 */}
          <article className="feat-grid-card">
            <div className="feat-card-top">
              <span className="feat-card-badge">01</span>
              <div className="feat-visual-box feat-visual-box--flow">
                <span className="feat-pill-tag">Resume.pdf</span>
                <span className="feat-arrow-symbol">→</span>
                <span className="feat-pill-tag feat-pill-tag--active">Tailored Questions</span>
              </div>
            </div>
            <div className="feat-card-content">
              <h3 className="feat-card-title">Built around you, not a template</h3>
              <p className="feat-card-desc">
                Upload your resume, paste a target job description, or pick an interview track. Parisamvad grounds every prompt in your actual experience.
              </p>
            </div>
          </article>

          {/* Card 2 */}
          <article className="feat-grid-card">
            <div className="feat-card-top">
              <span className="feat-card-badge">02</span>
              <div className="feat-visual-box feat-visual-box--voice">
                <div className="feat-voice-bars" aria-hidden="true">
                  <span style={{ height: '14px' }} />
                  <span style={{ height: '26px' }} />
                  <span style={{ height: '10px' }} />
                  <span style={{ height: '32px' }} />
                  <span style={{ height: '18px' }} />
                  <span style={{ height: '28px' }} />
                  <span style={{ height: '12px' }} />
                </div>
                <span className="feat-voice-status">Vedanta Listening</span>
              </div>
            </div>
            <div className="feat-card-content">
              <h3 className="feat-card-title">Real voice. Real conversation</h3>
              <p className="feat-card-desc">
                Speak your answers aloud. Vedanta listens, reacts, and asks natural follow-up questions to test your composure under realistic timed pressure.
              </p>
            </div>
          </article>

          {/* Card 3 */}
          <article className="feat-grid-card">
            <div className="feat-card-top">
              <span className="feat-card-badge">03</span>
              <div className="feat-visual-box feat-visual-box--score">
                <span className="feat-score-number">88</span>
                <div className="feat-score-tags">
                  <span className="feat-score-rubric">STAR Structure: Strong</span>
                  <span className="feat-score-rubric">Technical Depth: High</span>
                </div>
              </div>
            </div>
            <div className="feat-card-content">
              <h3 className="feat-card-title">Rubric feedback that teaches</h3>
              <p className="feat-card-desc">
                Receive comprehensive feedback after every session. Discover exactly which answers landed, what lacked depth, and how to structure your responses.
              </p>
            </div>
          </article>

        </div>

        {/* Cohesive bottom highlights */}
        <div className="feat-footer-bar">
          <div className="feat-bar-item">
            <span className="feat-bar-check">✓</span>
            <span>Configurable session lengths (15 to 60 mins)</span>
          </div>
          <div className="feat-bar-divider" />
          <div className="feat-bar-item">
            <span className="feat-bar-check">✓</span>
            <span>Performance analytics &amp; score history</span>
          </div>
          <div className="feat-bar-divider" />
          <div className="feat-bar-item">
            <span className="feat-bar-check">✓</span>
            <span>Campus, Technical &amp; Leadership tracks</span>
          </div>
        </div>

      </div>
    </section>
  )
}
