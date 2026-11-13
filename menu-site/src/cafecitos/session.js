// Token de la sesión del cliente. Si localStorage no está disponible (modo privado, bloqueado), queda en memoria.
const KEY = 'galia.cafecitos.token'
let memory = null

export function getToken() {
  try {
    const stored = globalThis.localStorage?.getItem(KEY)
    if (stored) return stored
  } catch {
    // sin almacenamiento: usamos la copia en memoria
  }
  return memory
}

export function setToken(token) {
  memory = token
  try {
    globalThis.localStorage?.setItem(KEY, token)
  } catch {
    // queda solo en memoria
  }
}

export function clearToken() {
  memory = null
  try {
    globalThis.localStorage?.removeItem(KEY)
  } catch {
    // nada que borrar
  }
}
