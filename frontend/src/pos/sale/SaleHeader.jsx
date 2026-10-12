import { ArrowLeft, X } from 'lucide-react'
import StatusBadge from '../ui/StatusBadge'
import { saleTitle } from '../modals/AddProductsModal'
import { timeLabel } from '../utils/time'

// closeLabel: en el celular, el cierre es un "← Mesas" arriba a la izquierda en lugar de la ✕.
export default function SaleHeader({ sale, onClose, canChangeWaiter, onChangeWaiter, closeLabel = null }) {
  return (
    <div className="border-b px-4 py-3">
      {closeLabel && (
        <button type="button" onClick={onClose}
          className="-ml-1 mb-1 flex min-h-[44px] items-center gap-1 font-medium text-galia-plum">
          <ArrowLeft size={18} /> {closeLabel}
        </button>
      )}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h2 className="truncate text-lg font-semibold text-galia-plum">
            {saleTitle(sale)}{sale.customer_name ? ` · ${sale.customer_name}` : ''}
          </h2>
          <p className="text-sm text-gray-600">
            #{sale.number}{sale.people ? ` · ${sale.people} pers.` : ''} · abierta {timeLabel(sale.opened_at)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={sale.status} />
          {!closeLabel && (
            <button type="button" onClick={onClose} aria-label="Cerrar panel" className="rounded-lg p-2 hover:bg-gray-100">
              <X size={20} />
            </button>
          )}
        </div>
      </div>
      <p className="mt-1 text-sm text-gray-700">
        Mozo: {sale.waiter?.name ?? '—'}
        {canChangeWaiter && (
          <button type="button" className="ml-2 text-galia-plum underline" onClick={onChangeWaiter}>Cambiar</button>
        )}
      </p>
    </div>
  )
}
