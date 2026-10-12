const ACTIVE = ['open', 'billing']

export function posPermissions({ isAdmin = false, modules = [] } = {}) {
  const has = (name) => isAdmin || modules.includes(name)
  const pos = has('POS')
  const waiter = has('Camarero')
  return {
    pos,
    waiter,
    canUse: pos || waiter,
    charge: pos || has('Cobrar'),
    cancel: has('Anular'),
    discounts: has('Descuentos'),
  }
}

export function saleCounts(sale) {
  const items = sale?.items ?? []
  return {
    pending: items.filter((i) => i.status === 'pending').length,
    confirmed: items.filter((i) => i.status === 'confirmed').length,
  }
}

// Qué acciones muestra la UI para la venta. El backend valida igual.
export function saleActions(sale, perms) {
  const active = ACTIVE.includes(sale.status)
  const { pending, confirmed } = saleCounts(sale)
  const live = pending + confirmed
  return {
    addItems: sale.status === 'open',
    confirm: sale.status === 'open' && pending > 0,
    requestBill: sale.status === 'open' && sale.sale_type === 'salon' && live > 0,
    reopen: sale.status === 'billing',
    pay: perms.charge && active && live > 0 && sale.balance > 0,
    close: perms.charge && sale.status === 'billing' && sale.balance === 0,
    discount: active && confirmed > 0,
    move: active && sale.sale_type === 'salon',
    split: active && confirmed > 0 && sale.paid_total === 0,
    cancelSale: perms.cancel && active && sale.paid_total === 0,
    changeWaiter: perms.pos && active,
    history: perms.pos,
    cancelPayment: perms.cancel && ['billing', 'closed'].includes(sale.status),
  }
}

export function itemActions(item, sale, perms) {
  const active = ACTIVE.includes(sale.status)
  return {
    remove: item.status === 'pending' && sale.status === 'open',
    discount: item.status === 'confirmed' && active,
    cancel: perms.cancel && item.status === 'confirmed' && active,
  }
}
