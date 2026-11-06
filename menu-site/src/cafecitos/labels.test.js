import { describe, expect, it } from 'vitest'
import { reachable } from './labels'

const cafe = { name: 'Café', cost: 8 }
const focaccia = { name: 'Focaccia', cost: 10 }
const torta = { name: 'Torta', cost: 16 }

describe('reachable', () => {
  it('separa lo que alcanza de lo que falta', () => {
    expect(reachable(14, [cafe, focaccia, torta])).toEqual({
      available: [cafe, focaccia],
      next: [{ reward: torta, missing: 2 }],
    })
  })
  it('sin saldo nada alcanza', () => {
    expect(reachable(0, [cafe]).available).toEqual([])
  })
})
