import api from './api'

const TOKEN_KEY = 'auth_token'

export const authService = {
  async login(email, password) {
    const response = await api.post('/auth/login', { email, password })
    const { token, user } = response.data
    
    if (token) {
      localStorage.setItem(TOKEN_KEY, token)
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
    
    return user
  },

  async logout() {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      console.error('Error during logout:', error)
    } finally {
      localStorage.removeItem(TOKEN_KEY)
      delete api.defaults.headers.common['Authorization']
    }
  },

  async getCurrentUser() {
    const token = localStorage.getItem(TOKEN_KEY)
    
    if (!token) {
      return null
    }
    
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    
    try {
      const response = await api.get('/auth/me')
      return response.data.user
    } catch (error) {
      localStorage.removeItem(TOKEN_KEY)
      delete api.defaults.headers.common['Authorization']
      return null
    }
  },

  getToken() {
    return localStorage.getItem(TOKEN_KEY)
  },

  setToken(token) {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token)
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
  },
}
