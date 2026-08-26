import React from 'react';
import { Award, ArrowUpRight, ArrowDownRight, Minus, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react';

export default function EvaluationModal({ evaluation, onNextQuestion, isCompleted }) {
  if (!evaluation) return null;

  const getDifficultyShiftIcon = () => {
    if (evaluation.next_difficulty === 'Hard' && evaluation.current_difficulty !== 'Hard') {
      return <span style={{ color: 'var(--accent)', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}><ArrowUpRight size={18} /> Difficulty Upgraded to Hard</span>;
    }
    if (evaluation.next_difficulty === 'Easy' && evaluation.current_difficulty !== 'Easy') {
      return <span style={{ color: '#EF4444', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}><ArrowDownRight size={18} /> Difficulty Reduced to Easy</span>;
    }
    return <span style={{ color: 'var(--medium-color)', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}><Minus size={18} /> Difficulty Maintained at {evaluation.next_difficulty}</span>;
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1.5rem'
    }}>
      <div className="glass-card" style={{ maxWidth: '600px', width: '100%', padding: '2rem5', background: 'rgba(15, 23, 42, 0.95)', border: '1px solid var(--primary-glow)' }}>
        
        {/* Header Score Badge */}
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div style={{
            width: '80px',
            height: '80px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--primary) 0%, var(--purple) 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem',
            fontSize: '1.75rem',
            fontWeight: '800',
            color: '#fff',
            boxShadow: '0 0 25px rgba(99, 102, 241, 0.5)'
          }}>
            {evaluation.score.toFixed(1)}
          </div>
          <h2 style={{ fontSize: '1.5rem', color: '#fff', marginBottom: '0.25rem' }}>Answer Evaluation Result</h2>
          <div style={{ fontSize: '0.9rem', fontWeight: '500' }}>{getDifficultyShiftIcon()}</div>
        </div>

        {/* Feedback text */}
        <div style={{ background: 'rgba(255, 255, 255, 0.04)', padding: '1.25rem', borderRadius: '12px', marginBottom: '1.5rem' }}>
          <h4 style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Evaluator Feedback</h4>
          <p style={{ color: '#fff', fontSize: '1rem', lineHeight: '1.5' }}>"{evaluation.feedback}"</p>
        </div>

        {/* Missing Topics */}
        {evaluation.missing_topics && evaluation.missing_topics.length > 0 && (
          <div style={{ marginBottom: '1.5rem' }}>
            <h4 style={{ color: '#F59E0B', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem' }}>
              <AlertTriangle size={16} /> Concepts To Cover
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {evaluation.missing_topics.map((topic, idx) => (
                <span key={idx} style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#F59E0B', padding: '0.3rem 0.75rem', borderRadius: '6px', fontSize: '0.85rem' }}>
                  {topic}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Action Button */}
        <button
          onClick={onNextQuestion}
          className="btn-primary"
          style={{ width: '100%', justifyContent: 'center', padding: '0.9rem', fontSize: '1.05rem' }}
        >
          {isCompleted ? 'View Complete Final Report' : <>Proceed to Next Question <ArrowRight size={18} /></>}
        </button>

      </div>
    </div>
  );
}
