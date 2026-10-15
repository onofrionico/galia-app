import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { posFiscalApi } from '@/pos/api/posApi'
import { posKeys } from '@/pos/hooks/keys'
import { errorMessage } from '@/pos/utils/errors'
import { formatMoney } from '@/pos/utils/money'

const STATUS = { authorized: 'Autorizado', pending: 'Sin confirmar', rejected: 'Rechazado' }

// Finanzas → Comprobantes: facturas y notas de crédito del entorno activo.
export default function Invoices() {
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState({ from: '', to: '', kind: '', status: '', page: 1 })
  const [detail, setDetail] = useState(null)
  const [message, setMessage] = useState('')
  const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== ''))
  const { data, isLoading, isError } = useQuery({ queryKey: posKeys.fiscalInvoices(params), queryFn: () => posFiscalApi.list(params) })
  const set = (key) => (e) => setFilters({ ...filters, [key]: e.target.value, page: 1 })
  const act = async (fn, ok) => {
    setMessage('')
    try {
      const result = await fn()
      setMessage(result?.print_warning ?? (typeof ok === 'function' ? ok(result) : ok))
      queryClient.invalidateQueries({ queryKey: posKeys.fiscal })
    } catch (err) {
      setMessage(errorMessage(err))
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Comprobantes</h1>
      {data?.environment === 'homologacion' && (
        <p className="rounded-lg bg-amber-50 p-3 text-amber-900">Modo pruebas (homologación): sin validez fiscal.</p>
      )}
      <div className="flex flex-wrap gap-3 text-sm">
        <label>Desde <input type="date" value={filters.from} onChange={set('from')} className="ml-1 rounded border px-2 py-1" /></label>
        <label>Hasta <input type="date" value={filters.to} onChange={set('to')} className="ml-1 rounded border px-2 py-1" /></label>
        <select value={filters.kind} onChange={set('kind')} className="rounded border px-2 py-1">
          <option value="">Todos los tipos</option><option value="invoice">Facturas</option><option value="credit_note">Notas de crédito</option>
        </select>
        <select value={filters.status} onChange={set('status')} className="rounded border px-2 py-1">
          <option value="">Todos los estados</option>
          {Object.entries(STATUS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>
      {message && <p className="text-sm text-gray-700">{message}</p>}
      {isLoading && <p>Cargando…</p>}
      {isError && <p className="text-red-700">No se pudieron cargar los comprobantes.</p>}
      {data && (
        <div className="overflow-x-auto rounded-xl bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left">
              <tr>
                <th className="p-2">Fecha</th><th className="p-2">Comprobante</th><th className="p-2">Cliente</th>
                <th className="p-2 text-right">Total</th><th className="p-2">Estado</th><th className="p-2">Venta</th><th className="p-2" />
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.invoices.map((inv) => (
                <tr key={inv.id}>
                  <td className="p-2">{new Date(`${inv.voucher_date}T12:00:00`).toLocaleDateString('es-AR')}</td>
                  <td className="p-2"><button type="button" className="underline" onClick={() => setDetail(inv)}>{inv.label}</button></td>
                  <td className="p-2">{inv.receiver.name}</td>
                  <td className="p-2 text-right">{formatMoney(inv.total)}</td>
                  <td className="p-2">{STATUS[inv.status]}{inv.credit_note_label ? ' · anulada' : ''}</td>
                  <td className="p-2">{inv.sale_number ? `#${inv.sale_number}` : '-'}</td>
                  <td className="space-x-2 whitespace-nowrap p-2 text-right">
                    {inv.status === 'authorized' && (
                      <button type="button" className="underline" onClick={() => act(() => posFiscalApi.reprint(inv.id), 'Enviado a imprimir')}>Reimprimir</button>
                    )}
                    {inv.status === 'pending' && (
                      <button type="button" className="underline" onClick={() => act(() => posFiscalApi.verify(inv.id), (r) => `${r.label}: ${STATUS[r.status]}`)}>Verificar</button>
                    )}
                  </td>
                </tr>
              ))}
              {data.invoices.length === 0 && <tr><td colSpan={7} className="p-4 text-center text-gray-500">Sin comprobantes.</td></tr>}
            </tbody>
          </table>
          <div className="flex items-center justify-end gap-3 p-2 text-sm">
            <button type="button" disabled={filters.page <= 1} onClick={() => setFilters({ ...filters, page: filters.page - 1 })}>Anterior</button>
            <span>{data.page} / {data.pages}</span>
            <button type="button" disabled={filters.page >= data.pages} onClick={() => setFilters({ ...filters, page: filters.page + 1 })}>Siguiente</button>
          </div>
        </div>
      )}
      {detail && (
        <section className="space-y-2 rounded-xl bg-white p-4 text-sm shadow-sm">
          <div className="flex justify-between">
            <h2 className="font-semibold">{detail.label}</h2>
            <button type="button" onClick={() => setDetail(null)}>Cerrar</button>
          </div>
          <p>Cliente: {detail.receiver.name} · CAE {detail.cae ?? '-'} {detail.cae_due ? `(vence ${new Date(`${detail.cae_due}T12:00:00`).toLocaleDateString('es-AR')})` : ''}</p>
          {detail.related_label && <p>Anula: {detail.related_label}</p>}
          {detail.credit_note_label && <p>Anulada por: {detail.credit_note_label}</p>}
          {detail.error && <p className="text-red-700">{detail.error}</p>}
          <ul>{detail.lines.map((l, i) => <li key={i}>{l.qty} x {l.description} · {formatMoney(l.amount)}</li>)}</ul>
          {detail.sale_link && <Link className="underline" to={detail.sale_link}>Ir a la venta</Link>}
          <details>
            <summary>Pedido y respuesta de ARCA</summary>
            <pre className="overflow-x-auto text-xs">{JSON.stringify({ request: detail.request, arca: detail.arca_result }, null, 2)}</pre>
          </details>
        </section>
      )}
    </div>
  )
}
