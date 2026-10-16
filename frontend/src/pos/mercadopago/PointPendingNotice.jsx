import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { posMpApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'
import { formatMoney } from '../utils/money'

// "Cobro en Point pendiente": aparece si se cerró el modal mientras el Point cobraba.
export default function PointPendingNotice({ sale, onOpen }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const order = sale.point_order
  if (!order) return null

  const cancel = async () => {
    setBusy(true)
    try {
      await posMpApi.cancelPoint(order.id)
      toast.success('Se pidió cancelar el cobro en el Point')
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
      queryClient.invalidateQueries({ queryKey: posKeys.sale(sale.id) })
    }
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 border-t bg-amber-50 px-4 py-2 text-sm text-amber-900">
      <span>Cobro en Point pendiente · {formatMoney(order.amount)}</span>
      <span className="flex gap-3">
        <button type="button" className="underline" onClick={onOpen}>Ver</button>
        {order.status !== 'canceling' && (
          <button type="button" className="underline" disabled={busy} onClick={cancel}>Cancelar</button>
        )}
      </span>
    </div>
  )
}
