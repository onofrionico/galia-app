import { Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'

export const RoleProtectedRoute = ({ moduleName, children }) => {
  const { user, userModules, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (!userModules.some(module => module.name === moduleName)) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center max-w-md">
          <div className="mb-6">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4v2m0 4v2M6.343 17.657l1.414-1.414m2.828 0l1.414 1.414m2.828 0l1.414-1.414m-9.9-2.828l-1.414-1.414m9.9 0l1.414-1.414" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Acceso Denegado</h2>
          <p className="text-gray-600 mb-6">
            No tienes acceso al módulo <strong>{moduleName}</strong>. Por favor contacta a un administrador si crees que esto es un error.
          </p>
          <a
            href="/dashboard"
            className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
          >
            Volver al Dashboard
          </a>
        </div>
      </div>
    )
  }

  return children
}
