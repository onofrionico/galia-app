import { useAuth } from '@/context/AuthContext'

const AccessDenied = () => (
  <div className="flex items-center justify-center py-24">
    <div className="text-center max-w-md">
      <h2 className="text-2xl font-bold text-gray-900">Acceso denegado</h2>
      <p className="mt-2 text-gray-600">No tenés permisos para ver esta sección. Pedile acceso a un administrador.</p>
    </div>
  </div>
)

// Usar dentro de <ProtectedRoute>: asume que ya hay sesión.
export const RoleProtectedRoute = ({ moduleName, adminOnly = false, children }) => {
  const { loading, isAdmin, hasModuleAccess } = useAuth()

  if (loading) return null
  if (adminOnly ? !isAdmin() : !hasModuleAccess(moduleName)) return <AccessDenied />
  return children
}
