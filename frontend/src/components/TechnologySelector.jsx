import React, { useState } from 'react';
import { Play, Code, Database, Server, Cpu, Network, Users, ArrowRight } from 'lucide-react';

const TRACKS = [
  { id: 'Python', name: 'Python', desc: 'Decorators, AsyncIO, Memory & OOP', icon: Code, color: '#3776AB' },
  { id: 'DBMS', name: 'DBMS & SQL', desc: 'ACID, Indexing, Transactions & Normalization', icon: Database, color: '#336791' },
  { id: 'Java', name: 'Java', desc: 'JVM Heap, Multithreading & Collections', icon: Server, color: '#5382A1' },
  { id: 'Operating System', name: 'Operating System', desc: 'Processes, Virtual Memory & Thrashing', icon: Cpu, color: '#F29100' },
  { id: 'Computer Networks', name: 'Computer Networks', desc: 'TCP/IP Handshake, Subnetting & HTTP', icon: Network, color: '#00599C' },
  { id: 'Machine Learning', name: 'Machine Learning', desc: 'Overfitting, Loss Functions & Neural Nets', icon: Cpu, color: '#FF6F61' },
  { id: 'HR', name: 'HR & Behavioral', desc: 'STAR Technique, Leadership & Conflict Resolution', icon: Users, color: '#10B981' }
];

export default function TechnologySelector({ onStartInterview, isLoading }) {
  const [selectedTech, setSelectedTech] = useState('Python');
  const [difficulty, setDifficulty] = useState('Easy');

  const handleStart = () => {
    onStartInterview(selectedTech, difficulty);
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '3rem auto', padding: '0 1.5rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '2.75rem', fontWeight: '800', marginBottom: '1rem', background: 'linear-gradient(135deg, #fff 0%, #9CA3AF 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Choose Your Interview Track
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', maxWidth: '600px', margin: '0 auto' }}>
          Select a domain track. The interview engine will dynamically adjust question difficulty based on your real-time performance.
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '1.5rem',
        marginBottom: '2.5rem'
      }}>
        {TRACKS.map((track) => {
          const IconComp = track.icon;
          const isSelected = selectedTech === track.id;
          return (
            <div
              key={track.id}
              onClick={() => setSelectedTech(track.id)}
              className="glass-card"
              style={{
                padding: '1.5rem',
                cursor: 'pointer',
                borderColor: isSelected ? 'var(--primary-glow)' : 'var(--border-color)',
                boxShadow: isSelected ? '0 0 20px rgba(99, 102, 241, 0.4)' : 'none',
                transform: isSelected ? 'translateY(-4px)' : 'none'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <div style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '12px',
                  background: `${track.color}20`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <IconComp color={track.color} size={24} />
                </div>
                {isSelected && (
                  <span style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--primary-glow)', background: 'rgba(99, 102, 241, 0.15)', padding: '0.2rem 0.6rem', borderRadius: '20px' }}>
                    Selected
                  </span>
                )}
              </div>
              <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem', color: '#fff' }}>{track.name}</h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>{track.desc}</p>
            </div>
          );
        })}
      </div>

      {/* Starting Difficulty Selector */}
      <div className="glass-card" style={{ padding: '1.5rem 2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1.5rem' }}>
        <div>
          <h4 style={{ color: '#fff', fontSize: '1.1rem', marginBottom: '0.25rem' }}>Starting Difficulty Level</h4>
          <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Backend will automatically adapt difficulty up or down.</span>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          {['Easy', 'Medium', 'Hard'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setDifficulty(lvl)}
              className={difficulty === lvl ? `badge badge-${lvl.toLowerCase()}` : 'btn-secondary'}
              style={{
                padding: '0.6rem 1.25rem',
                fontSize: '0.9rem',
                cursor: 'pointer',
                borderRadius: '10px'
              }}
            >
              {lvl}
            </button>
          ))}
        </div>

        <button
          onClick={handleStart}
          disabled={isLoading}
          className="btn-primary"
          style={{ padding: '0.85rem 2rem', fontSize: '1.05rem' }}
        >
          {isLoading ? 'Starting Session...' : <>Start Interview <ArrowRight size={20} /></>}
        </button>
      </div>
    </div>
  );
}
