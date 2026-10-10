import { describe, expect, it } from 'vitest'
import { keysToInvalidate } from './changes'

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
      ['pos', 'floor'], ['pos', 'sales'],
    ])
  })
})
