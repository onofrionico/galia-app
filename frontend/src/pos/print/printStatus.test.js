import { describe, expect, it } from 'vitest'
import { jobLabel, printHealth } from './printStatus'

describe('printHealth', () => {
  it('clasifica el estado de la cola', () => {
    expect(printHealth(undefined)).toBe('unknown')
    expect(printHealth({ problems: [], points: [{ name: 'Caja', down: false }], pending: 0 })).toBe('ok')
    expect(printHealth({ problems: [], points: [{ name: 'Caja', down: false }], pending: 2 })).toBe('busy')
    expect(printHealth({ problems: [{ id: 1 }], points: [], pending: 1 })).toBe('alert')
    expect(printHealth({ problems: [], points: [{ name: 'Caja', down: true }], pending: 0 })).toBe('alert')
  })
})

describe('jobLabel', () => {
  it('describe el trabajo', () => {
    expect(jobLabel({ kind: 'order', station_name: 'Cocina', place: 'Mesa 1' })).toBe('Comanda · Cocina · Mesa 1')
    expect(jobLabel({ kind: 'bill', station_name: null, place: 'Mostrador #3' })).toBe('Precuenta · Caja · Mostrador #3')
    expect(jobLabel({ kind: 'test', station_name: null, place: null })).toBe('Prueba · Caja')
  })
})
