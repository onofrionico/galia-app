import { Gift, UserRound } from 'lucide-react'
import { customerChip } from './loyaltyFormat'

const ACTIVE = ['open', 'billing']

// Cliente de la venta y botón de canje (solo caja). Sin permiso o en práctica no se muestra.
export default function CustomerButton({ sale, perms, onPick, onRedeem }) {
  if (!perms.loyalty || sale.is_practice) {
    return sale.customer ? <p className="mt-1 text-sm text-gray-700">👤 {sale.customer.full_name}</p> : null
  }
  const editable = ACTIVE.includes(sale.status)
  return (
    <div className="mt-2 flex flex-wrap items-center gap-2">
      <button type="button" disabled={!editable} onClick={onPick}
        className="inline-flex min-h-[40px] items-center gap-1 rounded-full border border-galia-plum/40 px-3 text-sm text-galia-plum hover:bg-galia-plum/5 disabled:opacity-60">
        <UserRound size={16} />
        {sale.customer ? customerChip(sale.customer, sale.cafecitos_preview) : 'Cliente'}
      </button>
      {sale.customer && sale.status === 'open' && (
        <button type="button" onClick={onRedeem}
          className="inline-flex min-h-[40px] items-center gap-1 rounded-full bg-galia-plum px-3 text-sm text-galia-cream">
          <Gift size={16} /> Canjear
        </button>
      )}
    </div>
  )
}
