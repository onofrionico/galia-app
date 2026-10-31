import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const forbidden = (config) =>
  Promise.reject(Object.assign(new Error('403'), {
    config,
    response: { status: 403, data: { error: 'Acceso denegado' } },
  }))

describe('interceptor de 403', () => {
  let location
  let dispatched
  let api

  beforeEach(async () => {
    vi.resetModules()
    vi.useFakeTimers()
    vi.spyOn(console, 'error').mockImplementation(() => {})
    location = { pathname: '/sales', search: '', href: '/sales' }
    dispatched = []
    vi.stubGlobal('window', { location, dispatchEvent: (event) => dispatched.push(event) })
    vi.stubGlobal('localStorage', { getItem: () => 'token', removeItem: () => {} })
    api = (await import('./api')).default
    api.defaults.adapter = forbidden
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('no saca al usuario de la pantalla', async () => {
    await expect(api.get('/recurso')).rejects.toThrow('403')
    vi.advanceTimersByTime(10000)
    expect(location.href).toBe('/sales')
  })

  it('avisa del acceso denegado con el mensaje del backend', async () => {
    await expect(api.get('/recurso')).rejects.toThrow('403')
    expect(dispatched).toHaveLength(1)
    expect(dispatched[0].type).toBe('forbidden-access')
    expect(dispatched[0].detail.message).toBe('Acceso denegado')
  })
})
