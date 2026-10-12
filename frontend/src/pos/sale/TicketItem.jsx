import { useState } from 'react'
import { X } from 'lucide-react'
import { btn } from '../ui/buttons'
import { discountLabel, formatMoney, formatQuantity } from '../utils/money'
import { itemActions } from '../utils/permissions'

export default function TicketItem({ item, sale, perms, discounts, handlers, busy }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const actions = itemActions(item, sale, perms)
  const hasActions = actions.remove || actions.discount || actions.cancel
  const cancelled = item.status === 'cancelled'
  const details = [item.variant_name, ...item.modifiers.map((m) => m.option_name)].filter(Boolean).join(' · ')

  const pick = (handler) => {
    setMenuOpen(false)
    handler(item)
  }

  return (
    <li className="py-1.5">
      <button type="button" disabled={!hasActions} onClick={() => setMenuOpen((open) => !open)}
        aria-expanded={menuOpen}
        className="flex w-full items-start justify-between gap-3 rounded-lg px-1 py-1 text-left hover:bg-gray-50 disabled:hover:bg-transparent">
        <span className={`min-w-0 ${cancelled ? 'text-gray-400 line-through' : ''}`}>
          <span className="font-medium">{formatQuantity(item.quantity)} × {item.product_name}</span>
          <span className="block text-xs text-gray-500">{details}</span>
          {item.note && <span className="block text-xs italic text-gray-600">“{item.note}”</span>}
        </span>
        <span className={`whitespace-nowrap ${cancelled ? 'text-gray-400 line-through' : 'font-medium'}`}>
          {formatMoney(item.line_total)}
        </span>
      </button>
      {cancelled && <p className="px-1 text-xs text-red-700">Anulado: {item.cancel_reason}</p>}
      {discounts.map((discount) => (
        <div key={discount.id} className="flex items-center justify-between pl-5 pr-1 text-xs text-green-700">
          <span>Descuento {discountLabel(discount)}{discount.reason ? ` · ${discount.reason}` : ''}</span>
          <span className="flex items-center gap-1">
            −{formatMoney(discount.amount)}
            {actions.discount && (
              <button type="button" aria-label="Quitar descuento" disabled={busy}
                onClick={() => handlers.removeDiscount(discount)} className="rounded p-0.5 hover:bg-green-50">
                <X size={12} />
              </button>
            )}
          </span>
        </div>
      ))}
      {menuOpen && hasActions && (
        <div className="mt-1 flex flex-wrap gap-2 pl-1">
          {actions.remove && (
            <button type="button" className={btn('danger', 'min-h-[40px]')} disabled={busy} onClick={() => pick(handlers.remove)}>
              Borrar
            </button>
          )}
          {actions.discount && (
            <button type="button" className={btn('secondary', 'min-h-[40px]')} onClick={() => pick(handlers.discount)}>
              Descuento al ítem
            </button>
          )}
          {actions.cancel && (
            <button type="button" className={btn('danger', 'min-h-[40px]')} onClick={() => pick(handlers.cancel)}>
              Anular
            </button>
          )}
        </div>
      )}
    </li>
  )
}
