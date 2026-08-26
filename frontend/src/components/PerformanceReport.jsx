import React from 'react';
import { Award, CheckCircle, XCircle, BookOpen, RotateCcw, ExternalLink, Sparkles } from 'lucide-react';

export default function PerformanceReport({ report, onRestart }) {
  if (!report) return null;

  return (
    <div style={{ maxWidth: '950px', margin: '3rem auto', padding: '0 1.5rem' }}>
      {/* Title Header */}
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <div style={{
          display: 'inline-flex',
          padding: '0.5rem 1rem',
          borderRadius: '20px',
          background: 'rgba(16, 185, 129, 0.15)',
          color: 'var(--accent)',
          fontSize: '0.85rem',
          fontWeight: '700',
          marginBottom: '1rem'
        }}>
          <Sparkles size={16} style={{ marginRight: '0.4rem' }} /> Interview Completed
        </div>
        <h1 style={{ fontSize: '2.5rem', fontWeight: '800', color: '#fff', marginBottom: '0.5rem' }}>
          Interview Performance Report
        </h1>
        <p style={{ color: 'var(--text-muted)' }}>Track: {report.technology} • Total Questions Answered: {report.questions_answered}</p>
      </div>

      {/* Score Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem' }}>
        <div className="glass-card" style={{ padding: '1.75rem', textAlign: 'center', borderTop: '4px solid var(--primary)' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Technical Proficiency</span>
          <div style={{ fontSize: '2.75rem', fontWeight: '800', color: '#fff', margin: '0.5rem 0' }}>
            {report.technical_score.toFixed(1)}<span style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}>/10</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.75rem', textAlign: 'center', borderTop: '4px solid var(--purple)' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Communication Score</span>
          <div style={{ fontSize: '2.75rem', fontWeight: '800', color: '#fff', margin: '0.5rem 0' }}>
            {report.communication_score.toFixed(1)}<span style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}>/10</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.75rem', textAlign: 'center', borderTop: '4px solid var(--accent)' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Confidence Rating</span>
          <div style={{ fontSize: '2.75rem', fontWeight: '800', color: '#fff', margin: '0.5rem 0' }}>
            {report.confidence_rating.toFixed(1)}<span style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}>/10</span>
          </div>
        </div>
      </div>

      {/* Synthesis Feedback */}
      <div className="glass-card" style={{ padding: '2rem', marginBottom: '2.5rem' }}>
        <h3 style={{ fontSize: '1.2rem', color: '#fff', marginBottom: '0.75rem' }}>Overall Evaluator Synthesis</h3>
        <p style={{ color: 'var(--text-main)', lineHeight: '1.6', fontSize: '1.05rem' }}>"{report.overall_feedback}"</p>
      </div>

      {/* Strong vs Weak Topics */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2.5rem' }}>
        <div className="glass-card" style={{ padding: '1.75rem' }}>
          <h4 style={{ color: 'var(--accent)', fontSize: '1.1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle size={20} /> Strong Topics
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {report.strong_topics?.map((topic, i) => (
              <div key={i} style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#fff', padding: '0.6rem 1rem', borderRadius: '8px', fontSize: '0.95rem' }}>
                ✓ {topic}
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '1.75rem' }}>
          <h4 style={{ color: '#EF4444', fontSize: '1.1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <XCircle size={20} /> Areas For Growth
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {report.weak_topics?.map((topic, i) => (
              <div key={i} style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#fff', padding: '0.6rem 1rem', borderRadius: '8px', fontSize: '0.95rem' }}>
                • {topic}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Personalized Learning Roadmap */}
      <div className="glass-card" style={{ padding: '2rem', marginBottom: '3rem' }}>
        <h3 style={{ fontSize: '1.3rem', color: '#fff', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <BookOpen size={22} color="var(--primary-glow)" /> Personalized Learning Roadmap
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {report.learning_roadmap?.map((item, idx) => (
            <div key={idx} style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-color)', padding: '1.25rem', borderRadius: '12px' }}>
              <div style={{ fontWeight: '700', color: 'var(--primary-glow)', fontSize: '1.05rem', marginBottom: '0.35rem' }}>
                Step {idx + 1}: {item.topic}
              </div>
              <p style={{ color: '#fff', fontSize: '0.95rem', marginBottom: '0.5rem' }}>{item.action_item}</p>
              {item.recommended_resource && (
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                  <ExternalLink size={14} /> Resource: {item.recommended_resource}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Restart Button */}
      <div style={{ textAlign: 'center' }}>
        <button onClick={onRestart} className="btn-primary" style={{ padding: '0.85rem 2.5rem', fontSize: '1.1rem' }}>
          <RotateCcw size={20} /> Start Another Practice Interview
        </button>
      </div>
    </div>
  );
}
