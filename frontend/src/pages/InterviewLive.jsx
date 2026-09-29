import { useState, useEffect, useCallback, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import '../interview.css'
import { getAudioUrl, submitAnswer, endInterview } from '../services/api'
import PerformanceReport from '../components/PerformanceReport'

// ── Interview state machine ──────────────────────────────────────
const INTERVIEW_STATES = {
  INITIALIZING: 'INITIALIZING',
  AI_SPEAKING:  'AI_SPEAKING',
  LISTENING:    'LISTENING',
  RECORDING:    'RECORDING',   // mic is live, candidate speaking
  PROCESSING:   'PROCESSING',  // submitted, waiting for backend
  COMPLETED:    'COMPLETED',
  ERROR:        'ERROR',
}

// ── Oliver interviewer visual definition ─────────────────────────
const OLIVER_INTERVIEWER = {
  name: 'Oliver',
  role: 'Oliver — AI Interviewer',
  avatarUrl: null,
  avatarGradient: 'linear-gradient(135deg, #c084fc, #a855f7, #7c3aed)',
}

// ── Status display helper ────────────────────────────────────────
function getStatusDisplay(state, interviewerName = 'AI') {
  switch (state) {
    case INTERVIEW_STATES.INITIALIZING:
      return { label: 'PREPARING INTERVIEW',  dotColor: '#f59e0b' }
    case INTERVIEW_STATES.AI_SPEAKING:
      return { label: `${interviewerName.toUpperCase()} SPEAKING`, dotColor: '#8b5cf6' }
    case INTERVIEW_STATES.LISTENING:
      return { label: 'YOUR TURN',             dotColor: '#22c55e' }
    case INTERVIEW_STATES.RECORDING:
      return { label: "YOU'RE SPEAKING",       dotColor: '#3b82f6' }
    case INTERVIEW_STATES.PROCESSING:
      return { label: 'ANALYZING RESPONSE',    dotColor: '#f59e0b' }
    case INTERVIEW_STATES.COMPLETED:
      return { label: 'INTERVIEW COMPLETE',    dotColor: '#10b981' }
    case INTERVIEW_STATES.ERROR:
      return { label: 'SOMETHING WENT WRONG',  dotColor: '#ef4444' }
    default:
      return { label: 'STANDBY',               dotColor: '#94a3b8' }
  }
}

// ── Detect a supported MediaRecorder MIME type ───────────────────
// Tries common types in preference order; falls back to empty string
// which lets the browser choose its own default.
function getSupportedMimeType() {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/ogg',
    'audio/mp4',
  ]
  for (const type of candidates) {
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(type)) {
      return type
    }
  }
  return '' // browser default
}

// ─────────────────────────────────────────────────────────────────
// Sub-components (unchanged visual design)
// ─────────────────────────────────────────────────────────────────

/** Interviewer badge — top left */
function InterviewerBadge({ interviewer }) {
  const initial = interviewer.name ? interviewer.name[0].toUpperCase() : '?'
  return (
    <div className="interviewer-badge" role="status" aria-label={`Interviewer: ${interviewer.name}`}>
      <div
        className="interviewer-avatar"
        style={{ background: interviewer.avatarGradient || '#a78bfa' }}
        aria-hidden="true"
      >
        {interviewer.avatarUrl
          ? <img src={interviewer.avatarUrl} alt={interviewer.name} />
          : <span>{initial}</span>
        }
      </div>
      <div className="interviewer-info">
        <div className="interviewer-name">{interviewer.name}</div>
        <div className="interviewer-role">{interviewer.role}</div>
      </div>
    </div>
  )
}

function parseDurationSeconds(durationStr) {
  if (typeof durationStr === 'number') return durationStr
  if (!durationStr) return 15 * 60
  const match = String(durationStr).match(/(\d+)/)
  if (match) {
    const mins = parseInt(match[1], 10)
    if (!isNaN(mins) && mins > 0) return mins * 60
  }
  return 15 * 60
}

