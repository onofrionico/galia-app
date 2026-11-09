import { describe, it, expect } from 'vitest'
import { flowerByCategory } from './categoryFlower'

const groups = [
  { slug: 'cafeteria', categories: [{ slug: 'cafe' }, { slug: 'bebidas' }] },
  { slug: 'pasteleria', categories: [{ slug: 'tortas' }] },
]

describe('flowerByCategory', () => {
  it('alterna las flores siguiendo el orden de la carta, a través de los grupos', () => {
    expect(flowerByCategory(groups)).toEqual({
      cafe: '/brand/flower-coral.png',
      bebidas: '/brand/flower-lime.png',
      tortas: '/brand/flower-coral.png',
    })
  })

  it('devuelve vacío si la carta no tiene grupos', () => {
    expect(flowerByCategory([])).toEqual({})
  })
})
