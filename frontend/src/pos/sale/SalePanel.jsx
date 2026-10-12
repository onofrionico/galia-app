import { useState } from 'react'
import { X } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import { posApi } from '../api/posApi'
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
import { useToast } from '../ui/Toasts'
import { saleActions, saleCounts } from '../utils/permissions'
import SaleFooter from './SaleFooter'
import SaleHeader from './SaleHeader'
import SaleHistory from './SaleHistory'
import Ticket from './Ticket'

function PanelShell({ children }) {
  return (
    <aside aria-label="Venta" className="flex h-full w-[400px] flex-shrink-0 flex-col border-l border-gray-200 bg-white xl:w-[440px]">
      {children}
    </aside>
  )
}

function PanelMessage({ onClose, children }) {
  return (
    <PanelShell>
      <div className="flex justify-end p-2">
        <button type="button" onClick={onClose} aria-label="Cerrar panel" className="rounded-lg p-2 hover:bg-gray-100"><X size={20} /></button>
      </div>
      <p className="p-6 text-center text-gray-500">{children}</p>
    </PanelShell>
  )
}

// siblings: ventas activas de la misma mesa (pestañas "Cuenta 1", "Cuenta 2").
export default function SalePanel({ saleId, siblings = [], initialModal = null, onSelect, onClose, onStartMove }) {
  const { data: sale, isLoading, isError } = useSale(saleId)
  const perms = usePosPermissions()
  const toast = useToast()
  const queryClient = useQueryClient()
  const { run, busy } = useSaleMutation()
  const [tab, setTab] = useState('ticket')
  const [modal, setModal] = useState(initialModal ? { type: initialModal } : null)

  if (isLoading) return <PanelMessage onClose={onClose}>Cargando venta…</PanelMessage>
  if (isError || !sale) return <PanelMessage onClose={onClose}>No se encontró la venta.</PanelMessage>

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

  const handlers = {
    add: () => setModal({ type: 'add' }),
    confirm: () => run(sale.id, () => posApi.confirm(sale.id)),
    requestBill: async () => {
      if (await confirmPendingFirst()) await run(sale.id, () => posApi.requestBill(sale.id))
    },
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
    <PanelShell>
      <SaleHeader sale={sale} onClose={onClose} canChangeWaiter={actions.changeWaiter} onChangeWaiter={handlers.changeWaiter} />
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
      {actions.history && (
        <div className="flex border-b">
          <button type="button" className={tabClass(tab === 'ticket')} onClick={() => setTab('ticket')}>Ticket</button>
          <button type="button" className={tabClass(tab === 'history')} onClick={() => setTab('history')}>Historial</button>
        </div>
      )}
      <div className="min-h-0 flex-1 overflow-y-auto">
        {tab === 'history' && actions.history
          ? <SaleHistory saleId={sale.id} />
          : <Ticket sale={sale} perms={perms} handlers={itemHandlers} busy={busy} />}
      </div>
      <SaleFooter sale={sale} actions={actions} handlers={handlers} busy={busy} />

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
