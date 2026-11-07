import { describe, expect, it } from 'vitest'
import { monthRange, reportsUrl } from './loyaltyService'

describe('reportsUrl', () => {
  it('arma la URL con el rango', () => {
    expect(reportsUrl('redemptions', { from: '2026-11-01', to: '2026-11-30' }))
      .toBe('/api/v1/loyalty/admin/reports/redemptions?from=2026-11-01&to=2026-11-30')
  })
  it('sin rango no agrega querystring', () => {
    expect(reportsUrl('active')).toBe('/api/v1/loyalty/admin/reports/active')
  })
})

describe('monthRange', () => {
  it('primer y último día del mes', () => {
    expect(monthRange('2026-02')).toEqual({ from: '2026-02-01', to: '2026-02-28' })
    expect(monthRange('2028-02')).toEqual({ from: '2028-02-01', to: '2028-02-29' })
    expect(monthRange('2026-12')).toEqual({ from: '2026-12-01', to: '2026-12-31' })
  })
})
