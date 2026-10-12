import { describe, expect, it } from 'vitest'
import { changeFor, quickTenders } from './change'

describe('changeFor', () => {
  it('calcula el vuelto', () => {
    expect(changeFor(11900, 15000)).toBe(3100)
  })
  it('devuelve null si lo recibido no alcanza o falta', () => {
    expect(changeFor(11900, 10000)).toBeNull()
    expect(changeFor(11900, NaN)).toBeNull()
  })
})

describe('quickTenders', () => {
  it('ofrece el monto justo y redondeos hacia arriba sin repetir', () => {
    expect(quickTenders(11900)).toEqual([11900, 12000, 15000, 20000])
    expect(quickTenders(15000)).toEqual([15000, 20000])
  })
  it('no ofrece nada sin monto', () => {
    expect(quickTenders(0)).toEqual([])
  })
})
