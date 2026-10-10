import { createContext, useContext, useState, useEffect } from 'react'
import { authService } from '@/services/authService'
import permissionsService from '@/services/permissionsService'

const AuthContext = createContext(null)

// Módulos de autoservicio previos al sistema de permisos: si falla la carga
// (p. ej. frontend desplegado antes que las migraciones) los empleados conservan sus links.
const LEGACY_EMPLOYEE_MODULES = [{ name: 'MyPayroll' }, { name: 'MySchedule' }]

const loadModules = async (userData) => {
  try {
    return await permissionsService.getMyModules()
  } catch (error) {
    console.error('Error cargando módulos del usuario', error)
    return userData && userData.role !== 'admin' ? LEGACY_EMPLOYEE_MODULES : []
  }
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [userModules, setUserModules] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    initializeAuth()
  }, [])

  const initializeAuth = async () => {
    const token = authService.getToken()

    if (token) {
      try {
        const userData = await authService.getCurrentUser()
        if (userData) {
          setUser(userData)
          setUserModules(await loadModules(userData))
        } else {
          setUser(null)
          setUserModules([])
        }
      } catch (error) {
        setUser(null)
        setUserModules([])
      }
    }

    setLoading(false)
  }

  const login = async (email, password) => {
    const userData = await authService.login(email, password)
    setUser(userData)
    setUserModules(await loadModules(userData))
    return userData
  }

  const logout = async () => {
    await authService.logout()
    setUser(null)
    setUserModules([])
  }

  const isAdmin = () => {
    return user?.role === 'admin'
  }

  // El admin tiene acceso a todo aunque falle la carga de módulos.
  const hasModuleAccess = (moduleName) => {
    if (isAdmin()) return true
    return userModules.some(module => module.name === moduleName)
  }

  return (
    <AuthContext.Provider value={{ user, userModules, loading, login, logout, isAdmin, hasModuleAccess }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
