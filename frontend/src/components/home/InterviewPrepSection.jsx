import useScrollReveal from './useScrollReveal'
import HandwrittenHighlight from './HandwrittenHighlight'

const interviewTypes = [
  {
    id: 'campus',
    label: 'Campus / Placement',
    desc: 'Practice for the rounds that get you through the gate—aptitude, GDs, HR, and technical panels.',
  },
  {
    id: 'technical',
    label: 'Technical & System Design',
    desc: 'Code walkthroughs, system architecture, data structures, and explaining the reasoning behind every design choice.',
  },
  {
    id: 'hr',
    label: 'HR & Behavioral',
    desc: 'Structured answers using the STAR method for leadership, conflict resolution, and behavioral questions that never go away.',
  },
  {
    id: 'managerial',
    label: 'Managerial & Product',
    desc: 'Cross-functional execution, product strategy, ownership, and high-stakes decision-making under ambiguous constraints.',
  },
  {
    id: 'admissions',
    label: 'Executive & Case Studies',
    desc: 'Consulting business cases, market entry frameworks, and post-grad admissions panels practiced until the narrative is tight.',
  },
]

export default function InterviewPrepSection() {
  const ref = useScrollReveal({ threshold: 0.08 })

  // 4 secondary cards (from index 1 to 4)
  const secondaryTypes = interviewTypes.slice(1, 5)

  return (
    <section className="prep-section" id="interview-prep" aria-labelledby="prep-heading" ref={ref}>
      <div className="shell">

        <header className="prep-header">
          <div className="prep-eyebrow-wrapper">
            <HandwrittenHighlight size="34px">
              Targeted round preparation
            </HandwrittenHighlight>
          </div>
          <h2 className="prep-heading" id="prep-heading">
            Every interview is different.<br />
            Your practice should be too.
          </h2>
        </header>

        <div className="prep-composition">

          {/* Primary large card */}
          <article className="prep-card prep-card--primary" data-type="campus">
            <div className="prep-card-content">
              <span className="prep-card-label">Campus / Placement</span>
              <h3 className="prep-card-title">
                Practice for the rounds that get you through the gate.
              </h3>
              <p className="prep-card-desc">
                Aptitude rounds, group discussions, HR panels, and technical interviews — Parisamvad covers the full placement cycle. Master foundational clarity before stepping into specialized rounds.
              </p>
            </div>
            <div className="prep-card-tag" aria-hidden="true">Most popular track</div>
          </article>

          {/* Secondary 2x2 grid (exactly 4 cards) */}
          <div className="prep-secondary-grid">
            {secondaryTypes.map((type) => (
              <article key={type.id} className="prep-card prep-card--secondary" data-type={type.id}>
                <span className="prep-card-label">{type.label}</span>
                <p className="prep-card-desc">{type.desc}</p>
                <span className="prep-card-arrow" aria-hidden="true">→</span>
              </article>
            ))}
          </div>

        </div>

      </div>
    </section>
  )
}
