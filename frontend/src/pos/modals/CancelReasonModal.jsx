import { useState } from 'react'
import { useLookup } from '../hooks/usePosQueries'
import Chip from '../ui/Chip'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'

// Devuelve {reason_id, reason}: un motivo del catálogo, texto libre o ambos.
// Con `refundable` (pago cobrado con el Point) suma refund_mp: devolver también en MercadoPago o no.
export default function CancelReasonModal({ title, busy, onConfirm, onClose, refundable = false }) {
  const { data: reasons = [], isLoading } = useLookup('cancel-reasons')
  const [reasonId, setReasonId] = useState(null)
  const [text, setText] = useState('')
  const [refund, setRefund] = useState(true)
  const [error, setError] = useState('')

  const submit = () => {
    if (!reasonId && !text.trim()) {
      setError('Elegí un motivo o escribilo')
      return
    }
    setError('')
    onConfirm({ reason_id: reasonId, reason: text.trim() || null, ...(refundable ? { refund_mp: refund } : {}) })
  }

  const footer = (
    <div className="flex justify-end gap-2">
      <button type="button" className={btn('secondary')} onClick={onClose}>Volver</button>
      <button type="button" className={btn('danger')} onClick={submit} disabled={busy}>Anular</button>
    </div>
  )

  return (
    <Modal title={title} onClose={onClose} size="sm" footer={footer}>
      <p className="text-sm font-medium text-gray-700">Motivo</p>
      {isLoading ? (
        <p className="mt-2 text-sm text-gray-500">Cargando motivos…</p>
      ) : (
        <div className="mt-2 flex flex-wrap gap-2">
          {reasons.map((reason) => (
            <Chip key={reason.id} active={reasonId === reason.id}
              onClick={() => setReasonId((current) => (current === reason.id ? null : reason.id))}>
              {reason.name}
            </Chip>
          ))}
        </div>
      )}
      <label className="mt-4 block">
        <span className="text-sm font-medium text-gray-700">{reasonId ? 'Detalle (opcional)' : 'Escribí el motivo'}</span>
        <textarea value={text} onChange={(e) => { setText(e.target.value); setError('') }} rows={2} maxLength={200}
          className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-galia-plum focus:outline-none" />
      </label>
      {refundable && (
        <fieldset className="mt-4 space-y-2 text-sm">
          <legend className="font-medium text-gray-700">Cobrado con el Point</legend>
          <label className="flex items-center gap-2">
            <input type="radio" name="refund" checked={refund} onChange={() => setRefund(true)} />
            Devolver también en MercadoPago
          </label>
          <label className="flex items-center gap-2">
            <input type="radio" name="refund" checked={!refund} onChange={() => setRefund(false)} />
            Solo anular en Galia
          </label>
        </fieldset>
      )}
      {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
    </Modal>
  )
}
