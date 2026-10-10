import { useState } from 'react'
import { posApi } from '../api/posApi'
import { useSaleMutation } from '../hooks/useSaleMutation'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'

export default function NewCounterSaleModal({ onClose, onCreated }) {
  const [name, setName] = useState('')
  const { run, busy } = useSaleMutation()

  const submit = async (event) => {
    event.preventDefault()
    const sale = await run(null, () => posApi.openSale({ sale_type: 'counter', customer_name: name.trim() || null }))
    if (sale) onCreated(sale.id)
  }

  return (
    <Modal title="Nueva venta de mostrador" onClose={onClose} size="sm">
      <form onSubmit={submit}>
        <label className="block text-sm font-medium text-gray-700">
          Nombre del cliente (opcional)
          <input autoFocus value={name} onChange={(e) => setName(e.target.value)} maxLength={100}
            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
        </label>
        <div className="mt-4 flex justify-end gap-2">
          <button type="button" className={btn('secondary')} onClick={onClose}>Cancelar</button>
          <button type="submit" className={btn('primary')} disabled={busy}>Crear y cargar</button>
        </div>
      </form>
    </Modal>
  )
}
