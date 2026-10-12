import { useState } from 'react'
import { posApi } from '@/pos/api/posApi'
import { useFloor } from '@/pos/hooks/usePosQueries'
import { useSaleMutation } from '@/pos/hooks/useSaleMutation'
import { saleTitle } from '@/pos/modals/AddProductsModal'
import Chip from '@/pos/ui/Chip'
import Modal from '@/pos/ui/Modal'
import { useToast } from '@/pos/ui/Toasts'
import { btn } from '@/pos/ui/buttons'
import { tableStatus } from '@/pos/utils/floor'

// En el celular, mover es elegir una mesa libre de una lista (en la caja se toca en el plano).
export default function MoveSheet({ sale, onClose }) {
  const [salonId, setSalonId] = useState(sale.table?.salon_id)
  const { data, isLoading } = useFloor(salonId)
  const { run, busy } = useSaleMutation()
  const toast = useToast()
  const freeTables = (data?.tables ?? []).filter((table) => tableStatus(table) === 'free')

  const move = async (table) => {
    const moved = await run(sale.id, () => posApi.move(sale.id, table.id))
    if (moved) {
      toast.success(`Venta movida a ${table.label}`)
      onClose()
    }
  }

  return (
    <Modal title={`Mover ${saleTitle(sale)}`} onClose={onClose}>
      <div className="flex gap-2 overflow-x-auto pb-2">
        {(data?.salons ?? []).map((salon) => (
          <Chip key={salon.id} active={salon.id === data?.salon_id} onClick={() => setSalonId(salon.id)}>
            {salon.name}
          </Chip>
        ))}
      </div>
      {isLoading && <p className="py-6 text-center text-gray-500">Cargando mesas…</p>}
      {!isLoading && freeTables.length === 0 && (
        <p className="py-6 text-center text-gray-500">No hay mesas libres en este salón.</p>
      )}
      <div className="mt-2 grid grid-cols-3 gap-2">
        {freeTables.map((table) => (
          <button key={table.id} type="button" disabled={busy} onClick={() => move(table)}
            className={btn('secondary', 'min-h-[56px] text-lg')}>
            {table.label}
          </button>
        ))}
      </div>
    </Modal>
  )
}
