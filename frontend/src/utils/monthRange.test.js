import { describe, expect, it } from 'vitest'
import { currentMonthRange, monthRangeOf, periodRange, shiftMonth } from './monthRange'

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

describe('monthRangeOf', () => {
  it('devuelve el rango de un mes dado por año y mes (1-12)', () => {
    expect(monthRangeOf({ year: 2026, month: 2 })).toEqual({ from: '2026-02-01', to: '2026-02-28' })
  })
})

describe('shiftMonth', () => {
  it('avanza y retrocede cruzando el año', () => {
    expect(shiftMonth({ year: 2026, month: 12 }, 1)).toEqual({ year: 2027, month: 1 })
    expect(shiftMonth({ year: 2026, month: 1 }, -1)).toEqual({ year: 2025, month: 12 })
    expect(shiftMonth({ year: 2026, month: 11 }, -1)).toEqual({ year: 2026, month: 10 })
  })
})

describe('periodRange', () => {
  const wed = new Date(2026, 10, 25) // miércoles 25/11/2026

  it('hoy', () => {
    expect(periodRange('diario', wed)).toEqual({ from: '2026-11-25', to: '2026-11-25' })
  })

  it('esta semana va de lunes a domingo', () => {
    expect(periodRange('semanal', wed)).toEqual({ from: '2026-11-23', to: '2026-11-29' })
    expect(periodRange('semanal', new Date(2026, 10, 29))).toEqual({ from: '2026-11-23', to: '2026-11-29' })
  })

  it('este mes, este trimestre y este año', () => {
    expect(periodRange('mensual', wed)).toEqual({ from: '2026-11-01', to: '2026-11-30' })
    expect(periodRange('trimestral', wed)).toEqual({ from: '2026-10-01', to: '2026-12-31' })
    expect(periodRange('anual', wed)).toEqual({ from: '2026-01-01', to: '2026-12-31' })
  })
})
