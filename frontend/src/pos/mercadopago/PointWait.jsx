import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { posMpApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { btn } from '../ui/buttons'
import { errorMessage } from '../utils/errors'
import { formatMoney } from '../utils/money'
import { POLL_MS, elapsedText, isDone, isWaiting, resultMessage, waitingLabel } from './pointCharge'

const TONES = { ok: 'bg-green-50 text-green-800', warn: 'bg-amber-50 text-amber-900', error: 'bg-red-50 text-red-800' }
const SIMULATIONS = [['approved', 'aprobar'], ['rejected', 'rechazar'], ['expired', 'vencer']]

// Espera de un cobro en el Point: consulta cada 3 s (respaldo del webhook) y muestra el resultado.
export default function PointWait({ orderId, saleId, onDone }) {
  const queryClient = useQueryClient()
  const [now, setNow] = useState(() => new Date())
  const [error, setError] = useState('')
  const [acting, setActing] = useState(false)
  const { data: order, error: loadError } = useQuery({
    queryKey: posKeys.mpPointOrder(orderId),
    queryFn: () => posMpApi.pointOrder(orderId),
    refetchInterval: (query) => (query.state.data && isDone(query.state.data) ? false : POLL_MS),
  })
  const final = order ? isDone(order) : false

  useEffect(() => {
    if (final) return undefined
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [final])

  useEffect(() => {
    if (final) queryClient.invalidateQueries({ queryKey: posKeys.sale(saleId) })
  }, [final, saleId, queryClient])

  const act = async (fn) => {
    setError('')
    setActing(true)
    try {
      queryClient.setQueryData(posKeys.mpPointOrder(orderId), await fn())
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setActing(false)
    }
  }

  if (!order) {
    return (
      <p className="py-6 text-center text-gray-500">
        {loadError ? errorMessage(loadError) : 'Enviando al Point…'}
      </p>
    )
  }
  if (final) {
    const message = resultMessage(order)
    return (
      <div className="space-y-3">
        <p className="text-center text-2xl font-bold text-galia-plum">{formatMoney(order.amount)}</p>
        <p className={`rounded-lg p-3 ${TONES[message.tone]}`}>{message.text}</p>
        <button type="button" className={btn('primary', 'w-full')} onClick={() => onDone?.(order)}>
          {order.status === 'approved' ? 'Listo' : 'Volver al cobro'}
        </button>
      </div>
    )
  }
  return (
    <div className="space-y-3 text-center">
      <p className="text-3xl font-bold text-galia-plum">{formatMoney(order.amount)}</p>
      <p className="text-gray-700">{waitingLabel(order)}</p>
      <p className="font-mono text-sm text-gray-500">{elapsedText(order.created_at, now)}</p>
      {error && <p className="text-sm text-red-700">{error}</p>}
      {isWaiting(order.status) && order.status !== 'canceling' && (
        <button type="button" className={btn('secondary', 'w-full')} disabled={acting}
          onClick={() => act(() => posMpApi.cancelPoint(orderId))}>
          Cancelar cobro
        </button>
      )}
      {order.fake && (
        <div className="flex flex-wrap justify-center gap-3 rounded-lg border border-dashed p-2 text-xs">
          <span className="text-gray-500">Simular en el Point:</span>
          {SIMULATIONS.map(([outcome, label]) => (
            <button key={outcome} type="button" className="underline" disabled={acting}
              onClick={() => act(() => posMpApi.fakePoint(orderId, outcome))}>
              {label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
