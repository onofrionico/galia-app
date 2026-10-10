import { describe, expect, it } from 'vitest'
import { elapsedLabel, parseServerDate } from './time'

describe('parseServerDate', () => {
  it('interpreta las fechas sin zona del backend como UTC', () => {
    expect(parseServerDate('2026-10-10T12:00:00').toISOString()).toBe('2026-10-10T12:00:00.000Z')
    expect(parseServerDate('2026-10-10T12:00:00+00:00').toISOString()).toBe('2026-10-10T12:00:00.000Z')
    expect(parseServerDate(null)).toBeNull()
  })
})

describe('elapsedLabel', () => {
  const now = new Date('2026-10-10T13:05:00Z')
  it('muestra minutos y horas', () => {
    expect(elapsedLabel('2026-10-10T13:00:00', now)).toBe('5 min')
    expect(elapsedLabel('2026-10-10T11:00:00', now)).toBe('2 h 05')
    expect(elapsedLabel(null, now)).toBe('')
  })
})
