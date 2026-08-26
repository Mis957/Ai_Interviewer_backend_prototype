import axios from 'axios';

// Base URL points to FastAPI backend (or proxied /api)
const API_BASE_URL = 'http://127.0.0.1:8000';

export const checkHealth = async () => {
  const response = await axios.get(`${API_BASE_URL}/health`);
  return response.data;
};

export const startInterview = async (technology, initialDifficulty = 'Easy') => {
  const response = await axios.post(`${API_BASE_URL}/interview/start`, {
    user_id: `candidate_${Math.floor(Math.random() * 1000)}`,
    technology: technology,
    initial_difficulty: initialDifficulty
  });
  return response.data;
};

export const submitAnswer = async ({ sessionId, questionId, generatedQuestionId, candidateAnswer, audioBlob }) => {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  if (questionId) formData.append('question_id', questionId);
  if (generatedQuestionId) formData.append('generated_question_id', generatedQuestionId);
  
  if (candidateAnswer) {
    formData.append('candidate_answer', candidateAnswer);
  }

  if (audioBlob) {
    formData.append('audio_file', audioBlob, 'recording.wav');
  }

  const response = await axios.post(`${API_BASE_URL}/interview/answer`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const endInterview = async (sessionId) => {
  const formData = new FormData();
  formData.append('session_id', sessionId);

  const response = await axios.post(`${API_BASE_URL}/interview/end`, formData);
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
