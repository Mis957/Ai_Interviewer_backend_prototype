import useScrollReveal from './useScrollReveal'
import HandwrittenHighlight from './HandwrittenHighlight'

export default function StatementSection() {
  const ref = useScrollReveal({ threshold: 0.2 })
  return (
    <section className="statement-section" ref={ref}>
      <div className="shell statement-inner">
        <div className="statement-lead">
          <div className="statement-eyebrow-wrapper">
            <HandwrittenHighlight size="32px">
              The practice that actually prepares you
            </HandwrittenHighlight>
          </div>
          <h2 className="statement-heading">
            Not another chatbot.<br />
            A real rehearsal.
          </h2>
        </div>
        <div className="statement-body">
          <p>
            Parisamvad brings the full interview lifecycle into one focused place —
            your resume, your target role, a real voice conversation with Vedanta,
            clear feedback, and proof that you're getting better.
          </p>
          <div className="statement-accent" aria-hidden="true">
            <span className="statement-line" />
            <span className="statement-dot" />
          </div>
        </div>
      </div>
    </section>
  )
}
