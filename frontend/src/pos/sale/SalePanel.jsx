import { useState } from 'react'
import { ArrowLeft, X } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { posApi, posPrintApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { useSale } from '../hooks/usePosQueries'
import { usePosPermissions } from '../hooks/usePosPermissions'
import { useSaleMutation } from '../hooks/useSaleMutation'
import AddProductsModal from '../modals/AddProductsModal'
import CancelReasonModal from '../modals/CancelReasonModal'
import DiscountModal from '../modals/DiscountModal'
import PaymentModal from '../modals/PaymentModal'
import SplitModal from '../modals/SplitModal'
import WaiterModal from '../modals/WaiterModal'
import InvoiceModal from '../fiscal/InvoiceModal'
import PrintJobsList from '../print/PrintJobsList'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'
import { saleActions, saleCounts } from '../utils/permissions'
import SaleFooter from './SaleFooter'
import SaleHeader from './SaleHeader'
import SaleHistory from './SaleHistory'
import Ticket from './Ticket'

const SHELLS = {
  panel: 'flex h-full w-[400px] flex-shrink-0 flex-col border-l border-gray-200 bg-white xl:w-[440px]',
  screen: 'flex h-full w-full flex-col bg-white pt-[env(safe-area-inset-top)]',
}

function PanelShell({ variant, children }) {
  return <aside aria-label="Venta" className={SHELLS[variant]}>{children}</aside>
}

function PanelMessage({ variant, closeLabel, onClose, children }) {
  return (
    <PanelShell variant={variant}>
      <div className={`flex p-2 ${closeLabel ? 'justify-start' : 'justify-end'}`}>
        {closeLabel ? (
          <button type="button" onClick={onClose} className="flex min-h-[44px] items-center gap-1 px-2 font-medium text-galia-plum">
            <ArrowLeft size={18} /> {closeLabel}
          </button>
        ) : (
          <button type="button" onClick={onClose} aria-label="Cerrar panel" className="rounded-lg p-2 hover:bg-gray-100"><X size={20} /></button>
        )}
      </div>
      <p className="p-6 text-center text-gray-500">{children}</p>
    </PanelShell>
  )
}

// siblings: ventas activas de la misma mesa (pestañas "Cuenta 1", "Cuenta 2").
// variant: 'panel' (caja, lateral de 400 px) o 'screen' (celular, pantalla completa con "← closeLabel").
export default function SalePanel({ saleId, siblings = [], initialModal = null, onSelect, onClose, onStartMove,
  variant = 'panel', closeLabel = null }) {
  const { data: sale, isLoading, isError } = useSale(saleId)
  const perms = usePosPermissions()
  const toast = useToast()
  const queryClient = useQueryClient()
  const { run, busy } = useSaleMutation()
  const [tab, setTab] = useState('ticket')
  const [modal, setModal] = useState(initialModal ? { type: initialModal } : null)

  if (isLoading) return <PanelMessage variant={variant} closeLabel={closeLabel} onClose={onClose}>Cargando venta…</PanelMessage>
  if (isError || !sale) return <PanelMessage variant={variant} closeLabel={closeLabel} onClose={onClose}>No se encontró la venta.</PanelMessage>

  const actions = saleActions(sale, perms)
  const { pending } = saleCounts(sale)
  const closeModal = () => setModal(null)

  // "Pedir cuenta" y "Cobrar" confirman antes la tanda pendiente.
  const confirmPendingFirst = async () => {
    if (!pending) return true
    const result = await run(sale.id, () => posApi.confirm(sale.id))
    if (result) toast.info('Se confirmó la tanda pendiente')
    return Boolean(result)
  }

  // Imprimir no cambia la venta: solo se avisa y se refresca la pestaña "Impresiones".
  const sendToPrinter = (request, message) => request(sale.id)
    .then(() => {
      toast.success(message)
      queryClient.invalidateQueries({ queryKey: posKeys.printSaleJobs(sale.id) })
    })
    .catch((error) => toast.error(errorMessage(error)))

  const handlers = {
    add: () => setModal({ type: 'add' }),
    confirm: () => run(sale.id, () => posApi.confirm(sale.id)),
    requestBill: async () => {
      if (!(await confirmPendingFirst())) return
      const billed = await run(sale.id, () => posApi.requestBill(sale.id))
      if (billed) toast.info('Cuenta pedida', { label: 'Imprimir precuenta', onClick: handlers.printBill })
    },
    printBill: () => sendToPrinter(posPrintApi.printBill, 'Precuenta enviada a imprimir'),
    printReceipt: () => sendToPrinter(posPrintApi.printReceipt, 'Ticket enviado a imprimir'),
    reopen: () => run(sale.id, () => posApi.reopen(sale.id)),
    pay: async () => {
      if (sale.sale_type === 'salon' && sale.status === 'open') {
        if (!(await confirmPendingFirst())) return
        if (!(await run(sale.id, () => posApi.requestBill(sale.id)))) return
      }
      setModal({ type: 'pay' })
    },
    close: async () => {
      if (await run(sale.id, () => posApi.close(sale.id))) onClose()
    },
    discount: () => setModal({ type: 'discount' }),
    move: onStartMove,
    split: () => setModal({ type: 'split' }),
    cancelSale: () => setModal({ type: 'cancel-sale' }),
    changeWaiter: () => setModal({ type: 'waiter' }),
    invoice: () => setModal({ type: 'invoice' }),
  }

  const itemHandlers = {
    remove: (item) => run(sale.id, () => posApi.deleteItem(sale.id, item.id)),
    discount: (item) => setModal({ type: 'discount', item }),
    cancel: (item) => setModal({ type: 'cancel-item', item }),
    removeDiscount: (discount) => run(sale.id, () => posApi.cancelDiscount(discount.id)),
  }

  const tabClass = (active) =>
    `flex-1 py-2 text-sm font-medium ${active ? 'border-b-2 border-galia-plum text-galia-plum' : 'text-gray-600'}`

  return (
    <PanelShell variant={variant}>
      <SaleHeader sale={sale} onClose={onClose} closeLabel={closeLabel}
        canChangeWaiter={actions.changeWaiter} onChangeWaiter={handlers.changeWaiter} />
      {siblings.length > 1 && (
        <div className="flex gap-1 overflow-x-auto border-b px-3 py-2" role="tablist" aria-label="Cuentas de la mesa">
          {siblings.map((s, index) => (
            <button key={s.id} type="button" role="tab" aria-selected={s.id === sale.id} onClick={() => onSelect(s.id)}
              className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-sm ${s.id === sale.id ? 'bg-galia-plum text-galia-cream' : 'bg-gray-100'}`}>
              Cuenta {index + 1} · #{s.number}
            </button>
          ))}
        </div>
      )}
      <div className="flex border-b">
        <button type="button" className={tabClass(tab === 'ticket')} onClick={() => setTab('ticket')}>Ticket</button>
        {actions.history && (
          <button type="button" className={tabClass(tab === 'history')} onClick={() => setTab('history')}>Historial</button>
        )}
        <button type="button" className={tabClass(tab === 'prints')} onClick={() => setTab('prints')}>Impresiones</button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto">
        {tab === 'history' && actions.history && <SaleHistory saleId={sale.id} />}
        {tab === 'prints' && <PrintJobsList saleId={sale.id} />}
        {(tab === 'ticket' || (tab === 'history' && !actions.history)) && (
          <Ticket sale={sale} perms={perms} handlers={itemHandlers} busy={busy} />
        )}
      </div>
      <div className="bg-gray-50 pb-[env(safe-area-inset-bottom)]">
        <SaleFooter sale={sale} actions={actions} handlers={handlers} busy={busy} />
      </div>

      {modal?.type === 'add' && <AddProductsModal sale={sale} onClose={closeModal} />}
      {modal?.type === 'pay' && (
        <PaymentModal sale={sale} onClose={closeModal} onSaleClosed={() => { closeModal(); onClose() }} />
      )}
      {modal?.type === 'discount' && <DiscountModal sale={sale} item={modal.item ?? null} onClose={closeModal} />}
      {modal?.type === 'split' && (
        <SplitModal sale={sale} onClose={closeModal} onDone={(newSale) => {
          closeModal()
          queryClient.invalidateQueries({ queryKey: posKeys.sale(sale.id) })
          onSelect(newSale.id)
        }} />
      )}
      {modal?.type === 'waiter' && <WaiterModal sale={sale} onClose={closeModal} />}
      {modal?.type === 'invoice' && <InvoiceModal saleId={sale.id} onClose={closeModal} />}
      {modal?.type === 'cancel-item' && (
        <CancelReasonModal title={`Anular ${modal.item.product_name}`} busy={busy} onClose={closeModal}
          onConfirm={async (body) => {
            if (await run(sale.id, () => posApi.cancelItem(sale.id, modal.item.id, body))) closeModal()
          }} />
      )}
      {modal?.type === 'cancel-sale' && (
        <CancelReasonModal title="Anular la venta" busy={busy} onClose={closeModal}
          onConfirm={async (body) => {
            if (await run(sale.id, () => posApi.cancelSale(sale.id, body))) {
              closeModal()
              onClose()
            }
          }} />
      )}
    </PanelShell>
  )
}
