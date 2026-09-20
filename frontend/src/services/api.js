import axios from 'axios';

// Base URL points to FastAPI backend (or proxied /api)
const API_BASE_URL = 'http://127.0.0.1:8000';

export const checkHealth = async () => {
  const response = await axios.get(`${API_BASE_URL}/health`);
  return response.data;
};

export const startInterview = async ({
  mode,
  userId,
  technology,
  targetRole,
  yearsOfExperience,
  initialDifficulty = 'Easy',
  resumeText,
  file
}) => {
  const formData = new FormData();

  if (mode) formData.append('mode', mode);
  formData.append('user_id', userId || `candidate_${Math.floor(Math.random() * 1000)}`);
  if (technology) formData.append('technology', technology);
  if (targetRole) formData.append('target_role', targetRole);
  if (yearsOfExperience) formData.append('years_of_experience', yearsOfExperience);
  if (initialDifficulty) formData.append('initial_difficulty', initialDifficulty);
  if (resumeText) formData.append('resume_text', resumeText);
  if (file) formData.append('file', file);

  const response = await axios.post(`${API_BASE_URL}/interview/start`, formData);
  return response.data;
};

export const submitAnswer = async ({ sessionId, questionId, generatedQuestionId, candidateAnswer, audioBlob, mimeType }) => {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  if (questionId) formData.append('question_id', questionId);
  if (generatedQuestionId) formData.append('generated_question_id', generatedQuestionId);

  if (candidateAnswer) {
    formData.append('candidate_answer', candidateAnswer);
  }

  if (audioBlob) {
    // Derive extension from the actual recorded MIME type so the backend
    // receives a filename that matches the real bytes (e.g. recording.webm,
    // not recording.wav when the browser recorded WebM/Opus).
    const ext = mimeType && mimeType.includes('ogg') ? '.ogg'
              : mimeType && mimeType.includes('mp4') ? '.mp4'
              : '.webm'; // Chrome/Edge default
    formData.append('audio_file', audioBlob, `recording${ext}`);
  }

  // Do NOT set Content-Type manually — the browser must generate the
  // multipart boundary automatically when sending FormData.
  const response = await axios.post(`${API_BASE_URL}/interview/answer`, formData);
  return response.data;
};

export const endInterview = async (sessionId) => {
  const formData = new FormData();
  formData.append('session_id', sessionId);

  const response = await axios.post(`${API_BASE_URL}/interview/end`, formData);
  return response.data;
};

export const screenResume = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post(`${API_BASE_URL}/resume/screen`, formData);
  return response.data;
};

export const fetchLearningAnalytics = async () => {
  const response = await axios.get(`${API_BASE_URL}/analytics/learning`);
  return response.data;
};

export const getAudioUrl = (relativePath) => {
  if (!relativePath) return null;
  // If absolute path returned from backend, extract filename
  if (relativePath.includes('/') || relativePath.includes('\\')) {
    const filename = relativePath.split(/[/\\]/).pop();
    return `${API_BASE_URL}/audio/${filename}`;
  }
  return `${API_BASE_URL}/audio/${relativePath}`;
};

