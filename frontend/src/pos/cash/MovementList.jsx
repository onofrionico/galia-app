import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { posCashApi } from '../api/posApi'
import { useCashMutation } from '../hooks/useCash'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { formatMoney } from '../utils/money'
import { timeLabel } from '../utils/time'

const LABELS = { opening_float: 'Fondo inicial', expense: 'Gasto', withdrawal: 'Retiro', deposit: 'Ingreso' }
const SIGNS = { opening_float: '+', deposit: '+', expense: '−', withdrawal: '−' }

export default function MovementList({ session }) {
  const { isAdmin } = useAuth()
  const [cancelling, setCancelling] = useState(null)
  const [reason, setReason] = useState('')
  const { run, busy } = useCashMutation()
  const canCancel = isAdmin() && session.status === 'open'

  const confirm = async () => {
    if (!reason.trim()) return
    if (await run(() => posCashApi.cancelMovement(cancelling.id, reason.trim()))) {
      setCancelling(null)
      setReason('')
    }
  }

  return (
    <>
      <ul className="divide-y rounded-xl border border-gray-200 bg-white">
        {session.movements.map((m) => (
          <li key={m.id} className={`flex items-center gap-3 px-4 py-2 text-sm ${m.is_active ? '' : 'text-gray-400 line-through'}`}>
            <span className="w-12 text-gray-500">{timeLabel(m.created_at)}</span>
            <span className="w-24 font-medium">{LABELS[m.kind]}</span>
            <span className="min-w-0 flex-1 truncate">{m.reason ?? ''}{m.created_by ? ` · ${m.created_by.name}` : ''}</span>
            <span className="whitespace-nowrap font-medium">{SIGNS[m.kind]} {formatMoney(m.amount)}</span>
            {canCancel && m.is_active && m.kind !== 'opening_float' && (
              <button type="button" className="text-red-700 underline" onClick={() => setCancelling(m)}>Anular</button>
            )}
          </li>
        ))}
      </ul>
      {cancelling && (
        <Modal title={`Anular ${LABELS[cancelling.kind].toLowerCase()} de ${formatMoney(cancelling.amount)}`}
          onClose={() => setCancelling(null)} size="sm"
          footer={(
            <div className="flex justify-end gap-2">
              <button type="button" className={btn('secondary')} onClick={() => setCancelling(null)}>Volver</button>
              <button type="button" className={btn('danger')} disabled={busy || !reason.trim()} onClick={confirm}>Anular</button>
            </div>
          )}>
          <label className="block text-sm font-medium text-gray-700">Motivo
            <input autoFocus value={reason} maxLength={255} onChange={(e) => setReason(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
          </label>
        </Modal>
      )}
    </>
  )
}
