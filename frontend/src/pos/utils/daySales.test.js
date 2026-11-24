import { describe, expect, it } from 'vitest'
import { argentinaToday, daySummary, isToday, shiftDay } from './daySales'

describe('argentinaToday', () => {
  it('usa la fecha de Argentina (UTC-3), no la del reloj UTC', () => {
    expect(argentinaToday(new Date('2026-11-25T01:30:00Z'))).toBe('2026-11-24')
    expect(argentinaToday(new Date('2026-11-25T03:00:00Z'))).toBe('2026-11-25')
  })
})

describe('shiftDay', () => {
  it('avanza y retrocede días cruzando mes y año', () => {
    expect(shiftDay('2026-11-24', -1)).toBe('2026-11-23')
    expect(shiftDay('2026-12-31', 1)).toBe('2027-01-01')
    expect(shiftDay('2026-03-01', -1)).toBe('2026-02-28')
  })
})

describe('isToday', () => {
  it('compara contra el día de Argentina de ahora', () => {
    const now = new Date('2026-11-24T15:00:00Z')
    expect(isToday('2026-11-24', now)).toBe(true)
    expect(isToday('2026-11-23', now)).toBe(false)
  })
})

describe('daySummary', () => {
  it('cuenta las cerradas y suma lo cobrado sin las anuladas', () => {
    const sales = [
      { status: 'closed', total: 1000.5 },
      { status: 'closed', total: 500.25 },
      { status: 'cancelled', total: 9999 },
    ]
    expect(daySummary(sales)).toEqual({ closed: 2, cancelled: 1, total: 1500.75 })
  })

  it('sin ventas devuelve ceros', () => {
    expect(daySummary([])).toEqual({ closed: 0, cancelled: 0, total: 0 })
  })
})
