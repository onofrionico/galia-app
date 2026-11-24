import { describe, expect, it } from 'vitest'
import { currentMonthRange } from './monthRange'

describe('currentMonthRange', () => {
  it('devuelve el primer y el último día del mes de la fecha dada', () => {
    expect(currentMonthRange(new Date(2026, 10, 24))).toEqual({ from: '2026-11-01', to: '2026-11-30' })
  })

  it('respeta meses de 31 días y febrero bisiesto', () => {
    expect(currentMonthRange(new Date(2026, 11, 5))).toEqual({ from: '2026-12-01', to: '2026-12-31' })
    expect(currentMonthRange(new Date(2028, 1, 10))).toEqual({ from: '2028-02-01', to: '2028-02-29' })
  })

  it('usa la fecha local, sin desfase por UTC, el último día del mes a la noche', () => {
    expect(currentMonthRange(new Date(2026, 10, 30, 23, 30))).toEqual({ from: '2026-11-01', to: '2026-11-30' })
  })
})
