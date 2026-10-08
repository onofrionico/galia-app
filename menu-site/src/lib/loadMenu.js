export const CACHE_KEY = 'galia-menu-v1'

export class MenuUnavailableError extends Error {}

function isValidMenu(data) {
  if (!data) return false
  return (
    (data.version === 1 && Array.isArray(data.categories)) ||
    (data.version === 2 && Array.isArray(data.groups))
  )
}

function normalizeCategory(category) {
  return {
    ...category,
    show_title: category.show_title !== false,
    items: (Array.isArray(category.items) ? category.items : []).map((item) => ({
      ...item,
      tags: Array.isArray(item.tags) ? item.tags : [],
      variants: Array.isArray(item.variants) ? item.variants : [],
    })),
  }
}

function normalizeMenu(menu) {
  const groups = menu.version === 1
    ? [{ slug: '_carta', name: null, categories: menu.categories }]
    : menu.groups
  const { categories, ...rest } = menu
  return {
    ...rest,
    version: 2,
    tags: Array.isArray(menu.tags) ? menu.tags : [],
    settings: menu.settings && typeof menu.settings === 'object' ? menu.settings : {},
    groups: groups.map((group) => ({
      ...group,
      name: group.name ?? null,
      categories: (Array.isArray(group.categories) ? group.categories : []).map(normalizeCategory),
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
