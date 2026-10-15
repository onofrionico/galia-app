import { afterEach, describe, expect, it, vi } from 'vitest'
import { DEAD_PRINTER_ERROR, printByPrinter, shouldReconnect } from './printLoop'
import { startTicker } from './ticker'

const job = (id, printerId) => ({ id, printer: { id: printerId, name: `P${printerId}` } })

describe('printByPrinter', () => {
  it('una impresora caída no frena a las demás y sus trabajos restantes fallan sin esperar', async () => {
    const order = []
    let releaseKitchen
    const kitchenBlocked = new Promise((resolve) => { releaseKitchen = resolve })
    const printOne = vi.fn(async (j) => {
      order.push(`start ${j.id}`)
      if (j.printer.id === 1) {
        await kitchenBlocked
        throw new Error('timeout')
      }
      order.push(`done ${j.id}`)
    })
    const onFail = vi.fn()
    const run = printByPrinter([job(1, 1), job(2, 1), job(3, 2), job(4, 1), job(5, 2)], printOne, onFail)
    await new Promise((resolve) => setTimeout(resolve, 0))
    // La barra (impresora 2) imprime todo mientras la cocina sigue colgada.
    expect(order).toEqual(['start 1', 'start 3', 'done 3', 'start 5', 'done 5'])
    releaseKitchen()
    await run
    expect(printOne).toHaveBeenCalledTimes(3)
    expect(onFail.mock.calls.map(([j, message]) => [j.id, message])).toEqual([
      [1, 'timeout'], [2, DEAD_PRINTER_ERROR], [4, DEAD_PRINTER_ERROR],
    ])
  })
})

describe('shouldReconnect', () => {
  const base = { simulate: false, ready: false, lastAttemptAt: 0, now: 60_000 }
  it('reintenta la conexión con QZ cuando no está lista, respetando una espera', () => {
    expect(shouldReconnect(base)).toBe(true)
    expect(shouldReconnect({ ...base, lastAttemptAt: 55_000 })).toBe(false)
    expect(shouldReconnect({ ...base, ready: true })).toBe(false)
    expect(shouldReconnect({ ...base, simulate: true })).toBe(false)
  })
})

describe('startTicker', () => {
  afterEach(() => vi.useRealTimers())

  it('sin Web Worker usa setInterval y se puede detener', () => {
    vi.useFakeTimers()
    const tick = vi.fn()
    const stop = startTicker(tick, 2000)
    vi.advanceTimersByTime(6000)
    expect(tick).toHaveBeenCalledTimes(3)
    stop()
    vi.advanceTimersByTime(6000)
    expect(tick).toHaveBeenCalledTimes(3)
  })
})
