import { useRef, useState } from 'react'
import { X } from 'lucide-react'
import { posApi } from '../api/posApi'
import { useLookup } from '../hooks/usePosQueries'
import { usePosPermissions } from '../hooks/usePosPermissions'
import { useSaleMutation } from '../hooks/useSaleMutation'
import Modal from '../ui/Modal'
import { useModalPresentation } from '../ui/ModalPresentation'
import { btn } from '../ui/buttons'
import { changeFor, quickTenders } from '../utils/change'
import { newRequestId } from '../utils/ids'
import { applyKey } from '../utils/keypad'
import { amountToText, formatMoney, parseAmount } from '../utils/money'
import CancelReasonModal from './CancelReasonModal'
import NumericKeypad from './NumericKeypad'
import { saleTitle } from './AddProductsModal'

const inputClass = (focused) =>
  `mt-1 w-full rounded-lg border px-3 py-2 text-2xl ${focused ? 'border-galia-plum ring-2 ring-galia-plum/30' : 'border-gray-300'}`

export default function PaymentModal({ sale, onClose, onSaleClosed }) {
  const perms = usePosPermissions()
  const { data: methods = [] } = useLookup('payment-methods')
  const [methodId, setMethodId] = useState(null)
  const [amountText, setAmountText] = useState(amountToText(sale.balance))
  const [tenderedText, setTenderedText] = useState('')
  const [field, setField] = useState('amount')
  const [fresh, setFresh] = useState(true)
  const [error, setError] = useState('')
  const [closedChange, setClosedChange] = useState(null)
  const [cancelling, setCancelling] = useState(null)
  const requestId = useRef(newRequestId())
  const { run, busy } = useSaleMutation()
  // En el celular se usa el teclado del teléfono (los campos tienen inputMode="decimal").
  const showKeypad = useModalPresentation() !== 'sheet'

  const method = methods.find((m) => m.id === methodId) ?? methods[0] ?? null
  const isCash = method?.kind === 'cash'
  const amount = parseAmount(amountText)
  const tendered = parseAmount(tenderedText)
  const change = isCash ? changeFor(amount, tendered) : null
  const payments = sale.payments.filter((p) => p.is_active)

  const focusField = (name) => {
    setField(name)
    setFresh(true)
  }

  const onKey = (key) => {
    const setter = field === 'amount' ? setAmountText : setTenderedText
    setter((text) => applyKey(text, key, fresh))
    setFresh(false)
    setError('')
  }

  const resetForNext = (updated) => {
    setAmountText(amountToText(updated.balance))
    setTenderedText('')
    setField('amount')
    setFresh(true)
  }

  const submit = async () => {
    if (!method) return setError('Elegí un medio de pago')
    if (!(amount > 0)) return setError('Indicá el monto')
    if (amount > sale.balance) return setError(`El monto no puede superar el saldo (${formatMoney(sale.balance)})`)
    if (isCash && tenderedText && !(tendered >= amount)) return setError('Lo recibido no alcanza para el monto')
    setError('')
    const body = { payment_method_id: method.id, amount, client_request_id: requestId.current }
    if (isCash && tenderedText) body.tendered = tendered
    const result = await run(sale.id, () => posApi.addPayment(sale.id, body))
    if (!result) return // el id se conserva: un reintento no duplica el pago
    requestId.current = newRequestId()
    if (result.status === 'closed') {
      const last = result.payments.filter((p) => p.is_active).at(-1)
      setClosedChange(last?.change ?? 0)
      return
    }
    resetForNext(result)
  }

  const cancelPayment = async (body) => {
    const result = await run(sale.id, () => posApi.cancelPayment(cancelling.id, body))
    if (result) {
      setCancelling(null)
      resetForNext(result)
    }
  }

  if (closedChange !== null) {
    return (
      <Modal title="Venta cerrada" onClose={onSaleClosed} size="sm"
        footer={<button type="button" className={btn('primary', 'w-full')} onClick={onSaleClosed}>Listo</button>}>
        <div className="py-6 text-center">
          {closedChange > 0 ? (
            <>
              <p className="text-gray-600">Vuelto</p>
              <p className="text-4xl font-bold text-green-700">{formatMoney(closedChange)}</p>
            </>
          ) : (
            <p className="text-lg">Cobro completo.</p>
          )}
        </div>
      </Modal>
    )
  }

  return (
    <Modal title={`Cobrar ${saleTitle(sale)}`} onClose={onClose} size="lg">
      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <dl className="space-y-1 text-sm">
            <div className="flex justify-between"><dt>Total</dt><dd>{formatMoney(sale.total)}</dd></div>
            {payments.map((payment) => (
              <div key={payment.id} className="flex items-center justify-between text-gray-700">
                <dt>{payment.method_name}</dt>
                <dd className="flex items-center gap-1">
                  {formatMoney(payment.amount)}
                  {perms.cancel && (
                    <button type="button" aria-label={`Anular pago de ${payment.method_name}`}
                      onClick={() => setCancelling(payment)} className="rounded p-1 text-red-700 hover:bg-red-50">
                      <X size={14} />
                    </button>
                  )}
                </dd>
              </div>
            ))}
            <div className="flex justify-between border-t pt-2 text-lg font-semibold text-galia-plum">
              <dt>Saldo</dt><dd>{formatMoney(sale.balance)}</dd>
            </div>
          </dl>
          <p className="mt-5 text-sm font-medium text-gray-700">Medio de pago</p>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {methods.map((m) => (
              <button key={m.id} type="button" onClick={() => setMethodId(m.id)}
                className={btn(m.id === method?.id ? 'primary' : 'secondary')}>
                {m.name}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Monto a aplicar
            <input inputMode="decimal" value={amountText} onFocus={() => focusField('amount')}
              onChange={(e) => { setAmountText(e.target.value); setFresh(false) }} className={inputClass(field === 'amount')} />
          </label>
          {isCash && (
            <>
              <label className="mt-3 block text-sm font-medium text-gray-700">
                Recibido
                <input inputMode="decimal" value={tenderedText} onFocus={() => focusField('tendered')}
                  onChange={(e) => { setTenderedText(e.target.value); setFresh(false) }}
                  className={inputClass(field === 'tendered')} />
              </label>
              <div className="mt-2 flex flex-wrap gap-2">
                {quickTenders(amount).map((value, index) => (
                  <button key={value} type="button" className={btn('secondary', 'min-h-[36px] px-3 text-sm')}
                    onClick={() => { setTenderedText(amountToText(value)); setField('tendered'); setFresh(true) }}>
                    {index === 0 ? 'Justo' : formatMoney(value)}
                  </button>
                ))}
              </div>
              <p className="mt-3 flex justify-between text-lg text-green-700">
                <span>Vuelto</span><span className="font-semibold">{change === null ? '—' : formatMoney(change)}</span>
              </p>
            </>
          )}
          {showKeypad && <div className="mt-3"><NumericKeypad onKey={onKey} /></div>}
          {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
          <button type="button" className={btn('primary', 'mt-3 w-full text-lg')} disabled={busy} onClick={submit}>
            {amount >= sale.balance ? 'Registrar pago y cerrar' : 'Registrar pago'}
          </button>
        </div>
      </div>

      {cancelling && (
        <CancelReasonModal title={`Anular pago de ${formatMoney(cancelling.amount)}`} busy={busy}
          onClose={() => setCancelling(null)} onConfirm={cancelPayment} />
      )}
    </Modal>
  )
}
