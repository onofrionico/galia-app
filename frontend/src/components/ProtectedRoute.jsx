import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Cargando...</div>
      </div>
    )
  }

  if (!user) {
    // Después del login se vuelve a esta ruta (p. ej. una venta abierta en el celular).
    return <Navigate to="/login" replace state={{ from: `${location.pathname}${location.search}` }} />
  }

  return children
}

export default ProtectedRoute
