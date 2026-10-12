import { describe, expect, it } from 'vitest'
import { applyKey } from './keypad'

describe('applyKey', () => {
  it('la primera tecla reemplaza el valor sugerido', () => {
    expect(applyKey('11900', '5', true)).toBe('5')
    expect(applyKey('11900', ',', true)).toBe('0,')
    expect(applyKey('11900', 'back', true)).toBe('')
  })
  it('después agrega dígitos', () => {
    expect(applyKey('15', '0', false)).toBe('150')
    expect(applyKey('0', '7', false)).toBe('7')
  })
  it('acepta una sola coma y hasta dos decimales', () => {
    expect(applyKey('15', ',', false)).toBe('15,')
    expect(applyKey('15,5', ',', false)).toBe('15,5')
    expect(applyKey('15,55', '1', false)).toBe('15,55')
  })
  it('borra el último carácter', () => {
    expect(applyKey('150', 'back', false)).toBe('15')
  })
})
