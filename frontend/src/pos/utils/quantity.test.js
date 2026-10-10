import { describe, expect, it } from 'vitest'
import { stepQuantity } from './quantity'

describe('stepQuantity', () => {
  it('suma y resta de a uno dentro del rango', () => {
    expect(stepQuantity(0, 2, 1)).toBe(1)
    expect(stepQuantity(2, 2, 1)).toBe(2)
    expect(stepQuantity(1, 2, -1)).toBe(0)
    expect(stepQuantity(0, 2, -1)).toBe(0)
  })
  it('con cantidades no enteras llega al máximo', () => {
    expect(stepQuantity(2, 2.5, 1)).toBe(2.5)
  })
})
