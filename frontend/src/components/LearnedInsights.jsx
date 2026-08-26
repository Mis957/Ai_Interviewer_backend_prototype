import React, { useEffect, useState } from 'react';
import { fetchLearningAnalytics } from '../services/api';
import { Database, Brain, Sparkles, TrendingUp, CheckCircle, RefreshCw } from 'lucide-react';

export default function LearnedInsights() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = () => {
    setLoading(true);
    fetchLearningAnalytics()
      .then((data) => {
        setAnalytics(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', margin: '4rem auto', color: 'var(--text-muted)' }}>
        Fetching backend self-learning insights...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '3rem auto', padding: '0 1.5rem' }}>
      {/* Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2.25rem', fontWeight: '800', color: '#fff', marginBottom: '0.5rem' }}>
            Backend Self-Learning Dashboard
          </h1>
          <p style={{ color: 'var(--text-muted)' }}>
            The backend auto-curates high-performing LLM generated questions into the permanent Question Bank database.
          </p>
        </div>
        <button onClick={loadData} className="btn-secondary">
          <RefreshCw size={16} /> Refresh Analytics
        </button>
      </div>

      {/* Overview Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem' }}>
        <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Total Curated Questions</span>
          <h2 style={{ fontSize: '2.5rem', color: '#fff', margin: '0.3rem 0' }}>{analytics?.total_questions_in_bank || 0}</h2>
          <span style={{ fontSize: '0.8rem', color: 'var(--accent)' }}>Active in Database</span>
        </div>

        <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center', borderTop: '4px solid var(--purple)' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Auto-Promoted LLM Questions</span>
          <h2 style={{ fontSize: '2.5rem', color: 'var(--purple)', margin: '0.3rem 0' }}>{analytics?.auto_learned_questions_count || 0}</h2>
          <span style={{ fontSize: '0.8rem', color: 'var(--purple)' }}>Self-Learned by Engine</span>
        </div>

        <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center', borderTop: '4px solid var(--primary)' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Total Sessions Conducted</span>
          <h2 style={{ fontSize: '2.5rem', color: 'var(--primary-glow)', margin: '0.3rem 0' }}>{analytics?.total_sessions_conducted || 0}</h2>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Completed: {analytics?.completed_sessions || 0}</span>
        </div>
      </div>

      {/* Auto-Curated Questions Table / Cards */}
      <div className="glass-card" style={{ padding: '2rem', marginBottom: '2.5rem' }}>
        <h3 style={{ fontSize: '1.2rem', color: '#fff', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Sparkles size={20} color="var(--purple)" /> Auto-Curated Question Bank Expansion
        </h3>

        {(!analytics?.auto_curated_questions || analytics.auto_curated_questions.length === 0) ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            No LLM questions promoted yet. Complete an interview round with dynamic questions to see them automatically curated here!
          </p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {analytics.auto_curated_questions.map((q) => (
              <div key={q.id} style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-color)', padding: '1.25rem', borderRadius: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span className={`badge badge-${q.difficulty.toLowerCase()}`}>{q.difficulty}</span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Learned: {new Date(q.created_at).toLocaleDateString()}</span>
                </div>
                <div style={{ fontWeight: '600', color: '#fff', fontSize: '1.05rem', marginBottom: '0.3rem' }}>Track: {q.technology} • Topic: {q.topic}</div>
                <p style={{ color: 'var(--text-main)', fontSize: '0.95rem' }}>"{q.question}"</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
