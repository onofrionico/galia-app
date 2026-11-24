// Qué acciones se muestran visibles en el panel de venta y en qué orden.
// Los permisos ya vienen resueltos en `saleActions` / `itemActions` (permissions.js).

const FOOTER_CHIPS = [
  { key: 'discount', label: 'Descuento', danger: false },
  { key: 'printBill', label: 'Precuenta', danger: false },
  { key: 'move', label: 'Mover de mesa', danger: false },
  { key: 'split', label: 'Dividir la cuenta', danger: false },
  { key: 'close', label: 'Cerrar con saldo 0', danger: false },
  { key: 'cancelSale', label: 'Anular la venta', danger: true },
]

const ITEM_BUTTONS = [
  { key: 'remove', label: 'Borrar', danger: true },
  { key: 'discount', label: 'Descuento al ítem', danger: false },
  { key: 'cancel', label: 'Anular', danger: true },
]

export const footerChips = (actions) => FOOTER_CHIPS.filter(({ key }) => actions[key])

export const itemButtons = (actions) => ITEM_BUTTONS.filter(({ key }) => actions[key])
