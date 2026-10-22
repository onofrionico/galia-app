import { describe, expect, it } from 'vitest'
import { itemActions, posPermissions, saleActions } from './permissions'

const cashier = posPermissions({ modules: ['POS', 'Anular'] })
const waiter = posPermissions({ modules: ['Camarero'] })

const sale = (overrides = {}) => ({
  status: 'open', sale_type: 'salon', balance: 1000, paid_total: 0,
  items: [{ id: 1, status: 'confirmed' }, { id: 2, status: 'pending' }],
  ...overrides,
})

describe('posPermissions', () => {
  it('el admin puede todo', () => {
    expect(posPermissions({ isAdmin: true })).toEqual({
      pos: true, waiter: true, canUse: true, charge: true, cancel: true, discounts: true,
    })
  })
  it('Cobrar habilita cobrar sin POS', () => {
    expect(posPermissions({ modules: ['Camarero', 'Cobrar'] }).charge).toBe(true)
    expect(waiter.charge).toBe(false)
    expect(waiter.canUse).toBe(true)
  })
})

describe('saleActions', () => {
  it('ofrece imprimir precuenta con ítems confirmados y ticket con la venta cerrada', () => {
    const open = saleActions(sale({ status: 'open', items: [{ id: 1, status: 'confirmed' }] }), cashier)
    expect(open).toMatchObject({ printBill: true, printReceipt: false })
    expect(saleActions(sale({ status: 'open', items: [{ id: 1, status: 'pending' }] }), cashier).printBill).toBe(false)
    expect(saleActions(sale({ status: 'closed', items: [{ id: 1, status: 'confirmed' }] }), cashier))
      .toMatchObject({ printBill: false, printReceipt: true })
  })
  it('venta de salón abierta con pendientes', () => {
    const actions = saleActions(sale(), cashier)
    expect(actions).toMatchObject({
      addItems: true, confirm: true, requestBill: true, reopen: false, pay: true, close: false,
      move: true, split: true, cancelSale: true, changeWaiter: true, history: true,
    })
  })
  it('el mozo sin Cobrar no cobra ni ve el historial', () => {
    const actions = saleActions(sale(), waiter)
    expect(actions.pay).toBe(false)
    expect(actions.history).toBe(false)
    expect(actions.changeWaiter).toBe(false)
    expect(actions.cancelSale).toBe(false)
  })
  it('en cuenta pedida se reabre y no se agregan ítems', () => {
    const actions = saleActions(sale({ status: 'billing', items: [{ id: 1, status: 'confirmed' }] }), cashier)
    expect(actions).toMatchObject({ addItems: false, confirm: false, requestBill: false, reopen: true, pay: true })
  })
  it('con pagos no se divide ni se anula; con saldo 0 se cierra', () => {
    const actions = saleActions(sale({ status: 'billing', paid_total: 500, balance: 0 }), cashier)
    expect(actions).toMatchObject({ split: false, cancelSale: false, pay: false, close: true })
  })
  it('el mostrador no pide cuenta ni se mueve', () => {
    const actions = saleActions(sale({ sale_type: 'counter' }), cashier)
    expect(actions.requestBill).toBe(false)
    expect(actions.move).toBe(false)
    expect(actions.pay).toBe(true)
  })
  it('una venta cerrada solo permite anular pagos, facturar e imprimir el ticket', () => {
    const actions = saleActions(sale({ status: 'closed', balance: 0, paid_total: 1000 }), cashier)
    expect(Object.entries(actions).filter(([, v]) => v).map(([k]) => k).sort())
      .toEqual(['cancelPayment', 'history', 'invoice', 'printReceipt'])
  })
  it('ofrece facturar una venta cerrada sin factura y anularla con Anular', () => {
    const closed = sale({ status: 'closed', balance: 0, paid_total: 1000, invoice: null })
    expect(saleActions(closed, cashier)).toMatchObject({ invoice: true, invoiceActions: false, cancelInvoice: false })
    const invoiced = { ...closed, invoice: { id: 1, label: 'Factura C 00005-00000001', status: 'authorized', is_active: true } }
    expect(saleActions(invoiced, cashier)).toMatchObject({ invoice: false, invoiceActions: true, cancelInvoice: true })
    expect(saleActions(invoiced, waiter)).toMatchObject({ invoice: false, invoiceActions: false, cancelInvoice: false })
    const pending = { ...closed, invoice: { id: 2, label: 'x', status: 'pending', is_active: false } }
    expect(saleActions(pending, cashier)).toMatchObject({ invoice: false, invoiceActions: true, cancelInvoice: false })
  })
  it('una venta de práctica no se factura', () => {
    const practice = sale({ status: 'closed', balance: 0, paid_total: 1000, invoice: null, is_practice: true })
    expect(saleActions(practice, cashier).invoice).toBe(false)
  })
})

describe('itemActions', () => {
  it('pendiente: solo borrar', () => {
    expect(itemActions({ status: 'pending' }, sale(), cashier)).toEqual({ remove: true, discount: false, cancel: false })
  })
  it('confirmado: descuento y anular con permiso', () => {
    expect(itemActions({ status: 'confirmed' }, sale(), cashier)).toEqual({ remove: false, discount: true, cancel: true })
    expect(itemActions({ status: 'confirmed' }, sale(), waiter).cancel).toBe(false)
  })
})
