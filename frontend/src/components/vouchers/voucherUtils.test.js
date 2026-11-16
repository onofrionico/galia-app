import { describe, expect, it } from 'vitest'
import { STATUS_LABEL, chunk, formatExpiry } from './voucherUtils'

describe('chunk', () => {
  it('arma páginas de 8', () => {
    const pages = chunk([1, 2, 3, 4, 5, 6, 7, 8, 9], 8)
    expect(pages).toEqual([[1, 2, 3, 4, 5, 6, 7, 8], [9]])
  })
  it('devuelve una lista vacía si no hay elementos', () => {
    expect(chunk([], 8)).toEqual([])
  })
})

describe('formatExpiry', () => {
  it('muestra DD/MM/AAAA', () => {
    expect(formatExpiry('2026-12-31')).toBe('31/12/2026')
  })
  it('tolera un valor vacío', () => {
    expect(formatExpiry(null)).toBe('—')
  })
})

describe('STATUS_LABEL', () => {
  it('cubre los cinco estados', () => {
    expect(STATUS_LABEL).toEqual({
      available: 'Disponible', in_use: 'En uso', redeemed: 'Canjeado', expired: 'Vencido', voided: 'Anulado',
    })
  })
})
