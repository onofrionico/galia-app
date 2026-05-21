import { createContext, useContext, useState, useEffect } from 'react'
import { authService } from '@/services/authService'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [userModules, setUserModules] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    initializeAuth()
  }, [])

  const fetchUserModules = async () => {
    try {
      const token = authService.getToken()
      console.log('[Auth] Fetching modules with token:', token?.substring(0, 20) + '...')
      const response = await fetch('http://localhost:5000/api/v1/permissions/modules/my-modules', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setUserModules(data.modules || [])
      }
    } catch (error) {
      console.error('Error fetching user modules:', error)
      setUserModules([])
    }
  }

  const initializeAuth = async () => {
    const token = authService.getToken()

    if (token) {
      try {
        const userData = await authService.getCurrentUser()
        setUser(userData)
        await fetchUserModules()
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
    await fetchUserModules()
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

  const isWaiter = () => {
    return user?.role === 'waiter'
  }

  const hasModuleAccess = (moduleName) => {
    if (!moduleName) return false
    return userModules.some(module => module.name === moduleName)
  }

  return (
    <AuthContext.Provider value={{ user, userModules, loading, login, logout, isAdmin, isWaiter, hasModuleAccess }}>
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
