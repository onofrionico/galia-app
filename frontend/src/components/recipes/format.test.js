import { formatStepTime, formatQuantity, formatYield } from './format'

describe('formatStepTime', () => {
  it('formats a single time', () => {
    expect(formatStepTime(12, null)).toBe('12 min')
    expect(formatStepTime(null, 12)).toBe('12 min')
    expect(formatStepTime(12, 12)).toBe('12 min')
  })
  it('formats a range', () => {
    expect(formatStepTime(10, 12)).toBe('10–12 min')
  })
  it('formats hours', () => {
    expect(formatStepTime(75, null)).toBe('1 h 15 min')
    expect(formatStepTime(60, null)).toBe('1 h')
  })
  it('is empty when both are null', () => {
    expect(formatStepTime(null, null)).toBe('')
    expect(formatStepTime(undefined, undefined)).toBe('')
  })
})

describe('formatQuantity', () => {
  it('joins quantity and unit', () => {
    expect(formatQuantity(250, 'g', null)).toBe('250 g')
    expect(formatQuantity(0.5, 'kg', null)).toBe('0,5 kg')
  })
  it('pluralizes unidad', () => {
    expect(formatQuantity(2, 'unidad', null)).toBe('2 unidades')
    expect(formatQuantity(1, 'unidad', null)).toBe('1 unidad')
  })
  it('uses the note when there is no quantity', () => {
    expect(formatQuantity(null, null, 'pizca')).toBe('pizca')
  })
  it('asks to complete when nothing is known', () => {
    expect(formatQuantity(null, null, null)).toBe('a completar')
    expect(formatQuantity(null, 'g', '')).toBe('a completar')
  })
})

describe('formatYield', () => {
  it('formats yield', () => {
    expect(formatYield(12, 'unidad')).toBe('12 unidades')
    expect(formatYield(1.5, 'kg')).toBe('1,5 kg')
  })
  it('is empty without yield', () => {
    expect(formatYield(null, null)).toBe('')
  })
})
