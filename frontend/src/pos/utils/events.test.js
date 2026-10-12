import { describe, expect, it } from 'vitest'
import { eventDetail, eventLabel } from './events'

const plain = (text) => text.replace(/\s/g, ' ')

describe('eventos', () => {
  it('traduce el tipo', () => {
    expect(eventLabel('item_cancelled')).toBe('Anuló un ítem')
    expect(eventLabel('desconocido')).toBe('desconocido')
  })
  it('arma el detalle', () => {
    expect(eventDetail({ payload: { product: 'Latte', quantity: '2.000' } })).toBe('2 × Latte')
    expect(plain(eventDetail({ payload: { method: 'Efectivo', amount: '1500.00' } }))).toBe('Efectivo · $ 1.500')
    expect(eventDetail({ payload: { reason: 'Error de carga' } })).toBe('Motivo: Error de carga')
    expect(eventDetail({ payload: {} })).toBe('')
  })
})
