// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

const TOKEN_KEY = 'auth_token'

export const getAuthHeader = () => ({
  'Authorization': `Bearer ${localStorage.getItem(TOKEN_KEY)}`
})

export const getJsonHeader = () => ({
  'Content-Type': 'application/json',
  ...getAuthHeader()
})
