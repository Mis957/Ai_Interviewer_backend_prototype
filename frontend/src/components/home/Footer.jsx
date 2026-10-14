import BrandWordmark from '../BrandWordmark'

const scrollTo = (id) => {
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' })
  } else if (id === 'top') {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const footerColumns = [
  {
    heading: 'Product',
    links: [
      { label: 'Core Features', id: 'features' },
      { label: 'How It Works', id: 'how' },
      { label: 'Interview Types', id: 'interview-prep' },
      { label: 'Pricing Plans', id: 'pricing' },
    ],
  },
  {
    heading: 'Experience',
    links: [
      { label: 'Vedanta Voice Engine', id: 'start' },
      { label: 'STAR Rubric Feedback', id: 'features' },
      { label: 'Resume Profiler', id: 'how' },
      { label: 'Frequently Asked Questions', id: 'faq' },
    ],
  },
  {
    heading: 'Interview Tracks',
    links: [
      { label: 'Campus Placement', id: 'interview-prep' },
      { label: 'Software Engineering', id: 'interview-prep' },
      { label: 'Product & Behavioral', id: 'interview-prep' },
      { label: 'Consulting & Case Studies', id: 'interview-prep' },
    ],
  },
]

export default function Footer() {
  const year = new Date().getFullYear()

  return (
    <footer className="site-footer" aria-label="Site footer">
      <div className="site-footer-inner shell">
        {/* Brand column */}
        <div className="site-footer-brand">
          <button
            type="button"
            className="site-footer-wordmark"
            onClick={() => scrollTo('top')}
            aria-label="Back to top"
          >
            <BrandWordmark swoopColor="#E86127" swoopHeight={11} swoopBottom={-6} />
          </button>
          <p className="site-footer-tagline">
            Voice-first AI interview rehearsals designed to help ambitious candidates speak with clarity, structure, and poise.
          </p>
          <div className="site-footer-status">
            <span className="site-footer-status-indicator" />
            <span>Systems operational & ready for rehearsal</span>
          </div>
        </div>

        {/* Link columns */}
        <nav className="site-footer-nav" aria-label="Footer navigation">
          {footerColumns.map((col) => (
            <div key={col.heading} className="site-footer-col">
              <p className="site-footer-col-heading">{col.heading}</p>
              <ul className="site-footer-list">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <button
                      type="button"
                      className="site-footer-link"
                      onClick={() => scrollTo(link.id)}
                    >
                      {link.label}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
      </div>

      {/* Bottom bar */}
      <div className="site-footer-bar">
        <div className="site-footer-bar-inner shell">
          <div className="site-footer-bar-left">
            <span className="site-footer-pt" aria-hidden="true">PS.</span>
            <p className="site-footer-copy">© {year} परिSamvad. Built for practice that matters.</p>
          </div>
          <div className="site-footer-bar-right">
            <button
              type="button"
              className="site-footer-top"
              onClick={() => scrollTo('top')}
              aria-label="Back to top"
            >
              Back to top ↑
            </button>
          </div>
        </div>
      </div>
    </footer>
  )
}