/** Session timer — top right */
function SessionTimer({ duration, isRunning, onTimeUp }) {
  const [elapsed, setElapsed] = useState(0)
  const intervalRef = useRef(null)
  const hasTriggeredTimeUp = useRef(false)

  useEffect(() => {
    if (duration > elapsed) {
      hasTriggeredTimeUp.current = false
    }
  }, [duration, elapsed])

  useEffect(() => {
    if (!isRunning) return
    intervalRef.current = setInterval(() => {
      setElapsed(prev => {
        if (prev + 1 >= duration) {
          clearInterval(intervalRef.current)
          if (!hasTriggeredTimeUp.current) {
            hasTriggeredTimeUp.current = true
            if (onTimeUp) onTimeUp()
          }
          return duration
        }
        return prev + 1
      })
    }, 1000)
    return () => clearInterval(intervalRef.current)
  }, [isRunning, duration, onTimeUp])

  const remaining = Math.max(0, duration - elapsed)
  const minutes = String(Math.floor(remaining / 60)).padStart(2, '0')
  const seconds = String(remaining % 60).padStart(2, '0')

  return (
    <div className="session-timer" role="timer" aria-label={`Time remaining: ${minutes}:${seconds}`}>
      <span className="timer-dot" aria-hidden="true" />
      {minutes}:{seconds}
    </div>
  )
}

/** Timer Expired / Extension Modal ("Time's Up!") */
function TimerExpiredModal({ onEndSession, onExtendSession, isEnding }) {
  const [selectedMinutes, setSelectedMinutes] = useState(5)

  return (
    <div className="interview-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="timer-expired-title">
      <div className="interview-modal timer-expired-modal">
        <div className="timer-expired-icon" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="9" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
        </div>
        <h3 id="timer-expired-title">Time's Up!</h3>
        <p>
          Your session timer has expired. Would you like to conclude your interview and see your report, or extend your time to keep practicing?
        </p>

        {/* Extension time picker */}
        <div className="timer-extension-box">
          <label className="timer-extension-label">
            Extend Time By:
          </label>
          <div className="timer-extension-options">
            {[5, 10, 15].map(mins => (
              <button
                key={mins}
                type="button"
                className={`timer-extension-btn ${selectedMinutes === mins ? 'active' : ''}`}
                onClick={() => setSelectedMinutes(mins)}
              >
                +{mins} mins
              </button>
            ))}
          </div>
        </div>

        <div className="interview-modal-actions timer-expired-actions">
          <button
            type="button"
            className="modal-extend-btn"
            onClick={() => onExtendSession(selectedMinutes)}
            disabled={isEnding}
          >
            Extend by +{selectedMinutes} mins &amp; Continue
          </button>
          
          <button
            type="button"
            className="modal-cancel-btn"
            onClick={onEndSession}
            disabled={isEnding}
          >
            {isEnding ? 'Generating Report…' : 'End Interview & Get Report'}
          </button>
        </div>
      </div>
    </div>
  )
}

/**
 * AI Orb — center visual, state-aware.
 * Maps RECORDING → data-state="USER_SPEAKING" so the existing CSS animation
 * (orbUserSpeaking) fires correctly.
 * Clicking the orb replays audio when autoplay is blocked.
 */
function AIOrb({ state, audioLevel = 0, onReplayAudio }) {
  // Map internal RECORDING state to the CSS class name the stylesheet expects
  const cssState = state === INTERVIEW_STATES.RECORDING ? 'USER_SPEAKING' : state

  return (
    <div className="ai-orb-container">
      <div
        className="ai-orb"
        data-state={cssState}
        aria-hidden="true"
        onClick={onReplayAudio}
        style={onReplayAudio ? { cursor: 'pointer' } : undefined}
        title={onReplayAudio ? 'Click to replay question audio' : undefined}
      >
        <div className="ai-orb-glow" />
        <div
          className="ai-orb-sphere"
          style={audioLevel > 0 ? { transform: `scale(${1 + audioLevel * 0.08})` } : undefined}
        />
        <div className="ai-orb-highlight" />
        <div className="ai-orb-highlight" />
        <div className="ai-orb-highlight" />
        <div className="ai-orb-highlight" />
      </div>
    </div>
  )
}

