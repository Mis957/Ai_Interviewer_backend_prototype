import axios from 'axios'
import { createClient } from '@supabase/supabase-js'

// Base URLs
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const CLOUD_URL = import.meta.env.VITE_SUPABASE_URL || 'https://zygzvqtofseyyijqduke.supabase.co'
const CLOUD_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

const OFFLINE_URL = import.meta.env.VITE_SUPABASE_OFFLINE_URL || 'http://127.0.0.1:54321'
const OFFLINE_ANON_KEY = import.meta.env.VITE_SUPABASE_OFFLINE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJpYXQiOjE2NDk4Mjg0MDAsImV4cCI6MTk2NTQwNDQwMH0.Pql0cW9b_local_dummy_key'

// Initialize Cloud and Offline Supabase Clients
export const cloudClient = CLOUD_URL
  ? createClient(CLOUD_URL, CLOUD_ANON_KEY || OFFLINE_ANON_KEY, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
        storageKey: 'preptalk_supabase_cloud_auth',
      },
    })
  : null

export const offlineClient = OFFLINE_URL
  ? createClient(OFFLINE_URL, OFFLINE_ANON_KEY, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
        storageKey: 'preptalk_supabase_offline_auth',
      },
    })
  : null

/**
 * Automatically determine internet connectivity
 */
export function isOnline() {
  return typeof navigator !== 'undefined' ? navigator.onLine : true
}

/**
 * Get active client automatically based on internet connection
 */
export function getActiveClient() {
  if (isOnline() && CLOUD_ANON_KEY && cloudClient) {
    return cloudClient
  }
  return offlineClient || cloudClient
}

export const supabase = getActiveClient()

/**
 * Format user into standard candidate format
 */
export function formatPrepTalkUser(rawUser, fallbackName = '') {
  if (!rawUser) return null
  const meta = rawUser.user_metadata || {}
  const name = rawUser.name || meta.name || meta.full_name || meta.display_name || fallbackName || rawUser.email?.split('@')[0] || 'Candidate'
  const email = rawUser.email || ''
  const avatar = rawUser.avatar || (name ? name.trim()[0] : 'C').toUpperCase()
  const role = rawUser.role || meta.role || 'Software Engineer'

  return {
    id: rawUser.id,
    name,
    email,
    avatar,
    role,
    auth_provider: rawUser.auth_provider || 'email',
  }
}

/**
 * Persist user into localStorage and notify UI components
 */
export function persistUser(user, token = null) {
  if (!user) {
    localStorage.removeItem('preptalk_user')
    localStorage.removeItem('preptalk_token')
  } else {
    localStorage.setItem('preptalk_user', JSON.stringify(user))
    if (token) {
      localStorage.setItem('preptalk_token', token)
    }
  }
  window.dispatchEvent(new Event('preptalk_user_updated'))
}

/**
 * Sign up: creates user in the database and generates session
 */
export async function signUpUser({ name, email, password }) {
  const trimmedEmail = email.trim().toLowerCase()
  const trimmedName = name.trim()

  // 1. Primary: Save directly to the database via FastAPI /auth/signup
  try {
    const res = await axios.post(`${API_BASE_URL}/auth/signup`, {
      name: trimmedName,
      email: trimmedEmail,
      password,
    })

    const { user, access_token } = res.data
    const formatted = formatPrepTalkUser(user, trimmedName)
    persistUser(formatted, access_token)

    // Optional background sync with Supabase Cloud
    if (isOnline() && CLOUD_ANON_KEY && cloudClient) {
      cloudClient.auth.signUp({
        email: trimmedEmail,
        password,
        options: { data: { name: trimmedName } },
      }).catch(() => {})
    }

    return { data: { user: formatted, session: { access_token } }, error: null }
  } catch (err) {
    // If backend returns a business error (e.g. email exists), return it
    if (err.response?.data?.detail) {
      return { data: null, error: { message: err.response.data.detail } }
    }

    // If backend server is unreachable (offline mode), attempt Supabase client directly
    const client = getActiveClient()
    if (client) {
      try {
        const { data, error } = await client.auth.signUp({
          email: trimmedEmail,
          password,
          options: { data: { name: trimmedName } },
        })
        if (!error && data?.user) {
          const formatted = formatPrepTalkUser(data.user, trimmedName)
          persistUser(formatted, data.session?.access_token)
          return { data: { user: formatted, session: data.session }, error: null }
        }
        if (error) return { data: null, error }
      } catch (sbErr) {
        // Continue to fallback
      }
    }

    return { data: null, error: { message: err.message || 'Could not complete registration.' } }
  }
}

/**
 * Sign in: checks credentials against the database and establishes session
 */
