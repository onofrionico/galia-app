import { describe, expect, it } from 'vitest'
import { addDays, formatUnits, groupByCategory, productName } from './productionForecast'

const products = [
  { key: 'v:1', producto: 'Café con leche', variante: 'Taza', categoria: 'Cafetería', total: 30 },
  { key: 'v:2', producto: 'Cortado', variante: null, categoria: 'Cafetería', total: 12 },
  { key: 'v:3', producto: 'Medialuna', variante: 'Unidad', categoria: 'Panadería', total: 40 },
]

describe('groupByCategory', () => {
  it('agrupa respetando el orden del backend', () => {
    const groups = groupByCategory(products, '')
    expect(groups.map((g) => g.categoria)).toEqual(['Cafetería', 'Panadería'])
    expect(groups[0].products.map((p) => p.key)).toEqual(['v:1', 'v:2'])
  })

  it('filtra por nombre sin distinguir mayúsculas ni tildes', () => {
    expect(groupByCategory(products, 'MEDI')[0].products[0].producto).toBe('Medialuna')
    expect(groupByCategory(products, 'cafe')[0].products.map((p) => p.key)).toEqual(['v:1'])
    expect(groupByCategory(products, 'zzz')).toEqual([])
  })
})

describe('formatUnits', () => {
  it('muestra enteros sin decimales y el resto con coma', () => {
    expect(formatUnits(40)).toBe('40')
    expect(formatUnits(23.5)).toBe('23,5')
    expect(formatUnits(0)).toBe('0')
  })
})

describe('productName', () => {
  it('agrega la variante salvo que sea vacía o Unidad', () => {
    expect(productName(products[0])).toBe('Café con leche (Taza)')
    expect(productName(products[1])).toBe('Cortado')
    expect(productName(products[2])).toBe('Medialuna')
  })
})

describe('addDays', () => {
  it('suma días a una fecha ISO sin pasar por UTC', () => {
    expect(addDays('2026-11-30', 1)).toBe('2026-12-01')
    expect(addDays('2026-03-01', -1)).toBe('2026-02-28')
  })
})
