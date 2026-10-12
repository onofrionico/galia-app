import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { posApi } from '../api/posApi'
import { useLookup } from '../hooks/usePosQueries'
import { usePosPermissions } from '../hooks/usePosPermissions'
import { useSaleMutation } from '../hooks/useSaleMutation'
import Modal from '../ui/Modal'
import { useToast } from '../ui/Toasts'
import { btn } from '../ui/buttons'
import { conflictSaleId } from '../utils/errors'

// onOpened(saleId, isNew): isNew = false cuando la mesa ya tenía una venta (409) y se muestra esa.
// allowWaiterPick: por defecto solo la caja (POS) elige mozo; el celular pasa false (el mozo es quien abre).
export default function OpenTableModal({ table, onClose, onOpened, allowWaiterPick }) {
  const perms = usePosPermissions()
  const pickWaiter = allowWaiterPick ?? perms.pos
  const { user } = useAuth()
  const toast = useToast()
  const { data: waiters = [] } = useLookup('waiters', pickWaiter)
  const [people, setPeople] = useState(2)
  const [waiterId, setWaiterId] = useState(user?.id ?? null)
  const { run, busy } = useSaleMutation()

  const submit = async () => {
    const body = { sale_type: 'salon', table_id: table.id, people }
    if (pickWaiter && waiterId && waiterId !== user?.id) body.waiter_id = waiterId
    const sale = await run(null, () => posApi.openSale(body), {
      onError: (error) => {
        const existing = conflictSaleId(error)
        if (!existing) return false
        toast.info('La mesa ya estaba abierta: te muestro esa venta')
        onOpened(existing, false)
        return true
      },
    })
    if (sale) onOpened(sale.id, true)
  }

  const footer = (
    <div className="flex justify-end gap-2">
      <button type="button" className={btn('secondary')} onClick={onClose}>Cancelar</button>
      <button type="button" className={btn('primary')} onClick={submit} disabled={busy}>Abrir mesa</button>
    </div>
  )

  return (
    <Modal title={`Abrir ${table.label}`} onClose={onClose} size="sm" footer={footer}>
      <p className="text-sm font-medium text-gray-700">Personas</p>
      <div className="mt-2 flex items-center gap-3">
        <button type="button" className={btn('secondary', 'w-14 text-xl')} aria-label="Una persona menos"
          onClick={() => setPeople((p) => Math.max(1, p - 1))}>−</button>
        <span className="w-12 text-center text-3xl font-semibold">{people}</span>
        <button type="button" className={btn('secondary', 'w-14 text-xl')} aria-label="Una persona más"
          onClick={() => setPeople((p) => Math.min(100, p + 1))}>+</button>
      </div>
      {pickWaiter && (
        <div className="mt-5">
          <p className="text-sm font-medium text-gray-700">Mozo</p>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {waiters.map((waiter) => (
              <button key={waiter.id} type="button" onClick={() => setWaiterId(waiter.id)}
                className={btn(waiter.id === waiterId ? 'primary' : 'secondary', 'justify-start truncate')}>
                {waiter.name}
              </button>
            ))}
          </div>
        </div>
      )}
    </Modal>
  )
}
