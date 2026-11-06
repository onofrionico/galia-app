import { clearToken, getToken } from './session'

const API = `${import.meta.env.VITE_API_URL || ''}/api/public/loyalty`

export class ApiError extends Error {
  constructor(status, body) {
    super(body?.error || 'Algo salió mal, probá de nuevo')
    this.status = status
    this.body = body
  }
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
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
