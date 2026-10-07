import { describe, it, expect } from 'vitest'
import { filterMenu } from './filterMenu'

const categories = [
  {
    slug: 'cafes',
    name: 'Cafés',
    items: [
      { id: 1, name: 'Café con leche', description: null, tags: [] },
      { id: 2, name: 'Latte', description: 'Con leche de almendras', tags: ['vegano'] },
    ],
  },
  {
    slug: 'tortas',
    name: 'Tortas',
    items: [{ id: 3, name: 'Torta Galia', description: 'Masa de nuez', tags: ['sin-tacc', 'vegano'] }],
  },
]

describe('filterMenu', () => {
  it('sin filtros devuelve todo', () => {
    expect(filterMenu(categories)).toEqual(categories)
  })

  it('busca sin tildes en nombre y descripción y oculta categorías vacías', () => {
    const result = filterMenu(categories, { query: 'CAFE' })
    expect(result.map((c) => c.slug)).toEqual(['cafes'])
    expect(result[0].items.map((i) => i.id)).toEqual([1])

    expect(filterMenu(categories, { query: 'almendras' })[0].items.map((i) => i.id)).toEqual([2])
  })

  it('combina etiquetas con Y', () => {
    expect(filterMenu(categories, { tagSlugs: ['vegano'] }).flatMap((c) => c.items.map((i) => i.id))).toEqual([2, 3])
    expect(filterMenu(categories, { tagSlugs: ['vegano', 'sin-tacc'] }).flatMap((c) => c.items.map((i) => i.id))).toEqual([3])
  })

  it('combina búsqueda y etiquetas', () => {
    expect(filterMenu(categories, { query: 'latte', tagSlugs: ['sin-tacc'] })).toEqual([])
  })
})
