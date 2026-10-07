import { describe, it, expect } from 'vitest'
import { activeSectionIndex } from './activeSection'

describe('activeSectionIndex', () => {
  it('devuelve la última sección cuyo top <= umbral', () => {
    expect(activeSectionIndex([-500, -100, 50, 400], 100)).toBe(2)
  })
  it('incluye el borde del umbral', () => {
    expect(activeSectionIndex([-10, 100, 300], 100)).toBe(1)
  })
  it('devuelve 0 si ninguna califica', () => {
    expect(activeSectionIndex([200, 500], 100)).toBe(0)
  })
  it('devuelve 0 con lista vacía', () => {
    expect(activeSectionIndex([], 100)).toBe(0)
  })
})
