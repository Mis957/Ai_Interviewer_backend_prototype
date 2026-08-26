import React, { useEffect, useState } from 'react';
import { checkHealth } from '../services/api';
import { Cpu, Brain, Database, Award } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const [isBackendHealthy, setIsBackendHealthy] = useState(false);

  useEffect(() => {
    checkHealth()
      .then(() => setIsBackendHealthy(true))
      .catch(() => setIsBackendHealthy(false));
  }, []);

  return (
    <nav style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '1.25rem 2rem',
      borderBottom: '1px solid var(--border-color)',
      background: 'rgba(11, 15, 25, 0.8)',
      backdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)'
        }}>
          <Brain color="#fff" size={24} />
        </div>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#fff' }}>InterviewReady.AI</h2>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Deterministic Interview Engine</span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1rem' }}>
        <button
          onClick={() => setActiveTab('studio')}
          className={activeTab === 'studio' ? 'btn-primary' : 'btn-secondary'}
          style={{ padding: '0.5rem 1.25rem', fontSize: '0.9rem' }}
        >
          <Cpu size={16} /> Interview Studio
        </button>
        <button
          onClick={() => setActiveTab('insights')}
          className={activeTab === 'insights' ? 'btn-primary' : 'btn-secondary'}
          style={{ padding: '0.5rem 1.25rem', fontSize: '0.9rem' }}
        >
          <Database size={16} /> Learned Insights
        </button>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
        <span style={{
          width: '10px',
          height: '10px',
          borderRadius: '50%',
          backgroundColor: isBackendHealthy ? 'var(--accent)' : '#EF4444',
          boxShadow: isBackendHealthy ? '0 0 10px var(--accent)' : '0 0 10px #EF4444'
        }}></span>
        <span style={{ color: 'var(--text-muted)' }}>
          Backend: {isBackendHealthy ? 'Connected (Port 8000)' : 'Disconnected'}
        </span>
      </div>
    </nav>
  );
}
