import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { posFiscalApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { useToast } from '../ui/Toasts'
import { errorMessage } from '../utils/errors'

// Factura de la venta en el pie: reimprimir, verificar (si está sin confirmar) y anular (nota de crédito).
export default function InvoiceTag({ sale, canCancel }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const invoice = sale.invoice

  const run = async (fn, success) => {
    setBusy(true)
    try {
      const result = await fn()
      if (result?.status === 'rejected') toast.error(result.error)
      else if (result?.print_warning) toast.error(result.print_warning)
      else toast.success(typeof success === 'function' ? success(result) : success)
      queryClient.invalidateQueries({ queryKey: posKeys.sale(sale.id) })
      queryClient.invalidateQueries({ queryKey: posKeys.fiscal })
    } catch (err) {
      toast.error(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const cancel = () => {
    if (!window.confirm(`¿Anular la ${invoice.label}? Se emite una nota de crédito por el total.`)) return
    run(() => posFiscalApi.cancel(invoice.id),
      (r) => (r.status === 'pending' ? 'Nota de crédito sin confirmar: verificala en Comprobantes' : `${r.label} emitida`))
  }

  const pending = invoice.status === 'pending'
  return (
    <div className="flex flex-wrap items-center gap-3 text-sm">
      <span className={`rounded-full px-2 py-0.5 font-medium ${pending ? 'bg-amber-100 text-amber-900' : 'bg-green-100 text-green-800'}`}>
        {pending ? 'Factura sin confirmar' : invoice.label}
      </span>
      {pending ? (
        <button type="button" disabled={busy} className="underline"
          onClick={() => run(() => posFiscalApi.verify(invoice.id), (r) => (r.status === 'authorized' ? `${r.label} confirmada` : 'Verificada'))}>
          Verificar
        </button>
      ) : (
        <button type="button" disabled={busy} className="underline" onClick={() => run(() => posFiscalApi.reprint(invoice.id), 'Enviada a imprimir')}>
          Reimprimir
        </button>
      )}
      {canCancel && !pending && (
        <button type="button" disabled={busy} className="text-red-700 underline" onClick={cancel}>Anular factura</button>
      )}
    </div>
  )
}
