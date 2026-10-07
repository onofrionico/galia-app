export const CACHE_KEY = 'galia-menu-v1'

export class MenuUnavailableError extends Error {}

function isValidMenu(data) {
  return Boolean(data) && data.version === 1 && Array.isArray(data.categories)
}

function normalizeMenu(menu) {
  return {
    ...menu,
    tags: Array.isArray(menu.tags) ? menu.tags : [],
    settings: menu.settings && typeof menu.settings === 'object' ? menu.settings : {},
    categories: menu.categories.map((category) => ({
      ...category,
      items: (Array.isArray(category.items) ? category.items : []).map((item) => ({
        ...item,
        tags: Array.isArray(item.tags) ? item.tags : [],
        variants: Array.isArray(item.variants) ? item.variants : [],
      })),
    })),
  }
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

export async function loadMenu({ url, fetchImpl = globalThis.fetch, storage = browserStorage(), timeoutMs = 8000 } = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    if (!url) throw new Error('URL de carta no configurada')
    const response = await fetchImpl(url, { cache: 'no-cache', signal: controller.signal })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const raw = await response.json()
    if (!isValidMenu(raw)) throw new Error('Formato de carta inválido')
    const menu = normalizeMenu(raw)
    try {
      storage?.setItem(CACHE_KEY, JSON.stringify(menu))
    } catch {
      // storage lleno o bloqueado: la carta igual se muestra
    }
    return { menu, source: 'network' }
  } catch (error) {
    const cached = readCache(storage)
    if (isValidMenu(cached)) return { menu: normalizeMenu(cached), source: 'cache' }
    throw new MenuUnavailableError(error.message)
  } finally {
    clearTimeout(timer)
  }
}
