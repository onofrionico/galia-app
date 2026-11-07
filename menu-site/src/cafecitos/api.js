import { clearToken, getToken } from './session'

// Sin VITE_API_URL en producción no hay backend al que llamar (la carta es un sitio estático).
export function apiBase(env) {
  if (env.VITE_API_URL) return `${env.VITE_API_URL}/api/public/loyalty`
  return env.PROD ? null : '/api/public/loyalty'
}

const API = apiBase(import.meta.env)
export const apiConfigured = API !== null

export class ApiError extends Error {
  constructor(status, body) {
    super(body?.error || 'Algo salió mal, probá de nuevo')
    this.status = status
    this.body = body
  }
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  if (!apiConfigured) throw new ApiError(503, { error: 'Mis cafecitos todavía no está configurado.' })
  const headers = { 'Content-Type': 'application/json' }
  const token = auth ? getToken() : null
  if (token) headers.Authorization = `Bearer ${token}`
  const resp = await fetch(`${API}${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined })
  const data = await resp.json().catch(() => null)
  if (resp.status === 401 && auth) clearToken()
  if (!resp.ok) throw new ApiError(resp.status, data)
  return data
}

export const cafecitosApi = {
  loginWithGoogle: (credential, extra = {}) =>
    request('/auth/google', { method: 'POST', body: { credential, ...extra }, auth: false }),
  me: () => request('/me'),
  updateMe: (body) => request('/me', { method: 'PATCH', body }),
  movements: () => request('/me/movements'),
  rewards: () => request('/rewards', { auth: false }),
}
