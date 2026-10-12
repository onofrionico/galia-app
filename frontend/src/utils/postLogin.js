const STORAGE_KEY = 'postLoginRedirect'

const isInternalPath = (path) =>
  typeof path === 'string' && path.startsWith('/') && !path.startsWith('//') && !path.startsWith('/login')

// Adónde va el usuario al iniciar sesión: la ruta de la que venía (si es válida) o, si no, según sus permisos.
// Un mozo (Camarero sin POS ni admin) va directo a la vista del celular.
export function postLoginPath({ from = null, stored = null, isAdmin = false, modules = [] } = {}) {
  if (isInternalPath(from)) return from
  if (isInternalPath(stored)) return stored
  const names = modules.map((m) => (typeof m === 'string' ? m : m?.name))
  if (!isAdmin && names.includes('Camarero') && !names.includes('POS')) return '/camarero'
  return '/dashboard'
}

// Ruta de origen cuando un 401 manda al login con window.location (se pierde el estado del router).
export function storeRedirect(path) {
  try {
    sessionStorage.setItem(STORAGE_KEY, path)
  } catch {
    // Sin storage: el login usa el destino según permisos.
  }
}

export function takeStoredRedirect() {
  try {
    const path = sessionStorage.getItem(STORAGE_KEY)
    sessionStorage.removeItem(STORAGE_KEY)
    return path
  } catch {
    return null
  }
}
