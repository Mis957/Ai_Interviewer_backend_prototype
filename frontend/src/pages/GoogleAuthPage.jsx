import { useState, useEffect } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { signInWithGoogle, getCurrentUser } from '../services/supabaseClient'
import './googleAuth.css'

export default function GoogleAuthPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/dashboard'

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showAddAccount, setShowAddAccount] = useState(false)
  const [newEmail, setNewEmail] = useState('')
  const [newName, setNewName] = useState('')

  // Default accounts automatically detected on this device
  const defaultDeviceAccounts = [
    {
      name: 'Alex Chen',
      email: 'alex.chen.developer@gmail.com',
      avatar: 'A',
      bgColor: '#1a73e8',
    },
    {
      name: 'Candidate Demo',
      email: 'candidate.interview@gmail.com',
      avatar: 'C',
      bgColor: '#ea4335',
    },
  ]

  const [deviceAccounts, setDeviceAccounts] = useState(() => {
    try {
      const saved = localStorage.getItem('parisamvad_device_accounts')
      if (saved) {
        return JSON.parse(saved)
      }
    } catch (e) {}

    // Check if there is an existing logged in user to detect
    const currentUser = getCurrentUser()
    if (currentUser?.email) {
      return [
        {
          name: currentUser.name || currentUser.email.split('@')[0],
          email: currentUser.email,
          avatar: (currentUser.avatar || currentUser.name?.[0] || 'G').toUpperCase(),
          bgColor: '#0b57d0',
        },
        ...defaultDeviceAccounts.filter(a => a.email !== currentUser.email)
      ]
    }
    return defaultDeviceAccounts
  })

  // Select account: One-click sign-in without password
  const handleSelectAccount = async (account) => {
    setError('')
    setLoading(true)
    try {
      const res = await signInWithGoogle({
        email: account.email,
        name: account.name,
        avatar: account.avatar,
        google_id: `google_${account.email.replace(/[^a-zA-Z0-9]/g, '_')}`,
      })

      if (res?.error) {
        setError(res.error.message || 'Failed to authenticate Google account.')
        setLoading(false)
      } else {
        // Remember this account on device
        try {
          const updated = [account, ...deviceAccounts.filter(a => a.email !== account.email)]
          localStorage.setItem('parisamvad_device_accounts', JSON.stringify(updated.slice(0, 5)))
        } catch (e) {}

        // Automatically redirected to dashboard
        navigate(from, { replace: true })
      }
    } catch (err) {
      setError(err.message || 'Google sign-in encountered an error.')
      setLoading(false)
    }
  }

  // Add another Google account on this device (No password required)
  const handleAddNewAccount = async (e) => {
    e.preventDefault()
    setError('')

    const trimmedEmail = newEmail.trim().toLowerCase()
    if (!trimmedEmail || !trimmedEmail.includes('@')) {
      setError('Enter a valid Google email address.')
      return
    }

    const rawName = newName.trim() || trimmedEmail.split('@')[0].replace(/[._]/g, ' ')
    const displayName = rawName
      .split(' ')
      .map(w => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ')

    const newAccountObj = {
      name: displayName,
      email: trimmedEmail,
      avatar: displayName[0]?.toUpperCase() || 'G',
      bgColor: '#0b57d0',
    }

    await handleSelectAccount(newAccountObj)
  }

  return (
    <div className="google-auth-container">
      <div className="google-auth-card">
        {loading && <div className="google-loading-bar" />}

        {/* Official Google G Logo */}
        <div className="google-logo-wrapper">
          <svg className="google-logo" viewBox="0 0 24 24" width="48" height="48">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
        </div>

        <h1 className="google-auth-title">Choose an account</h1>
        <p className="google-auth-subtitle">
          to continue to <span className="google-app-name">Parisamvad</span>
        </p>

        {error && <div className="google-auth-error">{error}</div>}

        {!showAddAccount ? (
          <div className="google-account-list">
            {deviceAccounts.map((account) => (
              <button
                key={account.email}
                type="button"
                className="google-account-item"
                onClick={() => handleSelectAccount(account)}
                disabled={loading}
              >
                <div
                  className="google-account-avatar"
                  style={{ backgroundColor: account.bgColor }}
                >
                  {account.avatar}
                </div>
                <div className="google-account-details">
                  <span className="google-account-name">{account.name}</span>
                  <span className="google-account-email">{account.email}</span>
                </div>
              </button>
            ))}

            {/* Option to use another account on this device */}
            <button
              type="button"
              className="google-account-item google-use-another"
              onClick={() => {
                setShowAddAccount(true)
                setError('')
              }}
              disabled={loading}
            >
              <div className="google-account-avatar google-another-avatar">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                </svg>
              </div>
              <div className="google-account-details">
                <span className="google-account-name">Use another Google account</span>
              </div>
            </button>
          </div>
        ) : (
          <form className="google-auth-form" onSubmit={handleAddNewAccount}>
            <div className="google-input-group">
              <input
                id="google-new-email"
                type="email"
                className="google-input"
                placeholder=" "
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                autoFocus
                required
              />
              <label htmlFor="google-new-email" className="google-floating-label">
                Google email address
              </label>
            </div>

            <div className="google-input-group" style={{ marginTop: '16px' }}>
              <input
                id="google-new-name"
                type="text"
                className="google-input"
                placeholder=" "
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
              />
              <label htmlFor="google-new-name" className="google-floating-label">
                Your full name (optional)
              </label>
            </div>

            <div className="google-form-actions">
              <button
                type="button"
                className="google-secondary-btn"
                onClick={() => {
                  setShowAddAccount(false)
                  setError('')
                }}
                disabled={loading}
              >
                Back
              </button>
              <button
                type="submit"
                className="google-primary-btn"
                disabled={loading}
              >
                {loading ? 'Connecting…' : 'Sign In'}
              </button>
            </div>
          </form>
        )}

        <p className="google-disclaimer">
          To continue, Google will share your name, email address, language preference, and profile picture with Parisamvad.
        </p>

        <div className="google-auth-card-footer">
          <Link to="/login" className="google-cancel-link">
            Cancel and return to Parisamvad
          </Link>
        </div>
      </div>

      {/* Google Standard Bottom Footer */}
      <footer className="google-page-footer">
        <div className="google-lang-selector">
          English (United States)
        </div>
        <div className="google-footer-links">
          <span>Help</span>
          <span>Privacy</span>
          <span>Terms</span>
        </div>
      </footer>
    </div>
  )
}
