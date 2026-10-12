import { posApi } from '../api/posApi'
import { useLookup } from '../hooks/usePosQueries'
import { useSaleMutation } from '../hooks/useSaleMutation'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'

export default function WaiterModal({ sale, onClose }) {
  const { data: waiters = [], isLoading } = useLookup('waiters')
  const { run, busy } = useSaleMutation()

  const choose = async (waiter) => {
    if (waiter.id === sale.waiter?.id) {
      onClose()
      return
    }
    const result = await run(sale.id, () => posApi.changeWaiter(sale.id, waiter.id))
    if (result) onClose()
  }

  return (
    <Modal title="Cambiar mozo" onClose={onClose} size="sm">
      {isLoading && <p className="text-sm text-gray-500">Cargando…</p>}
      <div className="grid grid-cols-1 gap-2">
        {waiters.map((waiter) => (
          <button key={waiter.id} type="button" disabled={busy} onClick={() => choose(waiter)}
            className={btn(waiter.id === sale.waiter?.id ? 'primary' : 'secondary', 'justify-start')}>
            {waiter.name}
          </button>
        ))}
      </div>
    </Modal>
  )
}
