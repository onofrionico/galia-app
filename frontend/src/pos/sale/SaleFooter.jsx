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

// Altura reducida (el `!` gana a la altura base de btn): el detalle de la venta necesita el espacio.
const MAIN = '!min-h-[40px]'
const SPANS = { 1: 'col-span-1', 2: 'col-span-2', 3: 'col-span-3' }

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
    <div className="space-y-1.5 border-t bg-gray-50 px-3 py-2">
      <div className="flex items-baseline justify-between px-1">
        <span className="text-sm text-gray-600">{showBalance ? 'Saldo' : 'Total'}</span>
        <span className="text-xl font-bold text-galia-plum">{formatMoney(showBalance ? sale.balance : sale.total)}</span>
      </div>
      <div className="grid grid-cols-2 gap-1.5 [&>*:last-child:nth-child(odd)]:col-span-2">
        {actions.addItems && (
          <button type="button" className={btn('secondary', MAIN)} onClick={handlers.add} disabled={busy}>
            <Plus size={18} /> Agregar
          </button>
        )}
        {actions.confirm && (
          <button type="button" className={btn('primary', MAIN)} onClick={handlers.confirm} disabled={busy}>
            Confirmar tanda ({pending})
          </button>
        )}
        {actions.requestBill && (
          <button type="button" className={btn('secondary', MAIN)} onClick={handlers.requestBill} disabled={busy}>Pedir cuenta</button>
        )}
        {actions.reopen && (
          <button type="button" className={btn('secondary', MAIN)} onClick={handlers.reopen} disabled={busy}>Reabrir</button>
        )}
        {actions.pay && (
          <button type="button" className={btn('primary', MAIN)} onClick={handlers.pay} disabled={busy}>Cobrar</button>
        )}
      </div>
      {chips.length > 0 && (
        <div className="grid grid-cols-3 gap-1.5">
          {chips.map(({ key, label, danger }, index) => {
            const Icon = CHIP_ICONS[key]
            // El último chip rellena la fila para que no quede un hueco a la derecha.
            const span = index === chips.length - 1 ? 3 - (index % 3) : 1
            return (
              <button key={key} type="button" disabled={busy} onClick={() => handlers[key]()}
                className={btn(danger ? 'danger' : 'secondary', `!min-h-[34px] !gap-1 !px-1.5 text-xs ${SPANS[span]}`)}>
                <Icon size={14} className="flex-shrink-0" /> <span className="truncate">{label}</span>
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
