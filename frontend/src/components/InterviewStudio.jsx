import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Volume2, Send, StopCircle, RefreshCw, AlertCircle, Sparkles, CheckCircle2 } from 'lucide-react';
import { getAudioUrl } from '../services/api';

export default function InterviewStudio({
  session,
  currentQuestion,
  onSubmitAnswer,
  onEndInterview,
  isLoading,
  questionNumber
}) {
  const [textAnswer, setTextAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const audioPlayerRef = useRef(null);

  // Auto-play question TTS speech when new question arrives
  useEffect(() => {
    if (currentQuestion?.audio_url && audioPlayerRef.current) {
      const fullUrl = getAudioUrl(currentQuestion.audio_url);
      audioPlayerRef.current.src = fullUrl;
      audioPlayerRef.current.play().catch(e => console.log('Audio autoplay prevented:', e));
    }
    // Reset state for new question
    setTextAnswer('');
    setAudioBlob(null);
    setAudioUrl(null);
  }, [currentQuestion]);

  // Audio recording handlers
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlobObj = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setAudioBlob(audioBlobObj);
        setAudioUrl(URL.createObjectURL(audioBlobObj));
        // Stop audio tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      alert('Microphone access is required for voice response. Please grant permissions or use text input.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
    }
  };

  const handleSubmit = () => {
    if (!textAnswer.trim() && !audioBlob) {
      alert('Please speak your answer or type it in the text area before submitting.');
      return;
    }
    onSubmitAnswer({
      candidateAnswer: textAnswer,
      audioBlob: audioBlob
    });
  };

  const difficultyClass = `badge-${(currentQuestion?.difficulty || 'easy').toLowerCase()}`;

  return (
    <div style={{ maxWidth: '900px', margin: '2rem auto', padding: '0 1.5rem' }}>
      {/* Top Header Card */}
      <div className="glass-card" style={{ padding: '1.25rem 2rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Track: {session.technology}</span>
          <h2 style={{ fontSize: '1.4rem', color: '#fff' }}>Question {questionNumber}</h2>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span className={`badge ${difficultyClass}`}>
            Current Difficulty: {currentQuestion?.difficulty}
          </span>
          {currentQuestion?.is_llm_generated && (
            <span className="badge" style={{ background: 'rgba(139, 92, 246, 0.2)', color: 'var(--purple)', border: '1px solid rgba(139, 92, 246, 0.4)' }}>
              <Sparkles size={14} /> Dynamic LLM Question
            </span>
          )}
        </div>
      </div>

      {/* Question Main Card */}
      <div className="glass-card" style={{ padding: '2rem', marginBottom: '1.5rem', borderLeft: '4px solid var(--primary)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', marginBottom: '1rem' }}>
          <span style={{ fontSize: '0.9rem', color: 'var(--primary-glow)', fontWeight: '600' }}>Topic: {currentQuestion?.topic}</span>
          <button
            onClick={() => audioPlayerRef.current?.play()}
            className="btn-secondary"
            style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
          >
            <Volume2 size={16} /> Replay Audio
          </button>
        </div>

        <h2 style={{ fontSize: '1.35rem', lineHeight: '1.5', color: '#fff', fontWeight: '500' }}>
          "{currentQuestion?.question_text}"
        </h2>

        {/* Hidden/Custom HTML5 Audio element */}
        <audio ref={audioPlayerRef} style={{ display: 'none' }} />
      </div>

      {/* Answer Studio Input Card */}
      <div className="glass-card" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.1rem', color: '#fff', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          Your Response (Voice or Text)
        </h3>

        {/* Voice Recorder Controls */}
        <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1.25rem', borderRadius: '12px', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {!isRecording ? (
              <button onClick={startRecording} className="btn-primary" style={{ background: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)' }}>
                <Mic size={18} /> Record Voice Response
              </button>
            ) : (
              <button onClick={stopRecording} className="btn-primary pulse-ring" style={{ background: '#DC2626' }}>
                <StopCircle size={18} /> Stop Recording ({recordingTime}s)
              </button>
            )}

            {audioBlob && !isRecording && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent)', fontSize: '0.9rem' }}>
                <CheckCircle2 size={18} /> Audio Recorded
                <audio src={audioUrl} controls style={{ height: '32px', marginLeft: '0.5rem' }} />
              </div>
            )}
          </div>

          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {isRecording ? 'Listening via Microphone...' : 'Or type your answer below'}
          </span>
        </div>

        {/* Fallback Text Area */}
        <textarea
          rows={4}
          value={textAnswer}
          onChange={(e) => setTextAnswer(e.target.value)}
          placeholder="Type your technical answer here in detail..."
          style={{
            width: '100%',
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-color)',
            borderRadius: '12px',
            padding: '1rem',
            color: '#fff',
            fontFamily: 'inherit',
            fontSize: '1rem',
            resize: 'vertical',
            outline: 'none'
          }}
        />
      </div>

      {/* Action Footer */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <button
          onClick={onEndInterview}
          className="btn-secondary"
          style={{ color: '#EF4444', borderColor: 'rgba(239, 68, 68, 0.3)' }}
        >
          End Interview Early
        </button>

        <button
          onClick={handleSubmit}
          disabled={isLoading}
          className="btn-primary"
          style={{ padding: '0.85rem 2rem', fontSize: '1.05rem' }}
        >
          {isLoading ? 'Evaluating with Gemini...' : <>Submit Answer <Send size={18} /></>}
        </button>
      </div>
    </div>
  );
}