/** Question Card — center right */
function InterviewQuestionCard({ question }) {
  return (
    <div className="question-card" role="region" aria-label="Current interview question">
      <div className="question-label">
        <span className="question-label-dot" aria-hidden="true" />
        CURRENT QUESTION
      </div>
      <p className="question-text">{question}</p>
    </div>
  )
}

/** Status indicator — bottom */
function InterviewStatusIndicator({ state, interviewerName }) {
  const { label, dotColor } = getStatusDisplay(state, interviewerName)
  return (
    <div className="interview-status" role="status" aria-live="polite" aria-label={label}>
      <span className="status-dot" style={{ background: dotColor }} aria-hidden="true" />
      {label}
    </div>
  )
}

/** Mic button shown during LISTENING and RECORDING states */
function MicButton({ state, onStartRecording, onStopRecording, recordingSeconds }) {
  const isListening  = state === INTERVIEW_STATES.LISTENING
  const isRecording  = state === INTERVIEW_STATES.RECORDING

  if (!isListening && !isRecording) return null

  return (
    <button
      id="mic-toggle-btn"
      className={isRecording ? 'mic-btn mic-btn--recording' : 'mic-btn'}
      onClick={isRecording ? onStopRecording : onStartRecording}
      type="button"
      aria-label={isRecording ? 'Stop recording' : 'Start recording your answer'}
      title={isRecording ? 'Stop recording' : 'Tap to answer'}
    >
      {isRecording ? (
        <>
          <span className="mic-btn-dot" aria-hidden="true" />
          STOP  {recordingSeconds > 0 && `(${recordingSeconds}s)`}
        </>
      ) : (
        <>
          {/* Inline mic SVG — matches the PrepTalk icon style */}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2" strokeLinecap="round"
               strokeLinejoin="round" aria-hidden="true">
            <rect x="8" y="3" width="8" height="12" rx="4" />
            <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
          </svg>
          ANSWER
        </>
      )}
    </button>
  )
}

