import { X } from 'lucide-react'
import { discountLabel, formatMoney } from '../utils/money'
import TicketItem from './TicketItem'

function Totals({ sale, saleDiscounts, activeDiscountCount, canRemove, onRemoveDiscount, busy }) {
  return (
    <dl className="space-y-1 border-t pt-3 text-sm">
      <div className="flex justify-between"><dt>Subtotal</dt><dd>{formatMoney(sale.subtotal)}</dd></div>
      {saleDiscounts.map((discount) => (
        <div key={discount.id} className="flex items-center justify-between text-green-700">
          <dt>Descuento {discountLabel(discount)}{discount.reason ? ` · ${discount.reason}` : ''}</dt>
          <dd className="flex items-center gap-1">
            −{formatMoney(discount.amount)}
            {canRemove && (
              <button type="button" aria-label="Quitar descuento" disabled={busy}
                onClick={() => onRemoveDiscount(discount)} className="rounded p-0.5 hover:bg-green-50">
                <X size={12} />
              </button>
            )}
          </dd>
        </div>
      ))}
      {/* Suma de los descuentos ya listados (por renglón y de la venta): solo si hay más de uno. */}
      {activeDiscountCount > 1 && sale.discount_total > 0 && (
        <div className="flex justify-between text-green-700"><dt>Total descuentos</dt><dd>−{formatMoney(sale.discount_total)}</dd></div>
      )}
      <div className="flex justify-between text-base font-semibold"><dt>Total</dt><dd>{formatMoney(sale.total)}</dd></div>
      {sale.paid_total > 0 && (
        <>
          <div className="flex justify-between"><dt>Pagado</dt><dd>{formatMoney(sale.paid_total)}</dd></div>
          <div className="flex justify-between font-semibold text-galia-plum"><dt>Saldo</dt><dd>{formatMoney(sale.balance)}</dd></div>
        </>
      )}
    </dl>
  )
}

export default function Ticket({ sale, perms, handlers, busy }) {
  const active = sale.discounts.filter((d) => d.is_active)
  const discountsFor = (item) => active.filter((d) => d.item_id === item.id)
  const saleDiscounts = active.filter((d) => d.item_id === null)
  const pending = sale.items.filter((i) => i.status === 'pending')
  const batches = new Map()
  for (const item of sale.items.filter((i) => i.status !== 'pending')) {
    const key = item.batch ?? 0
    batches.set(key, [...(batches.get(key) ?? []), item])
  }
  const row = (item) => (
    <TicketItem key={item.id} item={item} sale={sale} perms={perms} discounts={discountsFor(item)}
      handlers={handlers} busy={busy} />
  )

  return (
    <div className="space-y-4 px-4 py-3">
      {sale.items.length === 0 && <p className="py-8 text-center text-gray-500">Todavía no hay productos.</p>}
      {[...batches.entries()].sort(([a], [b]) => a - b).map(([batch, items]) => (
        <section key={batch}>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">Tanda {batch}</h3>
          <ul className="divide-y">{items.map(row)}</ul>
        </section>
      ))}
      {pending.length > 0 && (
        <section className="rounded-lg bg-amber-50 p-2">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-amber-800">Pendientes de confirmar</h3>
          <ul className="divide-y divide-amber-100">{pending.map(row)}</ul>
        </section>
      )}
      <Totals sale={sale} saleDiscounts={saleDiscounts} activeDiscountCount={active.length} busy={busy}
        onRemoveDiscount={handlers.removeDiscount}
        canRemove={['open', 'billing'].includes(sale.status)} />
    </div>
  )
}
