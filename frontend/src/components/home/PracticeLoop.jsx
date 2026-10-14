import { useEffect, useRef } from 'react'
import HandwrittenHighlight from './HandwrittenHighlight'

export default function PracticeLoop() {
  const sectionRef = useRef(null)

  useEffect(() => {
    const el = sectionRef.current
    if (!el) return

    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReduced) {
      el.classList.add('revealed')
      return
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.classList.add('revealed')
          observer.unobserve(el)
        }
      },
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  return (
    <section className="experience-section" id="start" ref={sectionRef}>
      <div className="experience-orange-glow" aria-hidden="true" />
      <div className="shell experience-shell">
        <header className="experience-header">
          <div className="experience-eyebrow-wrapper">
            <HandwrittenHighlight color="#ffffff" swoopColor="#ffffff" size="34px">
              The परिSamvad Experience
            </HandwrittenHighlight>
          </div>
          <h2 className="experience-heading">
            A conversation.<br />Not a questionnaire.
          </h2>
          <p className="experience-sub">
            Vedanta, your AI interviewer, listens to your voice, follows up on your answers,
            and responds like a real interviewer would. No typing. No multiple choice. Just the
            conversation you need to practice.
          </p>
        </header>

        {/* Big handwritten logo typo display with hashtag — seamless background, no duplicate box */}
        <div className="experience-typo-stage">
          <div className="experience-typo-container">
            <div className="experience-brand-mark">
              <span className="experience-handwritten-logo">
                <span className="experience-deva-glyph">परि</span>Samvad
              </span>
              <svg
                className="experience-crisp-swoop"
                viewBox="0 0 280 24"
                fill="none"
                aria-hidden="true"
                preserveAspectRatio="none"
              >
                <path
                  d="M4 16 C 75 4, 185 4, 274 14"
                  stroke="#ffffff"
                  strokeWidth="3.2"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            
            <div className="experience-hashtag-row">
              <span className="experience-hashtag">#PracticeTheMomentThatMatters</span>
              <span className="experience-hashtag-dot">•</span>
              <span className="experience-hashtag">#SpeakWithClarity</span>
            </div>
          </div>
        </div>

      </div>
    </section>
  )
}
