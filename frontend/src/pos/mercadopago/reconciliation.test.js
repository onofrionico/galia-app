import { describe, expect, it } from 'vitest'
import { channelLabel, monthDays, statusLabel } from './reconciliation'

describe('reconciliation', () => {
  it('etiquetas', () => {
    expect(statusLabel('conciliado')).toBe('Conciliado')
    expect(statusLabel('con_diferencias')).toBe('Con diferencias')
    expect(statusLabel('sin_traer')).toBe('Sin traer')
    expect(channelLabel('point')).toBe('Point')
    expect(channelLabel('transfer')).toBe('Transferencia')
    expect(channelLabel('raro')).toBe('Otro')
  })
  it('días del mes', () => {
    const days = monthDays(2026, 2)
    expect(days[0]).toBe('2026-02-01')
    expect(days.at(-1)).toBe('2026-02-28')
  })
})
