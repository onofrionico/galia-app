import { describe, it, expect } from 'vitest'
import { filterMenu } from './filterMenu'

const groups = [
  { slug: 'g1', name: 'Desayuno', categories: [
    { slug: 'cafes', name: 'Cafés', items: [
      { id: 1, name: 'Café con leche', description: null, tags: [] },
      { id: 2, name: 'Latte', description: 'Con leche de almendras', tags: ['vegano'] },
    ] },
  ] },
  { slug: 'g2', name: 'Dulces', categories: [
    { slug: 'tortas', name: 'Tortas', items: [{ id: 3, name: 'Torta Galia', description: 'Masa de nuez', tags: ['sin-tacc', 'vegano'] }] },
  ] },
]
const ids = (result) => result.flatMap((g) => g.categories.flatMap((c) => c.items.map((i) => i.id)))

describe('filterMenu', () => {
  it('sin filtros devuelve todo', () => {
    expect(filterMenu(groups)).toEqual(groups)
  })

  it('busca sin tildes en nombre y descripción y oculta categorías y grupos vacíos', () => {
    const result = filterMenu(groups, { query: 'CAFE' })
    expect(result.map((g) => g.slug)).toEqual(['g1'])
    expect(result[0].categories.map((c) => c.slug)).toEqual(['cafes'])
    expect(ids(result)).toEqual([1])
    expect(ids(filterMenu(groups, { query: 'almendras' }))).toEqual([2])
  })

  it('combina etiquetas con Y', () => {
    expect(ids(filterMenu(groups, { tagSlugs: ['vegano'] }))).toEqual([2, 3])
    expect(ids(filterMenu(groups, { tagSlugs: ['vegano', 'sin-tacc'] }))).toEqual([3])
  })

  it('combina búsqueda y etiquetas', () => {
    expect(filterMenu(groups, { query: 'latte', tagSlugs: ['sin-tacc'] })).toEqual([])
  })
})
