import { describe, expect, it } from 'vitest'
import { amountToText, discountLabel, formatMoney, formatQuantity, parseAmount, round2 } from './money'

const plain = (text) => text.replace(/\s/g, ' ')

describe('formatMoney', () => {
  it('formatea pesos sin decimales cuando el monto es entero', () => {
    expect(plain(formatMoney(1500))).toBe('$ 1.500')
  })
  it('muestra dos decimales cuando hay centavos', () => {
    expect(plain(formatMoney(1500.5))).toBe('$ 1.500,50')
  })
  it('trata null como cero', () => {
    expect(plain(formatMoney(null))).toBe('$ 0')
  })
})

describe('parseAmount', () => {
  it('ignora puntos de miles y usa coma decimal', () => {
    expect(parseAmount('1.500')).toBe(1500)
    expect(parseAmount('1500,5')).toBe(1500.5)
    expect(parseAmount('$ 2.000,25')).toBe(2000.25)
  })
  it('devuelve NaN si no hay número', () => {
    expect(parseAmount('')).toBeNaN()
    expect(parseAmount('abc')).toBeNaN()
  })
})

describe('amountToText', () => {
  it('es la inversa de parseAmount', () => {
    expect(amountToText(11900)).toBe('11900')
    expect(amountToText(11900.5)).toBe('11900,50')
    expect(parseAmount(amountToText(11900.5))).toBe(11900.5)
  })
})

describe('otros formatos', () => {
  it('redondea a dos decimales', () => {
    expect(round2(0.1 + 0.2)).toBe(0.3)
  })
  it('formatea cantidades', () => {
    expect(formatQuantity(2)).toBe('2')
    expect(formatQuantity(1.5)).toBe('1,5')
  })
  it('describe un descuento', () => {
    expect(discountLabel({ kind: 'percent', value: 20 })).toBe('20%')
    expect(plain(discountLabel({ kind: 'amount', value: 500 }))).toBe('$ 500')
  })
})
