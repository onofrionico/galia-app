import { useState } from 'react'
import { posApi } from '../api/posApi'
import { useSaleMutation } from '../hooks/useSaleMutation'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { formatQuantity } from '../utils/money'
import { stepQuantity } from '../utils/quantity'

export default function SplitModal({ sale, onClose, onDone }) {
  const items = sale.items.filter((i) => i.status === 'confirmed')
  const [quantities, setQuantities] = useState({})
  const { run, busy } = useSaleMutation()

  const lines = Object.entries(quantities)
    .filter(([, quantity]) => quantity > 0)
    .map(([itemId, quantity]) => ({ item_id: Number(itemId), quantity }))

  const step = (item, delta) => setQuantities((current) => ({
    ...current, [item.id]: stepQuantity(current[item.id] ?? 0, Number(item.quantity), delta),
  }))

  const submit = async () => {
    const result = await run(sale.id, () => posApi.split(sale.id, lines))
    if (result) onDone(result)
  }

  const footer = (
    <div className="flex justify-end gap-2">
      <button type="button" className={btn('secondary')} onClick={onClose}>Cancelar</button>
      <button type="button" className={btn('primary')} disabled={busy || lines.length === 0} onClick={submit}>
        Crear cuenta aparte
      </button>
    </div>
  )

  return (
    <Modal title="Dividir la cuenta" onClose={onClose} footer={footer}>
      <p className="mb-3 text-sm text-gray-600">Elegí qué pasa a la cuenta nueva.</p>
      <ul className="divide-y">
        {items.map((item) => (
          <li key={item.id} className="flex items-center justify-between gap-3 py-2">
            <span>
              <span className="font-medium">{item.product_name}</span>
              <span className="block text-xs text-gray-500">de {formatQuantity(item.quantity)} · {item.variant_name}</span>
            </span>
            <span className="flex items-center gap-2">
              <button type="button" className={btn('secondary', 'w-11')} aria-label={`Menos ${item.product_name}`}
                onClick={() => step(item, -1)}>−</button>
              <span className="w-10 text-center font-semibold">{formatQuantity(quantities[item.id] ?? 0)}</span>
              <button type="button" className={btn('secondary', 'w-11')} aria-label={`Más ${item.product_name}`}
                onClick={() => step(item, 1)}>+</button>
            </span>
          </li>
        ))}
      </ul>
    </Modal>
  )
}
