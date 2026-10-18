import axios from 'axios';
import { getAuthToken, getCurrentUser } from './supabaseClient';

// Base URL points to FastAPI backend (or proxied /api)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// Attach Supabase JWT Bearer token to all outgoing API requests when present
axios.interceptors.request.use(async (config) => {
  try {
    const token = await getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch (err) {
    // Non-blocking
  }
  return config;
});

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
  const activeUser = getCurrentUser();
  const resolvedUserId = userId || activeUser?.id || activeUser?.email || `candidate_${Math.floor(Math.random() * 1000)}`;

  if (mode) formData.append('mode', mode);
  formData.append('user_id', resolvedUserId);
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
    // Derive extension from actual recorded MIME type
    const ext = mimeType && mimeType.includes('ogg') ? '.ogg'
              : mimeType && mimeType.includes('mp4') ? '.mp4'
              : '.webm'; // Chrome/Edge default
    formData.append('audio_file', audioBlob, `recording${ext}`);
  }

  // Do NOT set Content-Type manually — the browser will generate the boundary
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

// Authentication Endpoints
export const apiSignup = async ({ name, email, password }) => {
  const response = await axios.post(`${API_BASE_URL}/auth/signup`, {
    name,
    email,
    password,
  });
  return response.data;
};

export const apiLogin = async ({ email, password }) => {
  const response = await axios.post(`${API_BASE_URL}/auth/login`, {
    email,
    password,
  });
  return response.data;
};

export const apiGoogleAuth = async ({ email, name, avatar, google_id }) => {
  const response = await axios.post(`${API_BASE_URL}/auth/google`, {
    email,
    name,
    avatar,
    google_id,
  });
  return response.data;
};

export const apiGetMe = async () => {
  const response = await axios.get(`${API_BASE_URL}/auth/me`);
  return response.data;
};

