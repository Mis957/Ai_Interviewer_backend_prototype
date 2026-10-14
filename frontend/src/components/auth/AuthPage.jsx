import { useNavigate } from 'react-router-dom'
import AuthDots from './AuthDots'
import AuthForm from './AuthForm'
import BrandWordmark from '../BrandWordmark'

/* Wordmark with authentic swoop underline */
function AuthWordmark() {
  const navigate = useNavigate()
  return (
    <button
      className="auth-wordmark"
      onClick={() => navigate('/')}
      aria-label="Parisamvad — go to home"
    >
      <BrandWordmark swoopHeight={11} swoopBottom={-6} />
    </button>
  )
}

export default function AuthPage({ mode }) {
  const navigate = useNavigate()

  const switchMode = () =>
    navigate(mode === 'login' ? '/signup' : '/login', { replace: true })

  return (
    <div className="auth-page" data-mode={mode}>

      {/* Top nav — wordmark only */}
      <nav className="auth-nav" aria-label="Authentication navigation">
        <AuthWordmark />
      </nav>

      {/* Two-column body */}
      <div className="auth-shell">

        {/* ── LEFT — editorial brand side ─────────────────── */}
        <div className="auth-editorial" aria-label="Parisamvad brand statement">
          {/* Dots live behind editorial content */}
          <AuthDots />

          <span className="auth-editorial-eyebrow" aria-hidden="true">
            Speak with clarity.
          </span>

          <h1 className="auth-editorial-headline">
            Practice the<br />
            moment that<br />
            matters.
          </h1>

          <p className="auth-editorial-tagline">
            Interview readiness, practiced.
          </p>

          <div className="auth-handwritten-note" aria-hidden="true">
            <span>Every interview is a conversation. Start speaking.</span>
            <svg viewBox="0 0 160 22"><path d="M4 14C50 3 95 20 156 6" /></svg>
          </div>
        </div>

        {/* ── RIGHT — authentication form ──────────────────── */}
        <div className="auth-form-panel">
          <div
            className="auth-form-surface"
            role="main"
            aria-label={mode === 'login' ? 'Log in to Parisamvad' : 'Create a Parisamvad account'}
          >
            <AuthForm mode={mode} onSwitch={switchMode} />
          </div>
        </div>

      </div>
    </div>
  )
}
