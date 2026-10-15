import { useState } from 'react'
import { MoreHorizontal, Plus } from 'lucide-react'
import { btn } from '../ui/buttons'
import { formatMoney } from '../utils/money'
import { saleCounts } from '../utils/permissions'

export default function SaleFooter({ sale, actions, handlers, busy }) {
  const [moreOpen, setMoreOpen] = useState(false)
  const { pending } = saleCounts(sale)

  if (!['open', 'billing'].includes(sale.status)) {
    return (
      <div className="flex items-center justify-between gap-2 border-t bg-gray-50 px-4 py-3 text-sm text-gray-700">
        <span>{sale.status === 'closed' ? `Cerrada · cobrado ${formatMoney(sale.paid_total)}` : `Anulada: ${sale.cancel_reason ?? ''}`}</span>
        {actions.printReceipt && (
          <button type="button" className={btn('secondary', 'min-h-[40px]')} onClick={handlers.printReceipt}>Imprimir ticket</button>
        )}
      </div>
    )
  }

  const more = [
    actions.discount && ['Descuento a la venta', handlers.discount],
    actions.printBill && ['Precuenta', handlers.printBill],
    actions.move && ['Mover de mesa', handlers.move],
    actions.split && ['Dividir la cuenta', handlers.split],
    actions.close && ['Cerrar con saldo 0', handlers.close],
    actions.cancelSale && ['Anular la venta', handlers.cancelSale, 'danger'],
  ].filter(Boolean)
  const showBalance = sale.paid_total > 0

  return (
    <div className="space-y-2 border-t bg-gray-50 px-3 py-3">
      <div className="flex items-baseline justify-between px-1">
        <span className="text-sm text-gray-600">{showBalance ? 'Saldo' : 'Total'}</span>
        <span className="text-2xl font-bold text-galia-plum">{formatMoney(showBalance ? sale.balance : sale.total)}</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {actions.addItems && (
          <button type="button" className={btn('secondary')} onClick={handlers.add} disabled={busy}>
            <Plus size={18} /> Agregar
          </button>
        )}
        {actions.confirm && (
          <button type="button" className={btn('primary')} onClick={handlers.confirm} disabled={busy}>
            Confirmar tanda ({pending})
          </button>
        )}
        {actions.requestBill && (
          <button type="button" className={btn('secondary')} onClick={handlers.requestBill} disabled={busy}>Pedir cuenta</button>
        )}
        {actions.reopen && (
          <button type="button" className={btn('secondary')} onClick={handlers.reopen} disabled={busy}>Reabrir</button>
        )}
        {actions.pay && (
          <button type="button" className={btn('primary')} onClick={handlers.pay} disabled={busy}>Cobrar</button>
        )}
        {more.length > 0 && (
          <button type="button" className={btn('ghost')} onClick={() => setMoreOpen((open) => !open)} aria-expanded={moreOpen}>
            <MoreHorizontal size={18} /> Más
          </button>
        )}
      </div>
      {moreOpen && (
        <div className="grid grid-cols-2 gap-2">
          {more.map(([label, onClick, variant]) => (
            <button key={label} type="button" className={btn(variant ?? 'secondary')} disabled={busy}
              onClick={() => { setMoreOpen(false); onClick() }}>
              {label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
