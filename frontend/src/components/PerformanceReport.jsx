import React from 'react';
import { Award, CheckCircle, XCircle, BookOpen, RotateCcw, ExternalLink, Sparkles, FileText, UserCheck, Code } from 'lucide-react';

export default function PerformanceReport({ report, resumeScreeningResult, onRestart }) {
  if (!report) return null;

  const techScore = Number(report?.technical_score ?? 0).toFixed(1);
  const commScore = Number(report?.communication_score ?? 0).toFixed(1);
  const confScore = Number(report?.confidence_rating ?? 0).toFixed(1);

  // Resume screening result details (when available from real POST /resume/screen API)
  const resumeScore = resumeScreeningResult?.overall_score != null 
    ? Number(resumeScreeningResult.overall_score).toFixed(0) 
    : null;

  return (
    <div style={{ maxWidth: '980px', margin: '2rem auto', padding: '0 1.5rem', fontFamily: "'DM Sans', Arial, sans-serif" }}>
      {/* Title Header */}
      <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.4rem',
          padding: '0.4rem 1.1rem',
          borderRadius: '20px',
          background: '#ecfdf5',
          color: '#047857',
          fontSize: '0.85rem',
          fontWeight: '700',
          marginBottom: '1rem',
          border: '1px solid #a7f3d0'
        }}>
          <Sparkles size={16} /> Parisamvad Evaluation Report
        </div>
        <h1 style={{ fontSize: '2.25rem', fontWeight: '800', color: '#0f172a', marginBottom: '0.5rem', letterSpacing: '-0.02em' }}>
          Interview Performance &amp; Evaluation
        </h1>
        <p style={{ color: '#64748b', fontSize: '1.05rem', margin: 0 }}>
          Technology: <strong style={{ color: '#0f172a' }}>{report.technology || 'General'}</strong> • Questions Answered: <strong style={{ color: '#0f172a' }}>{report.questions_answered ?? 0}</strong>
        </p>
      </div>

      {/* REAL RESUME EVALUATION SECTION (Rendered only when real resume screening data exists) */}
      {resumeScreeningResult && (
        <div style={{
          background: '#ffffff',
          borderRadius: '18px',
          padding: '2rem',
          marginBottom: '2rem',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)',
          borderLeft: '5px solid #3b82f6'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#0f172a', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FileText size={22} color="#2563eb" /> Resume Screening &amp; ATS Evaluation
              </h2>
              {resumeScreeningResult.candidate_name && (
                <span style={{ fontSize: '0.9rem', color: '#64748b', display: 'inline-flex', alignItems: 'center', gap: '0.3rem', marginTop: '0.25rem' }}>
                  <UserCheck size={14} /> Candidate: <strong>{resumeScreeningResult.candidate_name}</strong>
                </span>
              )}
            </div>

            {resumeScore !== null && (
              <div style={{ background: '#eff6ff', padding: '0.75rem 1.25rem', borderRadius: '12px', textAlign: 'center', border: '1px solid #bfdbfe' }}>
                <span style={{ fontSize: '0.75rem', color: '#1e40af', fontWeight: '700', textTransform: 'uppercase', display: 'block' }}>Resume Match Score</span>
                <span style={{ fontSize: '1.75rem', fontWeight: '800', color: '#1d4ed8' }}>{resumeScore}<span style={{ fontSize: '1rem', color: '#60a5fa' }}>/100</span></span>
              </div>
            )}
          </div>

          {/* Key Extracted Skills */}
          {Array.isArray(resumeScreeningResult.key_skills) && resumeScreeningResult.key_skills.length > 0 && (
            <div style={{ marginBottom: '1.25rem' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#475569', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: '0.5rem' }}>
                <Code size={14} /> Key Extracted Skills
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {resumeScreeningResult.key_skills.map((skill, idx) => (
                  <span key={idx} style={{ background: '#f1f5f9', color: '#334155', padding: '0.3rem 0.75rem', borderRadius: '8px', fontSize: '0.85rem', fontWeight: '600', border: '1px solid #e2e8f0' }}>
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Resume Strengths vs Weaknesses */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginTop: '1rem' }}>
            {Array.isArray(resumeScreeningResult.strengths) && resumeScreeningResult.strengths.length > 0 && (
              <div style={{ background: '#f0fdf4', padding: '1rem 1.25rem', borderRadius: '12px', border: '1px solid #bbf7d0' }}>
                <strong style={{ color: '#15803d', fontSize: '0.95rem', display: 'block', marginBottom: '0.5rem' }}>✓ Resume Highlights</strong>
                <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#166534', fontSize: '0.9rem', lineHeight: '1.5' }}>
                  {resumeScreeningResult.strengths.map((st, i) => (
                    <li key={i}>{st}</li>
                  ))}
                </ul>
              </div>
            )}

            {Array.isArray(resumeScreeningResult.weaknesses) && resumeScreeningResult.weaknesses.length > 0 && (
              <div style={{ background: '#fff1f2', padding: '1rem 1.25rem', borderRadius: '12px', border: '1px solid #fecdd3' }}>
                <strong style={{ color: '#be123c', fontSize: '0.95rem', display: 'block', marginBottom: '0.5rem' }}>• Resume Growth Areas</strong>
                <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#9f1239', fontSize: '0.9rem', lineHeight: '1.5' }}>
                  {resumeScreeningResult.weaknesses.map((wk, i) => (
                    <li key={i}>{wk}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* REAL INTERVIEW SCORES BREAKDOWN GRID */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        <div style={{
          background: '#ffffff',
          borderRadius: '16px',
          padding: '1.5rem',
          textAlign: 'center',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)',
          borderTop: '4px solid #4f46e5'
        }}>
          <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Technical Proficiency</span>
          <div style={{ fontSize: '2.5rem', fontWeight: '800', color: '#1e1b4b', margin: '0.4rem 0' }}>
            {techScore}<span style={{ fontSize: '1.1rem', color: '#94a3b8' }}>/10</span>
          </div>
        </div>

        <div style={{
          background: '#ffffff',
          borderRadius: '16px',
          padding: '1.5rem',
          textAlign: 'center',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)',
          borderTop: '4px solid #7c3aed'
        }}>
          <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Communication Score</span>
          <div style={{ fontSize: '2.5rem', fontWeight: '800', color: '#2e1065', margin: '0.4rem 0' }}>
            {commScore}<span style={{ fontSize: '1.1rem', color: '#94a3b8' }}>/10</span>
          </div>
        </div>

        <div style={{
          background: '#ffffff',
          borderRadius: '16px',
          padding: '1.5rem',
          textAlign: 'center',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)',
          borderTop: '4px solid #059669'
        }}>
          <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Confidence Rating</span>
          <div style={{ fontSize: '2.5rem', fontWeight: '800', color: '#064e3b', margin: '0.4rem 0' }}>
            {confScore}<span style={{ fontSize: '1.1rem', color: '#94a3b8' }}>/10</span>
          </div>
        </div>
      </div>

      {/* OVERALL EVALUATOR SYNTHESIS */}
      {report?.overall_feedback && (
        <div style={{
          background: '#ffffff',
          borderRadius: '16px',
          padding: '1.75rem',
          marginBottom: '2rem',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)'
        }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: '700', color: '#0f172a', marginBottom: '0.75rem' }}>
            Overall Evaluator Synthesis
          </h3>
          <p style={{ color: '#334155', lineHeight: '1.65', fontSize: '1.05rem', margin: 0, fontStyle: 'italic' }}>
            &quot;{report.overall_feedback}&quot;
          </p>
        </div>
      )}

      {/* STRONG VS WEAK TOPICS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        <div style={{
          background: '#ffffff',
          borderRadius: '16px',
          padding: '1.5rem',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)'
        }}>
          <h4 style={{ color: '#059669', fontSize: '1.05rem', fontWeight: '700', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.4rem', margin: '0 0 1rem 0' }}>
            <CheckCircle size={18} /> Strong Topics
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {Array.isArray(report?.strong_topics) && report.strong_topics.length > 0 ? (
              report.strong_topics.map((topic, i) => (
                <div key={i} style={{ background: '#f0fdf4', color: '#166534', padding: '0.6rem 0.9rem', borderRadius: '8px', fontSize: '0.9rem', fontWeight: '600', border: '1px solid #dcfce7' }}>
                  ✓ {topic}
                </div>
              ))
            ) : (
              <p style={{ color: '#94a3b8', fontSize: '0.9rem', margin: 0 }}>No specific strong topics highlighted.</p>
            )}
          </div>
        </div>

        <div style={{
          background: '#ffffff',
          borderRadius: '16px',
          padding: '1.5rem',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)'
        }}>
          <h4 style={{ color: '#dc2626', fontSize: '1.05rem', fontWeight: '700', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.4rem', margin: '0 0 1rem 0' }}>
            <XCircle size={18} /> Areas For Growth
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {Array.isArray(report?.weak_topics) && report.weak_topics.length > 0 ? (
              report.weak_topics.map((topic, i) => (
                <div key={i} style={{ background: '#fff1f2', color: '#9f1239', padding: '0.6rem 0.9rem', borderRadius: '8px', fontSize: '0.9rem', fontWeight: '600', border: '1px solid #ffe4e6' }}>
                  • {topic}
                </div>
              ))
            ) : (
              <p style={{ color: '#94a3b8', fontSize: '0.9rem', margin: 0 }}>No critical growth areas highlighted.</p>
            )}
          </div>
        </div>
      </div>

      {/* DETAILED QUESTION-BY-QUESTION EVALUATION */}
      {Array.isArray(report?.detailed_history) && report.detailed_history.length > 0 && (
        <div style={{
          background: '#ffffff',
          borderRadius: '16px',
          padding: '1.75rem',
          marginBottom: '2rem',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)'
        }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: '700', color: '#0f172a', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem', margin: '0 0 1.25rem 0' }}>
            <Award size={20} color="#4f46e5" /> Detailed Question-by-Question Evaluation
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {report.detailed_history.map((item, idx) => (
              <div key={idx} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '1.25rem', borderRadius: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span style={{ fontWeight: '700', color: '#4338ca', fontSize: '0.95rem' }}>
                    Question {idx + 1}
                  </span>
                  <span style={{ background: '#e0e7ff', color: '#3730a3', padding: '0.25rem 0.75rem', borderRadius: '12px', fontSize: '0.85rem', fontWeight: '700' }}>
                    Score: {Number(item.score ?? 0).toFixed(1)}/10
                  </span>
                </div>
                <p style={{ color: '#0f172a', fontWeight: '700', fontSize: '0.95rem', marginBottom: '0.5rem', margin: '0 0 0.5rem 0' }}>
                  Q: {item.question}
                </p>
                {item.candidate_answer && (
                  <p style={{ color: '#475569', fontSize: '0.9rem', marginBottom: '0.5rem', fontStyle: 'italic', margin: '0 0 0.5rem 0' }}>
                    Your Answer: &quot;{item.candidate_answer}&quot;
                  </p>
                )}
                {item.feedback && (
                  <p style={{ color: '#334155', fontSize: '0.9rem', marginTop: '0.5rem', margin: '0.5rem 0 0 0' }}>
                    <strong style={{ color: '#0f172a' }}>Feedback:</strong> {item.feedback}
                  </p>
                )}
                {Array.isArray(item.missing_topics) && item.missing_topics.length > 0 && (
                  <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#dc2626' }}>
                    <strong>Missing Topics:</strong> {item.missing_topics.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PERSONALIZED LEARNING ROADMAP */}
      {Array.isArray(report?.learning_roadmap) && report.learning_roadmap.length > 0 && (
        <div style={{
          background: '#ffffff',
          borderRadius: '16px',
          padding: '1.75rem',
          marginBottom: '2.5rem',
          border: '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.04)'
        }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: '700', color: '#0f172a', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem', margin: '0 0 1.25rem 0' }}>
            <BookOpen size={20} color="#7c3aed" /> Personalized Learning Roadmap
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {report.learning_roadmap.map((item, idx) => (
              <div key={idx} style={{ background: '#faf5ff', border: '1px solid #f3e8ff', padding: '1.25rem', borderRadius: '12px' }}>
                <div style={{ fontWeight: '700', color: '#6b21a8', fontSize: '1rem', marginBottom: '0.35rem' }}>
                  Step {idx + 1}: {item.topic}
                </div>
                <p style={{ color: '#334155', fontSize: '0.95rem', margin: '0 0 0.5rem 0' }}>{item.action_item}</p>
                {item.recommended_resource && (
                  <span style={{ fontSize: '0.85rem', color: '#6b21a8', display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontWeight: '600' }}>
                    <ExternalLink size={14} /> Resource: {item.recommended_resource}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* RESTART BUTTON */}
      <div style={{ textAlign: 'center' }}>
        <button onClick={onRestart} className="btn-primary" style={{
          padding: '0.85rem 2.5rem',
          fontSize: '1.05rem',
          fontWeight: '700',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
          color: '#ffffff',
          border: 'none',
          cursor: 'pointer',
          boxShadow: '0 4px 14px rgba(79, 70, 229, 0.3)',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <RotateCcw size={18} /> Start Another Practice Interview
        </button>
      </div>
    </div>
  );
}


