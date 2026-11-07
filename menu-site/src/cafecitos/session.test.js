import { afterEach, describe, expect, it } from 'vitest'
import { clearToken, getToken, setToken } from './session'

const original = globalThis.localStorage

afterEach(() => {
  globalThis.localStorage = original
  clearToken()
})

describe('session', () => {
  it('guarda y lee el token en localStorage', () => {
    const store = {}
    globalThis.localStorage = {
      getItem: (k) => (k in store ? store[k] : null),
      setItem: (k, v) => { store[k] = v },
      removeItem: (k) => { delete store[k] },
    }
    setToken('abc')
    expect(store['galia.cafecitos.token']).toBe('abc')
    expect(getToken()).toBe('abc')
    clearToken()
    expect(getToken()).toBe(null)
  })
  it('sigue funcionando en memoria si localStorage tira error', () => {
    globalThis.localStorage = {
      getItem: () => { throw new Error('bloqueado') },
      setItem: () => { throw new Error('bloqueado') },
      removeItem: () => { throw new Error('bloqueado') },
    }
    setToken('xyz')
    expect(getToken()).toBe('xyz')
    clearToken()
    expect(getToken()).toBe(null)
  })
})
