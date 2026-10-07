import { describe, it, expect } from 'vitest'
import { loadMenu, CACHE_KEY, MenuUnavailableError } from './loadMenu'

const validMenu = { version: 1, settings: {}, tags: [], categories: [{ slug: 'cafes', name: 'Cafés', items: [] }] }

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
    expect(result).toEqual({ menu: validMenu, source: 'network' })
    expect(JSON.parse(storage.data[CACHE_KEY])).toEqual(validMenu)
  })

  it('usa la caché si la red falla', async () => {
    const storage = memoryStorage({ [CACHE_KEY]: JSON.stringify(validMenu) })
    const result = await loadMenu({ url: 'u', fetchImpl: failingFetch, storage })
    expect(result).toEqual({ menu: validMenu, source: 'cache' })
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
    expect(menu.categories[0].items[0].tags).toEqual([])
    expect(menu.categories[0].items[0].variants).toEqual([])
    expect(menu.categories[1].items).toEqual([])
  })

  it('funciona sin storage disponible', async () => {
    const result = await loadMenu({ url: 'u', fetchImpl: okFetch(validMenu), storage: null })
    expect(result.source).toBe('network')
  })
})
