import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import '../dashboard.css'
import '../laptop.css'
import Sidebar from '../components/Sidebar'
import { getStoredUser, currentMockUser } from '../data/mockData'
import { fetchLearningAnalytics } from '../services/api'

const Icon = ({ name, size = 20 }) => {
  const paths = {
    bolt: <path d="m13 2-9 12h7l-1 8 9-12h-7z"/>,
    history: <><path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5M12 7v5l3 2"/></>,
    file: <><path d="M6 2h8l4 4v16H6z"/><path d="M14 2v5h5"/></>,
    chart: <path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>,
    award: <><circle cx="12" cy="8" r="7"/><path d="M8.21 13.89 7 23l5-3 5 3-1.21-9.11"/></>,
    user: <><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></>,
    arrowRight: <path d="M5 12h14M12 5l7 7-7 7"/>,
    sparkles: <path d="m12 3 1.912 5.813a2 2 0 0 0 1.275 1.275L21 12l-5.813 1.912a2 2 0 0 0-1.275 1.275L12 21l-1.912-5.813a2 2 0 0 0-1.275-1.275L3 12l5.813-1.912a2 2 0 0 0 1.275-1.275L12 3z"/>
  }
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {paths[name]}
    </svg>
  )
}

function Swoop(){ return <svg className="swoop" viewBox="0 0 80 50" aria-hidden="true"><path d="M7 42C28 10 42 13 55 5M27 45c19-5 33-3 48 0"/></svg> }

