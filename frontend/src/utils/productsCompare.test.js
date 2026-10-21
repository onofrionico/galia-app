import { describe, expect, it } from 'vitest'
import { barWidths, defaultMonths, rankProducts, variation } from './productsCompare'

const products = [
  { key: 'p:1', name: 'Medialuna', a: { quantity: '100.000', amount: '90000.00' }, b: { quantity: '120.000', amount: '108000.00' } },
  { key: 'p:2', name: 'Latte', a: { quantity: '50.000', amount: '175000.00' }, b: { quantity: '40.000', amount: '140000.00' } },
  { key: 'n:Torta', name: 'Torta', a: { quantity: '0.000', amount: '0.00' }, b: { quantity: '40.000', amount: '200000.00' } },
]

describe('productsCompare', () => {
  it('ordena por el mes B según la medida', () => {
    expect(rankProducts(products, 'amount').map((p) => p.key)).toEqual(['n:Torta', 'p:2', 'p:1'])
    expect(rankProducts(products, 'quantity').map((p) => p.key)).toEqual(['p:1', 'p:2', 'n:Torta'])
  })
  it('a igualdad ordena por nombre', () => {
    const tied = [{ ...products[1], b: { quantity: '1', amount: '10' } }, { ...products[0], b: { quantity: '1', amount: '10' } }]
    expect(rankProducts(tied, 'amount').map((p) => p.name)).toEqual(['Latte', 'Medialuna'])
  })
  it('calcula la variación', () => {
    expect(variation(100, 121)).toBe(21)
    expect(variation('100.00', '80.00')).toBe(-20)
    expect(variation(0, 5)).toBeNull()
  })
  it('escala las barras al máximo de los dos meses', () => {
    const widths = barWidths(products, 'amount')
    expect(Math.max(...widths.flatMap((w) => [w.a, w.b]))).toBe(100)
    expect(widths.find((w) => w.key === 'n:Torta').a).toBe(0)
    expect(barWidths([], 'amount')).toEqual([])
  })
  it('propone el mes anterior y el actual', () => {
    expect(defaultMonths(new Date('2026-10-20T12:00:00'))).toEqual(['2026-09', '2026-10'])
    expect(defaultMonths(new Date('2026-01-05T12:00:00'))).toEqual(['2025-12', '2026-01'])
  })
})
