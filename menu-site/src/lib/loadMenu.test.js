import { describe, it, expect } from 'vitest'
import { loadMenu, CACHE_KEY, MenuUnavailableError } from './loadMenu'

const validMenu = { version: 1, settings: {}, tags: [], categories: [{ slug: 'cafes', name: 'Cafés', items: [] }] }
const normalizedMenu = {
  version: 2,
  settings: {},
  tags: [],
  groups: [{ slug: '_carta', name: null, categories: [{ slug: 'cafes', name: 'Cafés', show_title: true, items: [] }] }],
}

function memoryStorage(initial = {}) {
  const data = { ...initial }
  return {
    getItem: (key) => (key in data ? data[key] : null),
    setItem: (key, value) => { data[key] = value },
    data,
  }
}

const okFetch = (body) => async () => ({ ok: true, status: 200, json: async () => body })
const failingFetch = async () => { throw new Error('offline') }

describe('loadMenu', () => {
  it('descarga y cachea la carta', async () => {
    const storage = memoryStorage()
    const result = await loadMenu({ url: 'u', fetchImpl: okFetch(validMenu), storage })
    expect(result).toEqual({ menu: normalizedMenu, source: 'network' })
    expect(JSON.parse(storage.data[CACHE_KEY])).toEqual(normalizedMenu)
  })

  it('usa la caché si la red falla', async () => {
    const storage = memoryStorage({ [CACHE_KEY]: JSON.stringify(validMenu) })
    const result = await loadMenu({ url: 'u', fetchImpl: failingFetch, storage })
    expect(result).toEqual({ menu: normalizedMenu, source: 'cache' })
  })

  it('usa la caché si la respuesta es inválida', async () => {
    const storage = memoryStorage({ [CACHE_KEY]: JSON.stringify(validMenu) })
    const result = await loadMenu({ url: 'u', fetchImpl: okFetch({ version: 99 }), storage })
    expect(result.source).toBe('cache')
  })

  it('usa la caché ante un HTTP de error', async () => {
    const storage = memoryStorage({ [CACHE_KEY]: JSON.stringify(validMenu) })
    const notFound = async () => ({ ok: false, status: 404, json: async () => ({}) })
    expect((await loadMenu({ url: 'u', fetchImpl: notFound, storage })).source).toBe('cache')
  })

  it('falla si no hay red ni caché válida', async () => {
    const storage = memoryStorage({ [CACHE_KEY]: '{roto' })
    await expect(loadMenu({ url: 'u', fetchImpl: failingFetch, storage })).rejects.toBeInstanceOf(MenuUnavailableError)
  })

  it('corta la petición por timeout y usa la caché', async () => {
    const storage = memoryStorage({ [CACHE_KEY]: JSON.stringify(validMenu) })
    const hanging = (_url, { signal }) =>
      new Promise((_, reject) => signal.addEventListener('abort', () => reject(new Error('aborted'))))
    const result = await loadMenu({ url: 'u', fetchImpl: hanging, storage, timeoutMs: 20 })
    expect(result.source).toBe('cache')
  })

  it('sin url va directo a la caché o falla', async () => {
    await expect(loadMenu({ url: '', fetchImpl: okFetch(validMenu), storage: memoryStorage() })).rejects.toBeInstanceOf(MenuUnavailableError)
  })

  it('normaliza campos faltantes', async () => {
    const raw = { version: 1, categories: [{ slug: 'a', name: 'A', items: [{ id: 1, name: 'x' }] }, { slug: 'b', name: 'B' }] }
    const { menu } = await loadMenu({ url: 'u', fetchImpl: okFetch(raw), storage: null })
    expect(menu.tags).toEqual([])
    expect(menu.settings).toEqual({})
    expect(menu.groups[0].categories[0].items[0].tags).toEqual([])
    expect(menu.groups[0].categories[0].items[0].variants).toEqual([])
    expect(menu.groups[0].categories[1].items).toEqual([])
  })

  it('convierte un menú v1 en un único grupo sin título', async () => {
    const v1 = { version: 1, settings: {}, tags: [], categories: [{ slug: 'cafes', name: 'Cafés', items: [] }] }
    const { menu } = await loadMenu({ url: 'u', fetchImpl: okFetch(v1), storage: memoryStorage() })
    expect(menu.version).toBe(2)
    expect(menu.groups).toEqual([{ slug: '_carta', name: null, categories: [{ slug: 'cafes', name: 'Cafés', show_title: true, items: [] }] }])
  })

  it('acepta v2 y completa show_title', async () => {
    const v2 = { version: 2, groups: [{ slug: 'g', name: 'G', categories: [{ slug: 'c', name: 'C', items: [{ id: 1, name: 'X' }] }] }] }
    const { menu } = await loadMenu({ url: 'u', fetchImpl: okFetch(v2), storage: memoryStorage() })
    expect(menu.groups[0].categories[0].show_title).toBe(true)
    expect(menu.groups[0].categories[0].items[0].tags).toEqual([])
  })

  it('funciona sin storage disponible', async () => {
    const result = await loadMenu({ url: 'u', fetchImpl: okFetch(validMenu), storage: null })
    expect(result.source).toBe('network')
  })
})
