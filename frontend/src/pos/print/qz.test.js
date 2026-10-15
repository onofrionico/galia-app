import { beforeEach, describe, expect, it, vi } from 'vitest'

// qz.websocket.isActive() da true también mientras el socket está CONECTANDO: no sirve para saber si se puede imprimir.
const socket = { active: false, closed: null, resolveConnect: null, rejectConnect: null }
const connect = vi.fn(() => {
  socket.active = true
  return new Promise((resolve, reject) => {
    socket.resolveConnect = resolve
    socket.rejectConnect = (error) => { socket.active = false; reject(error) }
  })
})

vi.mock('qz-tray', () => ({
  default: {
    security: { setCertificatePromise: vi.fn(), setSignatureAlgorithm: vi.fn(), setSignaturePromise: vi.fn() },
    websocket: {
      isActive: () => socket.active,
      connect: (...args) => connect(...args),
      setClosedCallbacks: (callback) => { socket.closed = callback },
    },
    configs: { create: vi.fn() },
    print: vi.fn(),
  },
}))
vi.mock('../api/posApi', () => ({ posPrintApi: { qzCertificate: vi.fn(), qzSign: vi.fn() } }))

const load = async () => {
  vi.resetModules()
  return import('./qz')
}

describe('conexión con QZ Tray', () => {
  beforeEach(() => {
    socket.active = false
    connect.mockClear()
  })

  it('no está lista mientras la conexión se está intentando', async () => {
    const { connectQz, qzReady } = await load()
    const pending = connectQz()
    expect(qzReady()).toBe(false)
    socket.resolveConnect()
    await pending
    expect(qzReady()).toBe(true)
  })

  it('dos pedidos de conexión simultáneos comparten el mismo intento', async () => {
    const { connectQz } = await load()
    const first = connectQz()
    const second = connectQz()
    expect(connect).toHaveBeenCalledTimes(1)
    socket.rejectConnect(new Error('Unable to establish connection with QZ'))
    await expect(first).rejects.toThrow()
    await expect(second).rejects.toThrow()
  })

  it('deja de estar lista cuando QZ Tray se cierra', async () => {
    const { connectQz, qzReady } = await load()
    const pending = connectQz()
    socket.resolveConnect()
    await pending
    socket.active = false
    socket.closed?.()
    expect(qzReady()).toBe(false)
  })
})
