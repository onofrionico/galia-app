import { useState } from 'react'
import { posCashApi } from '../api/posApi'
import { useCashMutation } from '../hooks/useCash'
import NumericKeypad from '../modals/NumericKeypad'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { applyKey } from '../utils/keypad'
import { parseAmount } from '../utils/money'

export default function OpenSessionModal({ register, onClose }) {
  const [text, setText] = useState('')
  const [fresh, setFresh] = useState(true)
  const [error, setError] = useState('')
  const { run, busy } = useCashMutation()

  const submit = async () => {
    const amount = parseAmount(text || '0')
    if (!Number.isFinite(amount) || amount < 0) return setError('Indicá el fondo inicial')
    const session = await run(() => posCashApi.open({ register_id: register.id, opening_float: amount }))
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
      {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
    </Modal>
  )
}
