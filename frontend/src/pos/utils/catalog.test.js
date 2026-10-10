import { describe, expect, it } from 'vitest'
import { addedSummary, filterProducts, needsDetail, normalize, priceLabel } from './catalog'

const products = [
  { id: 1, name: 'Latte', category_id: 1, variants: [{ id: 10, price: 3500 }, { id: 11, price: 4200 }], modifier_groups: [] },
  { id: 2, name: 'Café con leche', category_id: 1, variants: [{ id: 20, price: 3000 }], modifier_groups: [{ id: 5 }] },
  { id: 3, name: 'Medialuna', category_id: 2, variants: [{ id: 30, price: 900 }], modifier_groups: [] },
]
const plain = (text) => text.replace(/\s/g, ' ')

describe('catálogo', () => {
  it('normaliza acentos y mayúsculas', () => {
    expect(normalize('  CAFÉ ')).toBe('cafe')
  })
  it('filtra por texto y categoría', () => {
    expect(filterProducts(products, { query: 'cafe' }).map((p) => p.id)).toEqual([2])
    expect(filterProducts(products, { categoryId: 2 }).map((p) => p.id)).toEqual([3])
    expect(filterProducts(products, {}).length).toBe(3)
  })
  it('muestra el precio o "desde"', () => {
    expect(plain(priceLabel(products[2]))).toBe('$ 900')
    expect(plain(priceLabel(products[0]))).toBe('desde $ 3.500')
  })
  it('pide detalle si hay variantes o modificadores', () => {
    expect(products.map(needsDetail)).toEqual([true, true, false])
  })
  it('resume lo agregado', () => {
    expect(addedSummary([])).toBe('')
    expect(addedSummary([{ name: 'Latte', quantity: 1 }, { name: 'Medialuna', quantity: 1 }, { name: 'Latte', quantity: 1 }]))
      .toBe('3 agregados: 2 Latte, 1 Medialuna')
  })
})
