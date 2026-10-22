import { describe, expect, it } from 'vitest'
import { canvasHeight, clampPosition, clampSize, fitScale, snap, tableStatus, tableSummary, tileLabel } from './floor'

describe('tableStatus', () => {
  it('libre, abierta o con cuenta pedida', () => {
    expect(tableStatus({ sales: [] })).toBe('free')
    expect(tableStatus({ sales: [{ status: 'open' }, { status: 'billing' }] })).toBe('open')
    expect(tableStatus({ sales: [{ status: 'billing' }] })).toBe('billing')
  })
})

describe('tableSummary', () => {
  it('suma las cuentas y toma la apertura más vieja', () => {
    const summary = tableSummary({
      sales: [
        { total: 1000.1, opened_at: '2026-10-10T12:30:00', waiter: { name: 'Ana' } },
        { total: 500.2, opened_at: '2026-10-10T12:00:00', waiter: { name: 'Juan' } },
      ],
    })
    expect(summary).toEqual({ count: 2, total: 1500.3, waiter: 'Ana', openedAt: '2026-10-10T12:00:00' })
  })
})

describe('geometría', () => {
  it('ajusta a la grilla sin negativos', () => {
    expect(snap(10.4)).toBe(10)
    expect(snap(-3)).toBe(0)
  })
  it('mantiene la mesa dentro del ancho lógico', () => {
    expect(clampPosition({ pos_x: 95, pos_y: -2, width: 10 })).toEqual({ pos_x: 90, pos_y: 0 })
    expect(clampSize({ pos_x: 90, width: 20, height: 1 })).toEqual({ width: 10, height: 4 })
  })
  it('el alto del lienzo crece con las mesas', () => {
    expect(canvasHeight([])).toBe(60)
    expect(canvasHeight([{ pos_y: 70, height: 10 }])).toBe(84)
  })
})

describe('tileLabel', () => {
  it('muestra el número si la mesa no tiene nombre y el nombre si lo tiene', () => {
    expect(tileLabel({ number: 12, name: null, label: 'Mesa 12' })).toBe('12')
    expect(tileLabel({ number: 1, name: 'Barra 1', label: 'Barra 1' })).toBe('Barra 1')
  })
})

describe('fitScale', () => {
  const tables = [{ pos_y: 0, height: 96 }] // canvasHeight = 100

  it('sin alto escala al ancho', () => {
    expect(fitScale(800, null, tables)).toBe(8)
  })
  it('en una pantalla apaisada lo limita el alto', () => {
    expect(fitScale(1600, 600, tables)).toBe(6)
  })
  it('en una pantalla angosta lo limita el ancho', () => {
    expect(fitScale(400, 900, tables)).toBe(4)
  })
})
