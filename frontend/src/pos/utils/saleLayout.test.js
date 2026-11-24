import { describe, expect, it } from 'vitest'
import { footerChips, itemButtons } from './saleLayout'

describe('footerChips', () => {
  it('con todo habilitado devuelve las 6 acciones en orden y solo anular es peligrosa', () => {
    const all = { discount: true, printBill: true, move: true, split: true, close: true, cancelSale: true }
    const chips = footerChips(all)
    expect(chips.map((c) => c.key)).toEqual(['discount', 'printBill', 'move', 'split', 'close', 'cancelSale'])
    expect(chips.map((c) => c.label)).toEqual([
      'Descuento', 'Precuenta', 'Mover de mesa', 'Dividir la cuenta', 'Cerrar con saldo 0', 'Anular la venta',
    ])
    expect(chips.filter((c) => c.danger).map((c) => c.key)).toEqual(['cancelSale'])
  })

  it('sin acciones habilitadas devuelve una lista vacía', () => {
    expect(footerChips({})).toEqual([])
  })

  it('omite las deshabilitadas', () => {
    expect(footerChips({ cancelSale: false, split: true }).map((c) => c.key)).toEqual(['split'])
  })
})

describe('itemButtons', () => {
  it('ítem pendiente: solo borrar', () => {
    expect(itemButtons({ remove: true }).map((b) => b.key)).toEqual(['remove'])
  })

  it('ítem confirmado: descuento y anular, en ese orden', () => {
    const buttons = itemButtons({ discount: true, cancel: true })
    expect(buttons.map((b) => b.key)).toEqual(['discount', 'cancel'])
    expect(buttons.map((b) => b.label)).toEqual(['Descuento al ítem', 'Anular'])
    expect(buttons.map((b) => b.danger)).toEqual([false, true])
  })

  it('sin acciones devuelve una lista vacía', () => {
    expect(itemButtons({})).toEqual([])
  })
})
