import { useEffect, useRef } from 'react'
import HandwrittenHighlight from './HandwrittenHighlight'

const Arrow = () => (
  <svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2.5 8h10M8.5 3.5 13 8l-4.5 4.5" />
  </svg>
)

const steps = [
  {
    num: '01',
    phase: 'Prepare',
    title: 'Build your context.',
    body: 'Upload your resume. Paste the job description. Choose the interview type. Parisamvad knows what to ask before you even begin.',
  },
  {
    num: '02',
    phase: 'Practice',
    title: 'Have the conversation.',
    body: 'Speak naturally. Parisamvad listens, responds, and follows up—just like a real interviewer would. No typing. No scripts.',
  },
  {
    num: '03',
    phase: 'Evaluate',
    title: 'Understand your performance.',
    body: 'Every session ends with a clear evaluation—clarity, depth, structure. You see exactly where you landed and why.',
  },
  {
    num: '04',
    phase: 'Improve',
    title: 'Practice what needs work.',
    body: 'Use the feedback to refine your next answer. Then practice again. The loop is the whole point.',
  },
]

export default function HowItWorksSection() {
  const gridRef = useRef(null)

  useEffect(() => {
    const grid = gridRef.current
    if (!grid) return

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReduced) {
      grid.querySelectorAll('.hiw-step').forEach(el => el.classList.add('revealed'))
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed')
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.2, rootMargin: '0px 0px -40px 0px' }
    )

    grid.querySelectorAll('.hiw-step').forEach(el => observer.observe(el))
    return () => observer.disconnect()
  }, [])

  return (
    <section className="hiw-section" id="how" aria-labelledby="hiw-heading">
      <div className="shell">

        <header className="hiw-header">
          <div className="hiw-eyebrow-wrapper">
            <HandwrittenHighlight size="34px">
              Simple 4-step loop
            </HandwrittenHighlight>
          </div>
          <h2 className="hiw-heading" id="hiw-heading">
            Four steps.<br />One practice loop.
          </h2>
        </header>

        <div className="hiw-grid" ref={gridRef}>
          {steps.map((step, i) => (
            <article
              key={step.num}
              className="hiw-step"
              data-step={step.num}
              data-phase={step.phase.toLowerCase()}
              style={{ '--stagger': i }}
            >
              <div className="hiw-step-num" aria-hidden="true">{step.num}</div>
              <div className="hiw-step-phase">{step.phase}</div>
              <h3 className="hiw-step-title">{step.title}</h3>
              <p className="hiw-step-body">{step.body}</p>
              <span className="hiw-step-connector" aria-hidden="true" />
            </article>
          ))}
        </div>

        <footer className="hiw-coda" aria-label="Practice loop summary">
          <p className="hiw-coda-line" data-coda="prepare">Practice.</p>
          <p className="hiw-coda-line" data-coda="improve">Improve.</p>
          <p className="hiw-coda-line" data-coda="repeat">Repeat.</p>
          <div className="hiw-coda-cta">
            <button
              className="pill dark"
              onClick={() => document.getElementById('start')?.scrollIntoView({ behavior: 'smooth' })}
            >
              Start practicing <Arrow />
            </button>
          </div>
        </footer>

      </div>
    </section>
  )
}
