import { useState } from 'react'
import { posCashApi } from '../api/posApi'
import { useCashMutation } from '../hooks/useCash'
import NumericKeypad from '../modals/NumericKeypad'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { argentinaLocalInput, localInputLabel, toArgentinaIso } from '../utils/cashMath'
import { applyKey } from '../utils/keypad'
import { parseAmount } from '../utils/money'

export default function OpenSessionModal({ register, onClose }) {
  const [text, setText] = useState('')
  const [fresh, setFresh] = useState(true)
  const [backdate, setBackdate] = useState(false)
  const [openedAt, setOpenedAt] = useState('')
  const [error, setError] = useState('')
  const { run, busy } = useCashMutation()
  const maxOpenedAt = argentinaLocalInput(new Date())

  const submit = async () => {
    const amount = parseAmount(text || '0')
    if (!Number.isFinite(amount) || amount < 0) return setError('Indicá el fondo inicial')
    if (backdate && !openedAt) return setError('Indicá desde cuándo está abierta la caja')
    if (backdate && openedAt > maxOpenedAt) return setError('La apertura no puede ser futura')
    const body = { register_id: register.id, opening_float: amount }
    if (backdate) body.opened_at = toArgentinaIso(openedAt)
    const session = await run(() => posCashApi.open(body))
    if (session) onClose()
  }

  const footer = (
    <div className="flex justify-end gap-2">
      <button type="button" className={btn('secondary')} onClick={onClose}>Cancelar</button>
      <button type="button" className={btn('primary')} disabled={busy} onClick={submit}>Abrir caja</button>
    </div>
  )

  return (
    <Modal title={`Abrir ${register.name}`} onClose={onClose} size="sm" footer={footer}>
      <label className="block text-sm font-medium text-gray-700">
        Fondo inicial (efectivo contado)
        <input inputMode="decimal" value={text} autoFocus placeholder="0"
          onChange={(e) => { setText(e.target.value); setFresh(false); setError('') }}
          className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-2xl" />
      </label>
      <div className="mt-3">
        <NumericKeypad onKey={(key) => { setText((t) => applyKey(t, key, fresh)); setFresh(false); setError('') }} />
      </div>
      {backdate ? (
        <div className="mt-3 space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            Abierta desde
            <input type="datetime-local" value={openedAt} max={maxOpenedAt}
              onChange={(e) => { setOpenedAt(e.target.value); setError('') }}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
          </label>
          {openedAt && (
            <p className="rounded-lg bg-amber-50 p-2 text-sm text-amber-800">
              Va a tomar los pagos sin caja desde {localInputLabel(openedAt)}
            </p>
          )}
          <button type="button" className="text-sm text-galia-plum underline"
            onClick={() => { setBackdate(false); setOpenedAt(''); setError('') }}>
            Abrir con la hora actual
          </button>
        </div>
      ) : (
        <button type="button" className="mt-3 text-sm text-galia-plum underline" onClick={() => setBackdate(true)}>
          Abrir con hora anterior
        </button>
      )}
      {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
    </Modal>
  )
}
