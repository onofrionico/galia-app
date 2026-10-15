import { describe, expect, it } from 'vitest'
import { formatMoney } from '../utils/money'
import { cuitIsValid, customerPayload, previewSummary, validateCustomer } from './invoiceForm'

const base = { mode: 'identified', docType: 'DNI', docNumber: '30.123.456', name: 'Ana', ivaCondition: 'consumidor_final', address: '' }

describe('cuitIsValid', () => {
  it('valida el dígito verificador', () => {
    expect(cuitIsValid('20123456786')).toBe(true)
    expect(cuitIsValid('20-12345678-6')).toBe(true)
    expect(cuitIsValid('20123456780')).toBe(false)
    expect(cuitIsValid('201234')).toBe(false)
  })
})

describe('validateCustomer', () => {
  it('acepta consumidor final y un DNI válido', () => {
    expect(validateCustomer({ mode: 'anonymous' })).toBeNull()
    expect(validateCustomer(base)).toBeNull()
  })
  it('rechaza datos incompletos o inválidos', () => {
    expect(validateCustomer({ ...base, docNumber: '123' })).toBe('El DNI tiene que tener 7 u 8 dígitos')
    expect(validateCustomer({ ...base, docType: 'CUIT', docNumber: '20-12345678-0' })).toBe('El CUIT es inválido')
    expect(validateCustomer({ ...base, name: ' ' })).toBe('Indicá el nombre o la razón social')
    expect(validateCustomer({ ...base, ivaCondition: 'monotributo' })).toBe('Para esa condición hace falta el CUIT')
  })
})

describe('customerPayload', () => {
  it('limpia el documento y devuelve null para consumidor final', () => {
    expect(customerPayload({ mode: 'anonymous' })).toBeNull()
    expect(customerPayload({ ...base, address: ' Calle 1 ' })).toEqual({
      doc_type: 'DNI', doc_number: '30123456', name: 'Ana', iva_condition: 'consumidor_final', address: 'Calle 1',
    })
  })
})

describe('previewSummary', () => {
  it('explica qué se factura', () => {
    expect(previewSummary({ amount: '18000.00', total: '18000.00', detail_mode: 'items' }))
      .toBe(`Se facturan los ítems · ${formatMoney(18000)}`)
    expect(previewSummary({ amount: '10000.00', total: '18000.00', detail_mode: 'generic' }))
      .toBe(`Se factura ${formatMoney(10000)} de ${formatMoney(18000)} (lo demás lo factura otro sistema)`)
    expect(previewSummary({ amount: '0.00', total: '18000.00', detail_mode: null }))
      .toBe('Todo lo cobrado en esta venta lo factura otro sistema')
  })
})
