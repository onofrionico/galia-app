import { describe, expect, it } from 'vitest'
import { connectivityReducer, initialConnectivity, pollEvent } from './connectivity'

const run = (events, state = initialConnectivity) => events.reduce(connectivityReducer, state)

describe('connectivityReducer', () => {
  it('arranca conectado', () => {
    expect(initialConnectivity.online).toBe(true)
  })

  it('un fallo de red no alcanza; dos seguidos pasan a sin conexión', () => {
    expect(run(['poll-network-error']).online).toBe(true)
    expect(run(['poll-network-error', 'poll-network-error']).online).toBe(false)
  })

  it('una respuesta HTTP con error no cuenta como falta de red y reinicia el contador', () => {
    expect(run(['poll-network-error', 'poll-http-error', 'poll-network-error']).online).toBe(true)
  })

  it('el evento offline corta de inmediato', () => {
    expect(run(['offline']).online).toBe(false)
  })

  it('online no reconecta solo: espera una consulta exitosa', () => {
    expect(run(['offline', 'online']).online).toBe(false)
    expect(run(['offline', 'online', 'poll-ok']).online).toBe(true)
    expect(run(['poll-network-error', 'poll-network-error', 'poll-ok'])).toEqual({ online: true, failures: 0 })
  })

  it('ignora eventos desconocidos', () => {
    expect(run(['otro'])).toEqual(initialConnectivity)
  })
})

describe('pollEvent', () => {
  it('clasifica el resultado de la consulta', () => {
    expect(pollEvent(true)).toBe('poll-ok')
    expect(pollEvent(false, { response: { status: 500 } })).toBe('poll-http-error')
    expect(pollEvent(false, new Error('Network Error'))).toBe('poll-network-error')
    expect(pollEvent(false)).toBe('poll-network-error')
  })
})
