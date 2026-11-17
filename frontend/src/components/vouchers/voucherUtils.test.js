import { describe, expect, it } from 'vitest'
import { PRINT_CSS, STATUS_LABEL, availableKey, chunk, formatExpiry, printKey } from './voucherUtils'

describe('PRINT_CSS', () => {
  it('oculta la app con display:none para no imprimir páginas en blanco', () => {
    expect(PRINT_CSS).toContain('#root { display: none')
    expect(PRINT_CSS).not.toContain('visibility: hidden')
  })
  it('fuerza los colores de fondo de la marca al imprimir', () => {
    expect(PRINT_CSS).toContain('print-color-adjust: exact')
  })
  it('corta la página después de cada hoja de 8', () => {
    expect(PRINT_CSS).toContain('break-after: page')
  })
})

describe('availableKey', () => {
  it('cambia cuando cambian los vouchers disponibles, no solo su cantidad', () => {
    const vouchers = (ids) => ids.map((id) => ({ id, status: 'available' }))
    expect(availableKey({ vouchers: vouchers([1, 2]) })).toBe('1,2')
    expect(availableKey({ vouchers: vouchers([1, 3]) })).not.toBe(availableKey({ vouchers: vouchers([1, 2]) }))
    expect(availableKey({ vouchers: [{ id: 1, status: 'redeemed' }] })).toBe('')
  })
})

describe('printKey', () => {
  const batch = { vouchers: [{ id: 1, status: 'available' }] }
  it('cambia si se agrega o se quita el dorso', () => {
    expect(printKey(batch, true)).not.toBe(printKey(batch, false))
  })
  it('queda vacío si no hay nada para imprimir', () => {
    expect(printKey({ vouchers: [{ id: 1, status: 'redeemed' }] }, true)).toBe('')
  })
})

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
