import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Home from './pages/Home'
import Login from './pages/Login'
import Signup from './pages/Signup'
import GoogleAuthPage from './pages/GoogleAuthPage'
import Overview from './pages/Overview'
import InterviewDashboard from './pages/InterviewDashboard'
import History from './pages/History'
import Settings from './pages/Settings'
import InterviewLive from './pages/InterviewLive'
import ProtectedRoute from './components/auth/ProtectedRoute'
import { subscribeToAuthChanges } from './services/supabaseClient'

export default function App() {
  useEffect(() => {
    const unsubscribe = subscribeToAuthChanges()
    return () => {
      if (unsubscribe) unsubscribe()
    }
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/auth/google" element={<GoogleAuthPage />} />
        
        {/* Protected Candidate Routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Overview />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/new"
          element={
            <ProtectedRoute>
              <InterviewDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interview/live"
          element={
            <ProtectedRoute>
              <InterviewLive />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <History />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
