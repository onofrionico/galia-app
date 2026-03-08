import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      console.log('Token enviado:', token.substring(0, 20) + '...')
    } else {
      console.warn('No hay token en localStorage')
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Manejo de error 401 - No autenticado
    if (error.response?.status === 401 && !window.location.pathname.includes('/login')) {
      console.warn('[SECURITY] 401 Unauthorized - Redirigiendo a login')
      localStorage.removeItem('auth_token')
      delete api.defaults.headers.common['Authorization']
      window.location.href = '/login'
    }
    
    // Manejo de error 403 - No autorizado (sin permisos)
    if (error.response?.status === 403) {
      console.error(
        '[SECURITY] 403 Forbidden - Acceso denegado',
        {
          path: error.config?.url,
          method: error.config?.method,
          message: error.response?.data?.message || error.response?.data?.error
        }
      )
      
      // Mostrar notificación al usuario
      const errorMessage = error.response?.data?.message || 
                          error.response?.data?.error || 
                          'No tienes permisos para acceder a este recurso'
      
      // Crear evento personalizado para que los componentes puedan escucharlo
      window.dispatchEvent(new CustomEvent('forbidden-access', {
        detail: {
          message: errorMessage,
          path: error.config?.url
        }
      }))
      
      // Si no estamos en la página de inicio, redirigir después de 2 segundos
      if (!window.location.pathname.includes('/dashboard') && 
          !window.location.pathname.includes('/home')) {
        setTimeout(() => {
          window.location.href = '/dashboard'
        }, 2000)
      }
    }
    
    return Promise.reject(error)
  }
)

export default api
