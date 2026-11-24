import { Ban, Percent, Trash2, X } from 'lucide-react'
import { discountLabel, formatMoney, formatQuantity } from '../utils/money'
import { itemActions } from '../utils/permissions'
import { itemButtons } from '../utils/saleLayout'

const BUTTON_ICONS = { remove: Trash2, discount: Percent, cancel: Ban }

export default function TicketItem({ item, sale, perms, discounts, handlers, busy }) {
  const actions = itemActions(item, sale, perms)
  const buttons = itemButtons(actions)
  const cancelled = item.status === 'cancelled'
  const details = [item.variant_name, ...item.modifiers.map((m) => m.option_name)].filter(Boolean).join(' · ')

  return (
    <li className="py-1.5">
      <div className="flex w-full items-start justify-between gap-2 px-1 py-1">
        <span className={`min-w-0 flex-1 ${cancelled ? 'text-gray-400 line-through' : ''}`}>
          <span className="block break-words font-medium">{formatQuantity(item.quantity)} × {item.product_name}</span>
          <span className="block text-xs text-gray-500">{details}</span>
          {item.note && <span className="block text-xs italic text-gray-600">“{item.note}”</span>}
        </span>
        <span className="flex flex-shrink-0 items-center gap-1">
          <span className={`whitespace-nowrap ${cancelled ? 'text-gray-400 line-through' : 'font-medium'}`}>
            {formatMoney(item.line_total)}
          </span>
          {buttons.map(({ key, label, danger }) => {
            const Icon = BUTTON_ICONS[key]
            return (
              <button key={key} type="button" aria-label={label} title={label} disabled={busy}
                onClick={() => handlers[key](item)}
                className={`flex h-9 w-9 items-center justify-center rounded-lg border bg-white disabled:opacity-40 ${
                  danger ? 'border-red-300 text-red-700 hover:bg-red-50' : 'border-gray-300 text-gray-700 hover:bg-gray-50'}`}>
                <Icon size={18} />
              </button>
            )
          })}
        </span>
      </div>
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
    </li>
  )
}
