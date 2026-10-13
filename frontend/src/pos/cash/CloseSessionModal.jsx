import { useState } from 'react'
import { Link } from 'react-router-dom'
import { posCashApi } from '../api/posApi'
import { useCashMutation } from '../hooks/useCash'
import NumericKeypad from '../modals/NumericKeypad'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { closeValidation, countDifference, differenceTone } from '../utils/cashMath'
import { applyKey } from '../utils/keypad'
import { formatMoney } from '../utils/money'

const TONES = { missing: 'text-red-700', over: 'text-amber-700', even: 'text-gray-500' }

export function CloseSummaryModal({ result, onClose }) {
  return (
    <Modal title="Caja cerrada" onClose={onClose} size="sm"
      footer={<button type="button" className={btn('primary', 'w-full')} onClick={onClose}>Listo</button>}>
      <ul className="space-y-1 text-sm">
        {result.counts.map((c) => (
          <li key={c.payment_method_id} className="flex justify-between">
            <span>{c.method_name}</span>
            <span className={TONES[differenceTone(c.difference)]}>
              {formatMoney(c.counted)}{c.difference !== 0 ? ` (${c.difference > 0 ? '+' : ''}${formatMoney(c.difference)})` : ''}
            </span>
          </li>
        ))}
      </ul>
    </Modal>
  )
}

export default function CloseSessionModal({ session, onClose, onClosed }) {
  const methods = session.summary.methods
  const [texts, setTexts] = useState({})
  const [focused, setFocused] = useState(methods.find((m) => m.kind === 'cash')?.payment_method_id ?? null)
  const [fresh, setFresh] = useState(true)
  const [note, setNote] = useState('')
  const { run, busy } = useCashMutation()
  const validation = closeValidation(methods, texts, note)

  if (session.summary.open_sales > 0) {
    return (
      <Modal title="Cerrar caja" onClose={onClose} size="sm"
        footer={<Link to="/pos" className={btn('primary', 'w-full')}>Ir al plano</Link>}>
        <p>Hay {session.summary.open_sales} ventas abiertas. Cobralas o anulalas antes de cerrar.</p>
      </Modal>
    )
  }

  const setText = (id, value) => setTexts((current) => ({ ...current, [id]: value }))
  const onKey = (key) => {
    if (focused == null) return
    setText(focused, applyKey(texts[focused] ?? '', key, fresh))
    setFresh(false)
  }
  const submit = async () => {
    if (!validation.ok) return
    const result = await run(() => posCashApi.close(session.id, { counts: validation.counts, note: note.trim() || null }))
    if (result) onClosed(result)
  }

  return (
    <Modal title="Cerrar caja" onClose={onClose} size="lg">
      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500"><th>Medio</th><th>Esperado</th><th>Contado</th><th>Diferencia</th></tr>
            </thead>
            <tbody>
              {methods.map((m) => {
                const diff = countDifference(m.expected, texts[m.payment_method_id] ?? '')
                return (
                  <tr key={m.payment_method_id} className="border-t">
                    <td className="py-2 font-medium">{m.method_name}</td>
                    <td>{formatMoney(m.expected)}</td>
                    <td>
                      <input inputMode="decimal" value={texts[m.payment_method_id] ?? ''}
                        placeholder={m.kind === 'cash' ? 'Obligatorio' : formatMoney(m.expected)}
                        onFocus={() => { setFocused(m.payment_method_id); setFresh(true) }}
                        onChange={(e) => { setText(m.payment_method_id, e.target.value); setFresh(false) }}
                        className={`w-28 rounded-lg border px-2 py-1 ${focused === m.payment_method_id ? 'border-galia-plum' : 'border-gray-300'}`} />
                    </td>
                    <td className={TONES[differenceTone(diff)] ?? 'text-gray-400'}>
                      {diff == null ? '—' : `${diff > 0 ? '+' : ''}${formatMoney(diff)}`}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <label className="mt-4 block text-sm font-medium text-gray-700">Nota
            <textarea rows={2} maxLength={500} value={note} onChange={(e) => setNote(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
          </label>
          {!validation.ok && <p className="mt-2 text-sm text-amber-700">{validation.error}</p>}
        </div>
        <div>
          <NumericKeypad onKey={onKey} />
          <button type="button" className={btn('primary', 'mt-3 w-full text-lg')} disabled={busy || !validation.ok}
            onClick={submit}>
            Confirmar cierre
          </button>
        </div>
      </div>
    </Modal>
  )
}
