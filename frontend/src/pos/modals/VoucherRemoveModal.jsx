import { useState } from 'react'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'

// Quitar un voucher de la venta: pide el motivo (queda en la auditoría) y devuelve el voucher a "Disponible".
export default function VoucherRemoveModal({ discount, busy, onConfirm, onClose }) {
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')

  const submit = () => {
    if (!reason.trim()) return setError('Escribí el motivo')
    setError('')
    onConfirm(reason.trim())
  }

  const footer = (
    <div className="flex justify-end gap-2">
      <button type="button" className={btn('secondary')} onClick={onClose}>Volver</button>
      <button type="button" className={btn('danger')} onClick={submit} disabled={busy}>Quitar voucher</button>
    </div>
  )

  return (
    <Modal title={`Quitar ${discount.voucher_code}`} onClose={onClose} size="sm" footer={footer}>
      <p className="text-sm text-gray-600">El voucher vuelve a quedar disponible para usarse en otra venta.</p>
      <label className="mt-3 block">
        <span className="text-sm font-medium text-gray-700">Motivo</span>
        <input value={reason} onChange={(e) => { setReason(e.target.value); setError('') }} maxLength={200} autoFocus
          className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-galia-plum focus:outline-none" />
      </label>
      {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
    </Modal>
  )
}
