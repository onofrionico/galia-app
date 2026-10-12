import { describe, expect, it } from 'vitest'
import { pickSalonId } from './salons'

const salons = [{ id: 3, name: 'Salón' }, { id: 5, name: 'Patio' }]

describe('pickSalonId', () => {
  it('prefiere el salón de la URL si está activo', () => {
    expect(pickSalonId({ fromUrl: 5, saved: 3, salons })).toBe(5)
  })

  it('si no, el guardado en el dispositivo', () => {
    expect(pickSalonId({ fromUrl: null, saved: 5, salons })).toBe(5)
  })

  it('cae al primer salón activo si el pedido ya no existe', () => {
    expect(pickSalonId({ fromUrl: 99, saved: 98, salons })).toBe(3)
    expect(pickSalonId({ fromUrl: null, saved: null, salons })).toBe(3)
  })

  it('sin salones activos devuelve null', () => {
    expect(pickSalonId({ fromUrl: 5, saved: 3, salons: [] })).toBe(null)
  })
})
