import useScrollReveal from './useScrollReveal'
import HandwrittenHighlight from './HandwrittenHighlight'

const Arrow = () => (
  <svg viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2.5 8h10M8.5 3.5 13 8l-4.5 4.5" />
  </svg>
)

const plans = [
  {
    id: 'free',
    name: 'Free',
    price: '₹0',
    period: null,
    tagline: 'Get started, no commitment.',
    features: [
      'Limited practice sessions',
      'Basic interview setup',
      'Voice interview practice',
      'Basic session feedback',
    ],
    cta: 'Start practicing',
    ctaStyle: 'light',
    dominant: false,
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '₹299',
    period: '/month',
    tagline: 'For consistent, serious practice.',
    features: [
      'Unlimited practice sessions',
      'Resume + JD based interviews',
      'Detailed evaluation & scoring',
      'Session history & progress',
      'All interview types',
    ],
    cta: 'Get Pro',
    ctaStyle: 'dark',
    dominant: true,
  },
  {
    id: 'annual',
    name: 'Annual',
    price: '₹2,499',
    period: '/year',
    tagline: 'Pro, billed once a year.',
    savings: 'Save ₹1,089',
    features: [
      'Everything in Pro',
      'Priority support',
    ],
    cta: 'Get Annual',
    ctaStyle: 'light',
    dominant: false,
  },
]

export default function PricingSection() {
  const ref = useScrollReveal({ threshold: 0.1 })
  return (
    <section className="pricing-section" id="pricing" aria-labelledby="pricing-heading" ref={ref}>
      <div className="shell">

        <header className="pricing-header">
          <div className="pricing-eyebrow-wrapper">
            <HandwrittenHighlight size="34px">
              Transparent investment
            </HandwrittenHighlight>
          </div>
          <h2 className="pricing-heading" id="pricing-heading">
            Simple. No surprises.
          </h2>
          <p className="pricing-sub">
            Start free. Upgrade when the practice gets serious.
          </p>
        </header>

        <div className="pricing-grid">
          {plans.map((plan) => (
            <article
              key={plan.id}
              className={`pricing-card${plan.dominant ? ' pricing-card--dominant' : ''}`}
              data-plan={plan.id}
            >
              <div className="pricing-card-header">
                <span className="pricing-plan-name">{plan.name}</span>
                {plan.savings && (
                  <span className="pricing-savings-badge">{plan.savings}</span>
                )}
              </div>
              <div className="pricing-price-row">
                <span className="pricing-price">{plan.price}</span>
                {plan.period && (
                  <span className="pricing-period">{plan.period}</span>
                )}
              </div>
              <p className="pricing-tagline">{plan.tagline}</p>
              <ul className="pricing-features">
                {plan.features.map((feat) => (
                  <li key={feat} className="pricing-feature-item">
                    <span className="pricing-check" aria-hidden="true">✓</span>
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
              <div className="pricing-cta-wrap">
                <button
                  className={`pill ${plan.dominant ? 'dark' : 'light'} pricing-cta`}
                  onClick={() => document.getElementById('start')?.scrollIntoView({ behavior: 'smooth' })}
                >
                  <span>{plan.cta}</span>
                  <Arrow />
                </button>
              </div>
            </article>
          ))}
        </div>

      </div>
    </section>
  )
}
