import { Navigate, useLocation } from 'react-router-dom'
import { getCurrentUser } from '../../services/supabaseClient'

export default function ProtectedRoute({ children }) {
  const location = useLocation()
  const user = getCurrentUser()

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}
