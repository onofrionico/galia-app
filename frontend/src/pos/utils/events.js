import { formatMoney, formatQuantity } from './money'

const LABELS = {
  opened: 'Abrió la venta',
  item_added: 'Agregó',
  item_deleted: 'Borró un pendiente',
  item_cancelled: 'Anuló un ítem',
  batch_confirmed: 'Confirmó una tanda',
  bill_requested: 'Pidió la cuenta',
  reopened: 'Reabrió',
  discount_added: 'Aplicó un descuento',
  discount_cancelled: 'Quitó un descuento',
  payment_added: 'Cobró',
  payment_cancelled: 'Anuló un pago',
  closed: 'Cerró la venta',
  cancelled: 'Anuló la venta',
  moved: 'Movió de mesa',
  split_out: 'Separó ítems a otra cuenta',
  split_in: 'Recibió ítems de otra cuenta',
  waiter_changed: 'Cambió el mozo',
}

export const eventLabel = (type) => LABELS[type] ?? type

export function eventDetail(event) {
  const p = event.payload ?? {}
  const parts = []
  if (p.product) parts.push(p.quantity ? `${formatQuantity(p.quantity)} × ${p.product}` : p.product)
  if (p.method) parts.push(p.method)
  if (p.amount !== undefined && p.amount !== null) parts.push(formatMoney(p.amount))
  if (p.reason) parts.push(`Motivo: ${p.reason}`)
  return parts.join(' · ')
}
