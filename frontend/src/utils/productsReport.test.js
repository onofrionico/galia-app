import { describe, expect, it } from 'vitest'
import { coverageLevel, filterAndSortProducts, nextSort, productLabel } from './productsReport'

const products = [
  { producto: 'Cortado', variante: 'Taza', categoria: 'Cafetería', facturacion: 8000, unidades: 4, variacion: 10 },
  { producto: 'Medialuna', variante: null, categoria: 'Panadería', facturacion: 2000, unidades: 6, variacion: null },
  { producto: 'Café con leche', variante: null, categoria: 'Cafetería', facturacion: 3000, unidades: 2, variacion: -5 },
]

describe('filterAndSortProducts', () => {
  it('sorts by revenue descending by default', () => {
    expect(filterAndSortProducts(products).map((p) => p.producto)).toEqual(['Cortado', 'Café con leche', 'Medialuna'])
  })
  it('searches ignoring accents and case across name and category', () => {
    expect(filterAndSortProducts(products, { query: 'cafe' }).map((p) => p.producto)).toEqual(['Cortado', 'Café con leche'])
    expect(filterAndSortProducts(products, { query: 'TAZA' }).map((p) => p.producto)).toEqual(['Cortado'])
  })
  it('filters by category', () => {
    expect(filterAndSortProducts(products, { category: 'Panadería' })).toHaveLength(1)
  })
  it('keeps missing values last in either direction', () => {
    const asc = filterAndSortProducts(products, { sortKey: 'variacion', sortDir: 'asc' })
    const desc = filterAndSortProducts(products, { sortKey: 'variacion', sortDir: 'desc' })
    expect(asc.map((p) => p.variacion)).toEqual([-5, 10, null])
    expect(desc.map((p) => p.variacion)).toEqual([10, -5, null])
  })
  it('sorts names alphabetically including the variant', () => {
    expect(filterAndSortProducts(products, { sortKey: 'producto', sortDir: 'asc' }).map(productLabel))
      .toEqual(['Café con leche', 'Cortado (Taza)', 'Medialuna'])
  })
})

describe('coverageLevel', () => {
  it('classifies coverage', () => {
    expect(coverageLevel(100)).toBe('ok')
    expect(coverageLevel(80)).toBe('partial')
    expect(coverageLevel(10)).toBe('low')
  })
})

describe('nextSort', () => {
  it('toggles direction on the same column and resets on a new one', () => {
    expect(nextSort({ sortKey: 'facturacion', sortDir: 'desc' }, 'facturacion')).toEqual({ sortKey: 'facturacion', sortDir: 'asc' })
    expect(nextSort({ sortKey: 'facturacion', sortDir: 'asc' }, 'unidades')).toEqual({ sortKey: 'unidades', sortDir: 'desc' })
    expect(nextSort({ sortKey: 'facturacion', sortDir: 'desc' }, 'producto')).toEqual({ sortKey: 'producto', sortDir: 'asc' })
  })
})
