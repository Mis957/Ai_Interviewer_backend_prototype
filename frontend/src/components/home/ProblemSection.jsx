import useScrollReveal from './useScrollReveal'
import HandwrittenHighlight from './HandwrittenHighlight'

const challenges = [
  {
    num: '01',
    title: 'No realistic practice',
    body: "Reading answers off a screen doesn't prepare you for the pressure of speaking clearly, thinking on your feet, and holding a real conversation.",
  },
  {
    num: '02',
    title: 'Generic question banks',
    body: "Most tools ask the same recycled questions regardless of your background, your role, or the kind of interview you're walking into.",
  },
  {
    num: '03',
    title: 'No meaningful feedback',
    body: "Practicing alone means no one tells you what worked, what didn't, or what to change. You repeat the same mistakes without knowing it.",
  },
]

export default function ProblemSection() {
  const ref = useScrollReveal({ threshold: 0.12 })
  return (
    <section className="problem-section" ref={ref}>
      <div className="shell">
        <header className="problem-header">
          <div className="problem-eyebrow-wrapper">
            <HandwrittenHighlight size="32px">
              The problem with prep today
            </HandwrittenHighlight>
          </div>
          <h2 className="problem-heading">
            Interview prep is<br />
            still broken.
          </h2>
        </header>
        <div className="problem-grid">
          {challenges.map((c) => (
            <article key={c.num} className="problem-card" data-num={c.num}>
              <span className="problem-num" aria-hidden="true">{c.num}</span>
              <h3 className="problem-title">{c.title}</h3>
              <p className="problem-body">{c.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