/** End Session confirmation modal */
function EndSessionModal({ onCancel, onConfirm, isEnding }) {
  const cancelRef = useRef(null)

  useEffect(() => {
    cancelRef.current?.focus()
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && !isEnding) onCancel()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onCancel, isEnding])

  return (
    <div className="interview-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="end-session-title">
      <div className="interview-modal">
        <h3 id="end-session-title">End this interview?</h3>
        <p>
          Your current answers will be saved and evaluated to generate your performance report.
        </p>
        <div className="interview-modal-actions">
          <button
            ref={cancelRef}
            className="modal-cancel-btn"
            onClick={onCancel}
            disabled={isEnding}
            type="button"
          >
            Cancel
          </button>
          <button
            className="modal-end-btn"
            onClick={onConfirm}
            disabled={isEnding}
            type="button"
          >
            {isEnding ? 'Ending…' : 'End Interview'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────
// Main Interview Page
// ─────────────────────────────────────────────────────────────────

const DEFAULT_DURATION_SECONDS = 15 * 60

export default function InterviewLive() {
  const location  = useLocation()
  const navigate  = useNavigate()

  // ── Session data from InterviewDashboard nav state ───────────────
  const sessionData = location.state?.sessionData

  // ── Current question — driven exclusively by backend responses ───
  const [currentQuestion, setCurrentQuestion] = useState(
    () => sessionData?.first_question ?? null
  )

  // ── Interview state machine ──────────────────────────────────────
  const [interviewState, setInterviewState] = useState(INTERVIEW_STATES.INITIALIZING)
  const [showEndModal,   setShowEndModal]   = useState(false)
  const [showTimerExpiredModal, setShowTimerExpiredModal] = useState(false)
  const [addedSeconds, setAddedSeconds]     = useState(0)
  const [isSaving,       setIsSaving]       = useState(false)
  const [isEnding,       setIsEnding]       = useState(false)
  const [timerRunning,   setTimerRunning]   = useState(false)

  // ── Final Performance Report Data & Errors ────────────────────────
  const [reportData,     setReportData]     = useState(null)
  const [endError,       setEndError]       = useState(null)
  const [submitError,    setSubmitError]    = useState(null)

  // ── Recording state ──────────────────────────────────────────────
  const [recordingSeconds, setRecordingSeconds] = useState(0)

  // ── Refs ─────────────────────────────────────────────────────────
  const audioRef            = useRef(null)   // TTS playback element
  const mediaRecorderRef    = useRef(null)   // active MediaRecorder instance
  const audioChunksRef      = useRef([])     // collected Blob chunks
  const recordingMimeRef    = useRef('')     // actual MIME type used
  const micStreamRef        = useRef(null)   // getUserMedia stream
  const recordingTimerRef   = useRef(null)   // seconds counter
  const isSubmittingRef     = useRef(false)  // duplicate-submit guard

  // ── Helper: stop microphone stream tracks ────────────────────────
  const stopMicStream = useCallback(() => {
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach(track => track.stop())
      micStreamRef.current = null
    }
  }, [])

  // ── Redirect guard ───────────────────────────────────────────────
  useEffect(() => {
    if (!sessionData || !sessionData.session_id) {
      navigate('/dashboard', { replace: true })
    }
  }, [sessionData, navigate])

  // ── TTS playback effect ──────────────────────────────────────────
  // Fires whenever currentQuestion changes.
  // State machine is driven exclusively by real audio events — no fake timers.
  useEffect(() => {
    const audio = audioRef.current
    if (!audio || !currentQuestion) return

    const audioUrl = getAudioUrl(currentQuestion.audio_url)

    if (!audioUrl) {
      // No audio for this question — go straight to LISTENING
      setInterviewState(INTERVIEW_STATES.LISTENING)
      setTimerRunning(true)
      return
    }

    // Stop any currently playing audio
    audio.pause()
    audio.currentTime = 0

    const handlePlay = () => {
      setInterviewState(INTERVIEW_STATES.AI_SPEAKING)
      setTimerRunning(true)
    }

    const handleEnded = () => {
      setInterviewState(INTERVIEW_STATES.LISTENING)
    }

    const handleError = () => {
      console.warn('[InterviewLive] Audio playback error for:', audioUrl)
      // Graceful fallback: skip to LISTENING so candidate can still answer
      setInterviewState(INTERVIEW_STATES.LISTENING)
      setTimerRunning(true)
    }

    audio.addEventListener('play',  handlePlay)
    audio.addEventListener('ended', handleEnded)
    audio.addEventListener('error', handleError)

    audio.src = audioUrl
    audio.load()
    audio.play().catch((err) => {
      console.warn('[InterviewLive] Autoplay blocked:', err.message)
      // Autoplay policy blocked — let candidate click orb to replay,
      // and transition to LISTENING so mic button appears.
      setInterviewState(INTERVIEW_STATES.LISTENING)
      setTimerRunning(true)
    })

    return () => {
      audio.removeEventListener('play',  handlePlay)
      audio.removeEventListener('ended', handleEnded)
      audio.removeEventListener('error', handleError)
    }
  }, [currentQuestion])

  // ── Component unmount cleanup ────────────────────────────────────
  useEffect(() => {
    return () => {
      const audio = audioRef.current
      if (audio) { audio.pause(); audio.src = '' }
      stopMicStream()
      clearInterval(recordingTimerRef.current)
    }
  }, [stopMicStream])

  // ── Replay TTS audio — orb click ────────────────────────────────
  const handleReplayAudio = useCallback(() => {
    const audio = audioRef.current
    if (!audio || !audio.src) return
    audio.currentTime = 0
    audio.play().catch(err => console.warn('[InterviewLive] Replay failed:', err.message))
  }, [])

  // ── Handle when timer expires ────────────────────────────────────
  const handleTimerExpired = useCallback(() => {
    setTimerRunning(false)
    const audio = audioRef.current
    if (audio) audio.pause()
    stopMicStream()
    setShowTimerExpiredModal(true)
  }, [stopMicStream])

  // ── Extend time option ───────────────────────────────────────────
  const handleExtendSession = useCallback((minutes) => {
    const extra = (minutes || 5) * 60
    setAddedSeconds(prev => prev + extra)
    setShowTimerExpiredModal(false)
    setTimerRunning(true)
  }, [])

  // ── End session and fetch final report from backend ──────────────
  const handleEndSession = useCallback(async () => {
    if (isEnding) return
    setIsEnding(true)
    setEndError(null)

    const audio = audioRef.current
    if (audio) audio.pause()
    stopMicStream()
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop() } catch (e) {}
    }
    clearInterval(recordingTimerRef.current)
    setTimerRunning(false)
    setShowEndModal(false)
    setShowTimerExpiredModal(false)

    try {
      const report = await endInterview(sessionData.session_id)
      console.info('[InterviewLive] Final report received:', report)
      setReportData(report)
      setInterviewState(INTERVIEW_STATES.COMPLETED)
    } catch (err) {
      console.error('[InterviewLive] End session failed:', err)
      const detail = err?.response?.data?.detail || err?.message || 'Unable to generate your performance report. Please try again.'
      setEndError(detail)
    } finally {
      setIsEnding(false)
    }
  }, [isEnding, sessionData?.session_id, stopMicStream])

  // ── Start recording ──────────────────────────────────────────────
  const handleStartRecording = useCallback(async () => {
    // Guard: only allow from LISTENING state
    if (interviewState !== INTERVIEW_STATES.LISTENING) return
    // Guard: prevent multiple recorder instances
    if (mediaRecorderRef.current) return

    setSubmitError(null)

    let stream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch (err) {
      console.error('[InterviewLive] Microphone access denied:', err)
      setSubmitError('Microphone access is required. Please grant permission and try again.')
      return
    }

    micStreamRef.current = stream

    // Detect the best supported MIME type
    const mimeType = getSupportedMimeType()
    recordingMimeRef.current = mimeType

    const recorderOptions = mimeType ? { mimeType } : {}
    const recorder = new MediaRecorder(stream, recorderOptions)
    mediaRecorderRef.current = recorder
    audioChunksRef.current = []

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        audioChunksRef.current.push(e.data)
      }
    }

    // onstop fires after recorder.stop() — build the Blob and submit here
    recorder.onstop = async () => {
      clearInterval(recordingTimerRef.current)
      stopMicStream()
      mediaRecorderRef.current = null

      const actualMime = recordingMimeRef.current || 'audio/webm'
      const blob = new Blob(audioChunksRef.current, { type: actualMime })

      // Submit to backend
      await handleSubmitAnswer(blob, actualMime)
    }

    recorder.start()
    setInterviewState(INTERVIEW_STATES.RECORDING)
    setRecordingSeconds(0)

    // Seconds counter
    recordingTimerRef.current = setInterval(() => {
      setRecordingSeconds(prev => prev + 1)
    }, 1000)
  }, [interviewState, stopMicStream])   // eslint-disable-line react-hooks/exhaustive-deps

  // ── Stop recording ───────────────────────────────────────────────
  const handleStopRecording = useCallback(() => {
    if (interviewState !== INTERVIEW_STATES.RECORDING) return
    if (!mediaRecorderRef.current) return

    // Transition immediately so the user sees PROCESSING
    setInterviewState(INTERVIEW_STATES.PROCESSING)

    // recorder.onstop → handleSubmitAnswer
    mediaRecorderRef.current.stop()
  }, [interviewState])

  // ── Submit answer to backend ─────────────────────────────────────
  const handleSubmitAnswer = useCallback(async (audioBlob, mimeType) => {
    // Duplicate-submit guard
    if (isSubmittingRef.current) return
    isSubmittingRef.current = true

    // Pause TTS in case it was replaying
    const audio = audioRef.current
    if (audio) { audio.pause() }

    try {
      const response = await submitAnswer({
        sessionId:           sessionData.session_id,
        questionId:          currentQuestion?.question_id          ?? null,
        generatedQuestionId: currentQuestion?.generated_question_id ?? null,
        audioBlob,
        mimeType,
      })

      // ── Log adaptive signals for runtime verification ────────────
      console.info('[InterviewLive] Evaluation received:', {
        score:              response.score,
        confidence_score:   response.confidence_score,
        current_difficulty: response.current_difficulty,
        next_difficulty:    response.next_difficulty,
        session_completed:  response.session_completed,
        next_question_text: response.next_question?.question_text ?? null,
      })

      // ── Session completed ────────────────────────────────────────
      if (response.session_completed) {
        handleEndSession()
        return
      }

      // ── Auto-advance to next question ────────────────────────────
      if (response.next_question) {
        setSubmitError(null)
        setRecordingSeconds(0)
        setInterviewState(INTERVIEW_STATES.PROCESSING)
        setCurrentQuestion(response.next_question)
      } else {
        console.warn('[InterviewLive] No next_question in response — ending session.')
        handleEndSession()
      }

    } catch (err) {
      console.error('[InterviewLive] Answer submission failed:', err)
      const detail = err?.response?.data?.detail || err?.message || 'Submission failed. Please try again.'
      setSubmitError(detail)
      setInterviewState(INTERVIEW_STATES.ERROR)
    } finally {
      isSubmittingRef.current = false
    }
  }, [sessionData, currentQuestion, handleEndSession])

  // ── Retry after ERROR ────────────────────────────────────────────
  const handleRetry = useCallback(() => {
    setSubmitError(null)
    setInterviewState(INTERVIEW_STATES.LISTENING)
  }, [])

  // ── Save & Exit ──────────────────────────────────────────────────
  const handleSaveExit = useCallback(() => {
    if (isSaving) return
    setIsSaving(true)
    const audio = audioRef.current
    if (audio) audio.pause()
    stopMicStream()
    navigate('/dashboard')
  }, [isSaving, navigate, stopMicStream])

  // ── Guard: no render without session ────────────────────────────
  if (!sessionData || !sessionData.session_id) {
    return (
      <div className="interview-page" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#fafaf8' }}>
        <div style={{ textAlign: 'center', padding: '2.5rem 2rem', background: '#ffffff', borderRadius: '20px', border: '1px solid rgba(0,0,0,0.08)', boxShadow: '0 8px 30px rgba(0,0,0,0.06)', maxWidth: '480px' }}>
          <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: '#e0e7ff', color: '#4338ca', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.25rem', fontSize: '24px', fontWeight: '700' }}>
            !
          </div>
          <h2 style={{ color: '#0f172a', fontSize: '1.5rem', fontWeight: '700', marginBottom: '0.5rem' }}>No Active Interview Session</h2>
          <p style={{ color: '#64748b', fontSize: '0.95rem', lineHeight: '1.5', marginBottom: '1.75rem' }}>
            Please start a new mock interview session from the dashboard to begin.
          </p>
          <button 
            type="button"
            onClick={() => navigate('/interview/new')} 
            style={{ 
              padding: '0.8rem 1.75rem', 
              background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)', 
              color: '#ffffff', 
              border: 'none', 
              borderRadius: '12px', 
              cursor: 'pointer', 
              fontWeight: '700', 
              fontSize: '1rem',
              boxShadow: '0 4px 14px rgba(79, 70, 229, 0.3)'
            }}
          >
            Start New Interview
          </button>
        </div>
      </div>
    )
  }

  // ── Render Full Performance Report screen when completed and report is ready ──
  if (interviewState === INTERVIEW_STATES.COMPLETED && reportData) {
    return (
      <div className="interview-page" style={{ minHeight: '100vh', overflowY: 'auto', display: 'block', background: '#fafaf8' }}>
        <PerformanceReport
          report={reportData}
          resumeScreeningResult={sessionData?.resumeScreeningResult}
          onRestart={() => navigate('/interview/new')}
        />
      </div>
    )
  }

  const isInitializing = interviewState === INTERVIEW_STATES.INITIALIZING
  const questionText   = currentQuestion?.question_text || ''

  const durationSeconds = parseDurationSeconds(sessionData?.duration) + addedSeconds

  return (
    <div className="interview-page">
      {/*
        Hidden audio element for TTS.
        Managed imperatively via audioRef; src is set in the TTS effect.
      */}
      <audio ref={audioRef} style={{ display: 'none' }} preload="auto" />

      <div className="interview-frame">

        {/* ── Header ──────────────────────────────────────────────── */}
        <header className="interview-header">
          <InterviewerBadge interviewer={OLIVER_INTERVIEWER} />
          <SessionTimer
            duration={durationSeconds}
            isRunning={timerRunning && interviewState !== INTERVIEW_STATES.COMPLETED}
            onTimeUp={handleTimerExpired}
          />
        </header>

        {/* ── Main Stage ──────────────────────────────────────────── */}
        <main className="interview-stage">
          <AIOrb
            state={interviewState}
            audioLevel={0}
            onReplayAudio={
              interviewState === INTERVIEW_STATES.LISTENING ||
              interviewState === INTERVIEW_STATES.AI_SPEAKING
                ? handleReplayAudio
                : undefined
            }
          />
          {isEnding ? (
            <div className="interview-completed-card" role="status" aria-label="Generating report">
              <div className="interview-completed-icon" aria-hidden="true">⏳</div>
              <h2 className="interview-completed-title">Generating Report</h2>
              <p className="interview-completed-body">
                Analyzing your responses and evaluating technical performance…
              </p>
            </div>
          ) : interviewState === INTERVIEW_STATES.COMPLETED ? (
            <div className="interview-completed-card" role="status" aria-label="Interview complete">
              <div className="interview-completed-icon" aria-hidden="true">✓</div>
              <h2 className="interview-completed-title">Interview Complete</h2>
              <p className="interview-completed-body">
                Great work! Your responses have been evaluated. Loading your performance report…
              </p>
            </div>
          ) : (
            !isInitializing && (
              <InterviewQuestionCard question={questionText} />
            )
          )}
        </main>

        {/* ── Bottom Controls ─────────────────────────────────────── */}
        <footer className="interview-bottom">
          <InterviewStatusIndicator
            state={interviewState}
            interviewerName={OLIVER_INTERVIEWER.name}
          />

          {/* Mic button — visible only in LISTENING / RECORDING */}
          <MicButton
            state={interviewState}
            onStartRecording={handleStartRecording}
            onStopRecording={handleStopRecording}
            recordingSeconds={recordingSeconds}
          />

          {/* Inline error message for answer submission */}
          {submitError && interviewState === INTERVIEW_STATES.ERROR && (
            <div className="interview-submit-error" role="alert">
              <span>{submitError}</span>
              <button type="button" onClick={handleRetry} className="error-retry-btn">
                Retry
              </button>
            </div>
          )}

          {/* Inline error message for report generation failure */}
          {endError && (
            <div className="interview-submit-error" role="alert" style={{ marginBottom: '1rem' }}>
              <span>{endError}</span>
              <button type="button" onClick={handleEndSession} className="error-retry-btn">
                Retry End Session
              </button>
            </div>
          )}

          <div className="interview-controls">
            {isSaving ? (
              <div className="saving-indicator">
                <span className="saving-spinner" />
                Saving…
              </div>
            ) : (
              <button
                className="save-exit-btn"
                onClick={handleSaveExit}
                disabled={isSaving || isInitializing || isEnding}
                type="button"
                aria-label="Save progress and exit interview"
              >
                Save &amp; Exit
              </button>
            )}

            <button
              className="end-session-btn"
              onClick={() => setShowEndModal(true)}
              disabled={isInitializing || isEnding}
              type="button"
              aria-label="End interview session"
            >
              <span className="end-session-dot" aria-hidden="true" />
              {isEnding ? 'ENDING…' : 'END SESSION'}
            </button>
          </div>
        </footer>

        {/* ── Initialization Overlay ───────────────────────────────── */}
        {isInitializing && (
          <div className="interview-init-overlay" role="status" aria-label="Preparing interview">
            <AIOrb state={INTERVIEW_STATES.INITIALIZING} />
            <p className="init-text">Preparing your interview…</p>
            <div className="init-dots" aria-hidden="true">
              <span /><span /><span />
            </div>
          </div>
        )}
      </div>

      {/* ── End Session Modal ──────────────────────────────────────── */}
      {showEndModal && (
        <EndSessionModal
          onCancel={() => setShowEndModal(false)}
          onConfirm={handleEndSession}
          isEnding={isEnding}
        />
      )}

      {/* ── Timer Expired Modal ────────────────────────────────────── */}
      {showTimerExpiredModal && (
        <TimerExpiredModal
          onEndSession={handleEndSession}
          onExtendSession={handleExtendSession}
          isEnding={isEnding}
        />
      )}
    </div>
  )
}
