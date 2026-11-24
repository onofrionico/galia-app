import { ArrowRightLeft, Ban, CheckCircle2, Percent, Plus, Printer, SplitSquareHorizontal } from 'lucide-react'
import InvoiceTag from '../fiscal/InvoiceTag'
import { btn } from '../ui/buttons'
import { formatMoney } from '../utils/money'
import { saleCounts } from '../utils/permissions'
import { footerChips } from '../utils/saleLayout'

const CHIP_ICONS = {
  discount: Percent,
  printBill: Printer,
  move: ArrowRightLeft,
  split: SplitSquareHorizontal,
  close: CheckCircle2,
  cancelSale: Ban,
}

export default function SaleFooter({ sale, actions, handlers, busy }) {
  const { pending } = saleCounts(sale)

  if (!['open', 'billing'].includes(sale.status)) {
    return (
      <div className="space-y-2 border-t bg-gray-50 px-4 py-3 text-sm text-gray-700">
        <div className="flex items-center justify-between gap-2">
          <span>{sale.status === 'closed' ? `Cerrada · cobrado ${formatMoney(sale.paid_total)}` : `Anulada: ${sale.cancel_reason ?? ''}`}</span>
          <div className="flex gap-2">
            {actions.invoice && (
              <button type="button" className={btn('secondary', 'min-h-[40px]')} onClick={handlers.invoice}>Facturar</button>
            )}
            {actions.printReceipt && (
              <button type="button" className={btn('secondary', 'min-h-[40px]')} onClick={handlers.printReceipt}>Imprimir ticket</button>
            )}
          </div>
        </div>
        {actions.invoiceActions && <InvoiceTag sale={sale} canCancel={actions.cancelInvoice} />}
      </div>
    )
  }

  const chips = footerChips(actions)
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
      </div>
      {chips.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {chips.map(({ key, label, danger }) => {
            const Icon = CHIP_ICONS[key]
            return (
              <button key={key} type="button" disabled={busy} onClick={() => handlers[key]()}
                className={btn(danger ? 'danger' : 'secondary', `min-h-[40px] px-3 text-sm ${danger ? 'ml-auto' : ''}`)}>
                <Icon size={16} /> {label}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