export async function signInUser({ email, password }) {
  const trimmedEmail = email.trim().toLowerCase()

  // 1. Primary: Verify credentials against the database via FastAPI /auth/login
  try {
    const res = await axios.post(`${API_BASE_URL}/auth/login`, {
      email: trimmedEmail,
      password,
    })

    const { user, access_token } = res.data
    const formatted = formatPrepTalkUser(user)
    persistUser(formatted, access_token)

    // Optional background session sync with Supabase Cloud
    if (isOnline() && CLOUD_ANON_KEY && cloudClient) {
      cloudClient.auth.signInWithPassword({
        email: trimmedEmail,
        password,
      }).catch(() => {})
    }

    return { data: { user: formatted, session: { access_token } }, error: null }
  } catch (err) {
    if (err.response?.data?.detail) {
      return { data: null, error: { message: err.response.data.detail } }
    }

    // If backend is unreachable, try Supabase client
    const client = getActiveClient()
    if (client) {
      try {
        const { data, error } = await client.auth.signInWithPassword({
          email: trimmedEmail,
          password,
        })
        if (!error && data?.user) {
          const formatted = formatPrepTalkUser(data.user)
          persistUser(formatted, data.session?.access_token)
          return { data: { user: formatted, session: data.session }, error: null }
        }
        if (error) return { data: null, error }
      } catch (sbErr) {
        // Continue
      }
    }

    return { data: null, error: { message: 'Invalid email or password.' } }
  }
}

/**
 * Sign in with Google: records or updates user in database with auth_provider='google'
 */
export async function signInWithGoogle(customProfile = null) {
  // If specific profile is provided:
  if (customProfile?.email) {
    try {
      const res = await axios.post(`${API_BASE_URL}/auth/google`, {
        email: customProfile.email.trim().toLowerCase(),
        name: customProfile.name || customProfile.email.split('@')[0],
        avatar: customProfile.avatar,
        google_id: customProfile.google_id,
      })
      const { user, access_token } = res.data
      const formatted = formatPrepTalkUser(user)
      persistUser(formatted, access_token)
      return { data: { user: formatted, session: { access_token } }, error: null }
    } catch (err) {
      return { data: null, error: { message: err.response?.data?.detail || 'Google sign-in failed.' } }
    }
  }

  // If online with Supabase cloud credentials, attempt OAuth redirect to Google
  if (isOnline() && CLOUD_ANON_KEY && cloudClient) {
    try {
      const { data, error } = await cloudClient.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/dashboard`,
        },
      })
      if (!error && data?.url) {
        window.location.href = data.url
        return { data, error: null, redirected: true }
      }
    } catch (e) {
      console.warn('[Supabase Google] OAuth redirect notice:', e)
    }
  }

  // Redirect to the authentic Google sign-in page
  if (typeof window !== 'undefined') {
    window.location.href = '/auth/google'
    return { data: null, error: null, redirected: true }
  }

  return { data: null, error: null }
}

/**
 * Sign out user
 */
export async function signOutUser() {
  try {
    if (cloudClient) await cloudClient.auth.signOut().catch(() => {})
    if (offlineClient) await offlineClient.auth.signOut().catch(() => {})
  } catch (err) {
    console.warn('[Supabase Auth] Sign out error:', err)
  } finally {
    persistUser(null)
  }
}

/**
 * Password recovery
 */
export async function resetPasswordForEmail(email) {
  const client = getActiveClient()
  if (!client || !isOnline()) {
    return { error: null, message: 'Password recovery request noted.' }
  }
  return await client.auth.resetPasswordForEmail(email.trim().toLowerCase(), {
    redirectTo: `${window.location.origin}/settings`,
  })
}

/**
 * Read current stored candidate
 */
export function getCurrentUser() {
  try {
    const raw = localStorage.getItem('preptalk_user')
    if (raw && raw !== 'null' && raw !== 'undefined') {
      return JSON.parse(raw)
    }
  } catch (e) {
    console.error('[SupabaseClient] Error reading stored user:', e)
  }
  return null
}

/**
 * Get active token for API requests
 */
export async function getAuthToken() {
  const localToken = localStorage.getItem('preptalk_token')
  if (localToken) return localToken

  const client = getActiveClient()
  if (!client) return null
  try {
    const { data } = await client.auth.getSession()
    return data?.session?.access_token || null
  } catch (e) {
    return null
  }
}

/**
 * Listen for auth state changes and sync with database
 */
export function subscribeToAuthChanges(callback) {
  const unsubs = []

  const setupListener = (client) => {
    if (!client) return
    const { data: { subscription } } = client.auth.onAuthStateChange(async (event, session) => {
      if (session?.user) {
        // Sync OAuth / Supabase user to PostgreSQL database
        const meta = session.user.user_metadata || {}
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/google`, {
            email: session.user.email,
            name: meta.full_name || meta.name || session.user.email.split('@')[0],
            avatar: meta.avatar_url,
            google_id: session.user.id,
          })
          const formatted = formatPrepTalkUser(res.data.user)
          persistUser(formatted, res.data.access_token)
          if (callback) callback(event, formatted, session)
          return
        } catch (e) {
          // If backend sync fails, format directly
          const user = formatPrepTalkUser(session.user)
          persistUser(user, session.access_token)
          if (callback) callback(event, user, session)
        }
      } else if (event === 'SIGNED_OUT') {
        persistUser(null)
        if (callback) callback(event, null, null)
      }
    })
    unsubs.push(() => subscription?.unsubscribe())
  }

  setupListener(cloudClient)
  setupListener(offlineClient)

  return () => {
    unsubs.forEach(unsub => unsub())
  }
}