export default function Overview() {
  const navigate = useNavigate()
  const [user, setUser] = useState(() => getStoredUser() || currentMockUser)
  const [analytics, setAnalytics] = useState(null)
  const [loadingAnalytics, setLoadingAnalytics] = useState(true)
  const [analyticsError, setAnalyticsError] = useState(null)

  useEffect(() => {
    const syncUser = () => {
      setUser(getStoredUser() || currentMockUser)
    }
    window.addEventListener('preptalk_user_updated', syncUser)
    return () => window.removeEventListener('preptalk_user_updated', syncUser)
  }, [])

  useEffect(() => {
    async function loadAnalytics() {
      try {
        setLoadingAnalytics(true)
        const data = await fetchLearningAnalytics()
        setAnalytics(data)
        setAnalyticsError(null)
      } catch (err) {
        console.error('Failed to load learning analytics:', err)
        setAnalyticsError('Unable to load learning analytics.')
      } finally {
        setLoadingAnalytics(false)
      }
    }
    loadAnalytics()
  }, [])

  const safeUser = user || currentMockUser

  return (
    <div className="dashboard-shell">
      <Sidebar active="Overview" />
      <main className="dashboard-main">
        <div className="dashboard-content">
          <header className="page-heading">
            <p>DASHBOARD OVERVIEW</p>
            <h1>Welcome, {safeUser.name || 'Candidate'} <Swoop/></h1>
            <span>Ready for your next mock interview? Track your progress and jump right back into practice.</span>
          </header>

          {/* Quick Launch Banner */}
          <div
            className="setup-card"
            style={{
              background: 'linear-gradient(135deg, #090a12, #181926)',
              color: '#ffffff',
              padding: '32px 36px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderRadius: '22px',
              marginBottom: '28px',
              boxShadow: '0 16px 40px rgba(9, 10, 18, 0.25)'
            }}
          >
            <div>
              <span className="topic-tag" style={{ background: '#2a2b3d', color: '#a78bfa', fontSize: '12px', padding: '4px 12px' }}>
                AI VOICE INTERVIEW READY
              </span>
              <h2 style={{ font: '600 32px/1.1 "Bodoni Moda", Georgia, serif', margin: '12px 0 6px', color: '#ffffff' }}>
                Start a New AI Practice Session
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '15px', margin: 0, maxWidth: '480px' }}>
                Targeting <strong>{safeUser.role || 'Senior Software Engineer'}</strong>. Upload your latest resume or set up focus topics to generate tailored interview questions.
              </p>
            </div>
            <button
              className="black-button"
              style={{ background: '#ffffff', color: '#090a12', fontSize: '15px', height: '52px', padding: '0 28px' }}
              onClick={() => navigate('/interview/new')}
            >
              <Icon name="bolt" size={20} />
              Start Interview
            </button>
          </div>

          {/* Real Backend Key Metrics Row (from GET /analytics/learning) */}
          <div className="history-stats-row">
            <div className="stat-card">
              <span className="stat-card-icon"><Icon name="history" size={24} /></span>
              <div>
                <b>{analytics ? `${analytics.completed_sessions} / ${analytics.total_sessions_conducted}` : (loadingAnalytics ? '...' : '0')}</b>
                <small>Completed / Total Sessions</small>
              </div>
            </div>

            <div className="stat-card">
              <span className="stat-card-icon"><Icon name="award" size={24} /></span>
              <div>
                <b>{analytics ? analytics.total_questions_in_bank : (loadingAnalytics ? '...' : '0')}</b>
                <small>Question Bank Size</small>
              </div>
            </div>

            <div className="stat-card">
              <span className="stat-card-icon"><Icon name="sparkles" size={24} /></span>
              <div>
                <b>{analytics ? analytics.auto_learned_questions_count : (loadingAnalytics ? '...' : '0')}</b>
                <small>AI Auto-Curated Questions</small>
              </div>
            </div>

            <div className="stat-card">
              <span className="stat-card-icon"><Icon name="user" size={24} /></span>
              <div>
                <b style={{ fontSize: '18px', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', textOverflow: 'ellipsis', wordBreak: 'break-word', lineHeight: 1.2 }}>{safeUser.role || 'Software Eng'}</b>
                <small>Active Target Role</small>
              </div>
            </div>
          </div>

          {/* Real Learning Analytics & Topic Performance */}
          <div style={{ marginTop: '32px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ font: '600 26px "Bodoni Moda", Georgia, serif', margin: 0, color: '#0f172a' }}>
                AI Learning Insights &amp; Topic Analytics
              </h2>
              <span style={{ fontSize: '13px', color: '#64748b' }}>Driven by backend self-learning engine</span>
            </div>

            {loadingAnalytics ? (
              <p style={{ color: '#64748b', fontSize: '14px' }}>Loading real backend learning analytics…</p>
            ) : analyticsError ? (
              <p style={{ color: '#ef4444', fontSize: '14px' }}>{analyticsError}</p>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
                {/* Topic Analytics Card */}
                <div style={{ background: '#ffffff', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '16px', padding: '20px', boxShadow: '0 4px 16px rgba(0,0,0,0.03)' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#0f172a', marginBottom: '14px' }}>
                    Topic Performance Averages
                  </h3>
                  {Array.isArray(analytics?.topic_analytics) && analytics.topic_analytics.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {analytics.topic_analytics.map((t, idx) => (
                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f8fafc', padding: '10px 14px', borderRadius: '10px' }}>
                          <div>
                            <strong style={{ color: '#0f172a', fontSize: '14px', display: 'block' }}>{t.topic}</strong>
                            <small style={{ color: '#64748b', fontSize: '12px' }}>{t.total_attempts} attempts</small>
                          </div>
                          <span style={{ background: '#e0e7ff', color: '#3730a3', padding: '4px 10px', borderRadius: '12px', fontSize: '13px', fontWeight: '700' }}>
                            {t.average_score} / 10
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0 }}>No topic scores recorded yet. Complete interviews to view insights.</p>
                  )}
                </div>

                {/* Auto Curated Questions Card */}
                <div style={{ background: '#ffffff', border: '1px solid rgba(0,0,0,0.08)', borderRadius: '16px', padding: '20px', boxShadow: '0 4px 16px rgba(0,0,0,0.03)' }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#0f172a', marginBottom: '14px' }}>
                    Auto-Promoted Question Bank
                  </h3>
                  {Array.isArray(analytics?.auto_curated_questions) && analytics.auto_curated_questions.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      {analytics.auto_curated_questions.map((q, idx) => (
                        <div key={idx} style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', padding: '10px 14px', borderRadius: '10px' }}>
                          <span style={{ fontSize: '11px', color: '#15803d', fontWeight: '700', textTransform: 'uppercase' }}>{q.technology} • {q.topic}</span>
                          <p style={{ color: '#166534', fontSize: '13px', margin: '4px 0 0 0', fontWeight: '600' }}>{q.question}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p style={{ color: '#94a3b8', fontSize: '13px', margin: 0 }}>High-scoring generated questions (score &ge; 5.0) are automatically promoted here.</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

