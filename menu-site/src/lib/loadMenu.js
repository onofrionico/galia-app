export const CACHE_KEY = 'galia-menu-v1'

export class MenuUnavailableError extends Error {}

function isValidMenu(data) {
  return Boolean(data) && data.version === 1 && Array.isArray(data.categories)
}

export function browserStorage() {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

function readCache(storage) {
  try {
    return JSON.parse(storage?.getItem(CACHE_KEY) || 'null')
  } catch {
    return null
  }
}

export async function loadMenu({ url, fetchImpl = globalThis.fetch, storage = browserStorage() } = {}) {
  try {
    const response = await fetchImpl(url, { cache: 'no-cache' })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const menu = await response.json()
    if (!isValidMenu(menu)) throw new Error('Formato de carta inválido')
    try {
      storage?.setItem(CACHE_KEY, JSON.stringify(menu))
    } catch {
      // storage lleno o bloqueado: la carta igual se muestra
    }
    return { menu, source: 'network' }
  } catch (error) {
    const cached = readCache(storage)
    if (isValidMenu(cached)) return { menu: cached, source: 'cache' }
    throw new MenuUnavailableError(error.message)
  }
}
