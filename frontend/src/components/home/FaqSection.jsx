import { useState } from 'react'
import useScrollReveal from './useScrollReveal'
import HandwrittenHighlight from './HandwrittenHighlight'

const faqs = [
  {
    q: 'How does Vedanta evaluate my answers?',
    a: 'Vedanta analyzes your verbal responses for structural clarity (such as the STAR method), technical depth, communication confidence, and pacing. After every session, you receive a rubric-based breakdown with specific strengths and areas for refinement.',
  },
  {
    q: 'Can I tailor the interview to my specific resume and role?',
    a: 'Yes. You can upload your PDF resume and specify your target job title, company tier, or round type. Parisamvad analyzes your real project experience to generate personalized, probing questions.',
  },
  {
    q: 'Do I need special hardware or downloadable software?',
    a: 'No downloads required. Parisamvad runs directly in any modern desktop or laptop browser (Chrome, Edge, Safari, Firefox). All you need is a working microphone.',
  },
  {
    q: 'Which interview rounds can I practice?',
    a: 'We support campus placement rounds, technical engineering deep-dives, behavioral & HR panels, product management scenarios, and consulting case discussions.',
  },
  {
    q: 'Can I start practicing for free?',
    a: 'Yes. The Free Starter tier includes 3 full voice interview sessions with AI feedback reports so you can experience realistic rehearsals before upgrading.',
  },
]

export default function FaqSection() {
  const ref = useScrollReveal({ threshold: 0.1 })
  const [openIndex, setOpenIndex] = useState(0)

  const toggle = (idx) => {
    setOpenIndex(openIndex === idx ? -1 : idx)
  }

  return (
    <section className="faq-section" id="faq" ref={ref} aria-labelledby="faq-heading">
      <div className="shell faq-inner">
        <header className="faq-header">
          <div className="faq-eyebrow-wrapper">
            <HandwrittenHighlight size="32px">
              Common questions
            </HandwrittenHighlight>
          </div>
          <h2 id="faq-heading" className="faq-heading">
            Everything you need<br />to know.
          </h2>
          <p className="faq-sub">
            Have questions about rehearsals, feedback rubrics, or getting started? We've got answers.
          </p>
        </header>

        <div className="faq-list" role="region" aria-label="Frequently Asked Questions">
          {faqs.map((item, idx) => {
            const isOpen = openIndex === idx
            return (
              <div
                key={item.q}
                className={`faq-item ${isOpen ? 'faq-item--open' : ''}`}
              >
                <button
                  type="button"
                  className="faq-question"
                  onClick={() => toggle(idx)}
                  aria-expanded={isOpen}
                  aria-controls={`faq-answer-${idx}`}
                >
                  <span className="faq-q-text">{item.q}</span>
                  <span className="faq-icon" aria-hidden="true">
                    <svg
                      viewBox="0 0 16 16"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.75"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d={isOpen ? 'M4 8h8' : 'M8 4v8M4 8h8'} />
                    </svg>
                  </span>
                </button>
                <div
                  id={`faq-answer-${idx}`}
                  className="faq-answer"
                  hidden={!isOpen}
                >
                  <p className="faq-answer-text">{item.a}</p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
