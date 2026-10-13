import { describe, expect, it } from 'vitest'
import { cashChanged, keysToInvalidate, rememberEventIds, unseenChanges } from './changes'

describe('keysToInvalidate', () => {
  it('sin cambios no invalida nada', () => {
    expect(keysToInvalidate({ last_event_id: 5, sales: [] })).toEqual([])
    expect(keysToInvalidate(null)).toEqual([])
  })
  it('con reset invalida todo el POS', () => {
    expect(keysToInvalidate({ last_event_id: 9, reset: true, sales: [] })).toEqual([['pos']])
  })
  it('invalida cada venta, el plano y el mostrador según el tipo', () => {
    const keys = keysToInvalidate({
      last_event_id: 7,
      sales: [{ id: 3, sale_type: 'salon' }, { id: 4, sale_type: 'counter' }],
    })
    expect(keys).toEqual([
      ['pos', 'sale', 3], ['pos', 'events', 3], ['pos', 'sale', 4], ['pos', 'events', 4],
      ['pos', 'floor'], ['pos', 'sales'], ['pos', 'cash', 'session'],
    ])
  })
  it('con ventas cambiadas refresca las sesiones de caja (cobros y anulaciones)', () => {
    const keys = keysToInvalidate({ last_event_id: 8, sales: [{ id: 6, sale_type: 'counter' }] })
    expect(keys).toContainEqual(['pos', 'cash', 'session'])
    expect(keysToInvalidate({ last_event_id: 8, sales: [] })).not.toContainEqual(['pos', 'cash', 'session'])
  })
})

describe('unseenChanges', () => {
  it('descarta las ventas cuyos eventos ya se vieron', () => {
    const seen = new Set([10, 11, 12])
    const response = {
      last_event_id: 13,
      event_ids: [10, 11, 12, 13],
      sales: [{ id: 3, sale_type: 'salon', event_ids: [10, 12] }, { id: 4, sale_type: 'counter', event_ids: [11, 13] }],
    }
    expect(unseenChanges(response, seen).sales.map((s) => s.id)).toEqual([4])
    expect(keysToInvalidate(unseenChanges(response, new Set([10, 11, 12, 13])))).toEqual([])
  })
  it('un id nuevo menor que last_event_id igual invalida su venta', () => {
    const seen = new Set([10, 12])
    const response = {
      last_event_id: 12,
      event_ids: [10, 11, 12],
      sales: [{ id: 3, sale_type: 'salon', event_ids: [10, 12] }, { id: 5, sale_type: 'salon', event_ids: [11] }],
    }
    const filtered = unseenChanges(response, seen)
    expect(filtered.sales.map((s) => s.id)).toEqual([5])
    expect(keysToInvalidate(filtered)).toEqual([['pos', 'sale', 5], ['pos', 'events', 5], ['pos', 'floor'], ['pos', 'cash', 'session']])
  })
  it('respeta reset y ventas sin event_ids (backend viejo)', () => {
    const reset = { last_event_id: 9, reset: true, sales: [] }
    expect(unseenChanges(reset, new Set([1]))).toBe(reset)
    const legacy = { last_event_id: 9, sales: [{ id: 3, sale_type: 'salon' }] }
    expect(unseenChanges(legacy, new Set([9])).sales.map((s) => s.id)).toEqual([3])
  })
})

describe('cashChanged', () => {
  it('detecta cambios de versión de caja, salvo en la primera lectura', () => {
    expect(cashChanged(null, 3)).toBe(false)
    expect(cashChanged(3, 3)).toBe(false)
    expect(cashChanged(3, 4)).toBe(true)
    expect(cashChanged(3, undefined)).toBe(false)
  })
})

describe('rememberEventIds', () => {
  it('agrega los ids y conserva solo los más altos', () => {
    const seen = rememberEventIds(new Set([1, 2]), [3, 4], 3)
    expect([...seen].sort((a, b) => a - b)).toEqual([2, 3, 4])
  })
  it('sin ids devuelve el mismo conjunto', () => {
    const seen = new Set([1])
    expect(rememberEventIds(seen, undefined)).toBe(seen)
  })
})
