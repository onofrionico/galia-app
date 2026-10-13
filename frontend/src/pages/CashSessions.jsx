import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { posCashApi } from '@/pos/api/posApi'
import { posKeys } from '@/pos/hooks/keys'
import { formatMoney } from '@/pos/utils/money'

const isoDay = (date) => date.toISOString().slice(0, 10)
const today = () => new Date()
const daysAgo = (n) => new Date(Date.now() - n * 86_400_000)
const when = (iso) => (iso ? new Date(/[zZ]$/.test(iso) ? iso : `${iso}Z`).toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' }) : '—')

function Sessions({ params, setPage }) {
  const { data, isLoading, isError } = useQuery({ queryKey: posKeys.cashSessions(params), queryFn: () => posCashApi.listSessions(params) })
  if (isLoading) return <p className="text-gray-500">Cargando…</p>
  if (isError) return <p className="text-red-700">No se pudieron cargar las cajas.</p>
  return (
    <>
      <table className="w-full rounded-xl bg-white text-sm shadow-sm">
        <thead>
          <tr className="border-b text-left text-gray-500">
            <th className="p-3">Caja</th><th>Apertura</th><th>Cierre</th><th>Cobrado</th><th>Dif. efectivo</th><th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {data.sessions.map((s) => (
            <tr key={s.id} className="border-b last:border-0 hover:bg-gray-50">
              <td className="p-3"><Link to={`/cash-sessions/${s.id}`} className="font-medium text-galia-plum underline">{s.register.name}</Link></td>
              <td>{when(s.opened_at)} · {s.opened_by?.name}</td>
              <td>{s.closed_at ? `${when(s.closed_at)} · ${s.closed_by?.name}` : '—'}</td>
              <td>{formatMoney(s.collected_net)}</td>
              <td className={s.cash_difference < 0 ? 'text-red-700' : s.cash_difference > 0 ? 'text-amber-700' : ''}>
                {s.cash_difference == null ? '—' : formatMoney(s.cash_difference)}
              </td>
              <td>{s.status === 'open' ? 'Abierta' : 'Cerrada'}</td>
            </tr>
          ))}
          {data.sessions.length === 0 && <tr><td colSpan={6} className="p-6 text-center text-gray-500">Sin sesiones en el rango.</td></tr>}
        </tbody>
      </table>
      {data.pages > 1 && (
        <div className="mt-3 flex items-center gap-3">
          <button type="button" disabled={params.page <= 1} onClick={() => setPage(params.page - 1)} className="underline disabled:opacity-40">Anterior</button>
          <span>Página {data.page} de {data.pages}</span>
          <button type="button" disabled={params.page >= data.pages} onClick={() => setPage(params.page + 1)} className="underline disabled:opacity-40">Siguiente</button>
        </div>
      )}
    </>
  )
}

function Unassigned({ params }) {
  const { data = [], isLoading } = useQuery({ queryKey: posKeys.cashUnassigned(params), queryFn: () => posCashApi.unassignedPayments(params) })
  if (isLoading) return <p className="text-gray-500">Cargando…</p>
  return (
    <table className="w-full rounded-xl bg-white text-sm shadow-sm">
      <thead><tr className="border-b text-left text-gray-500"><th className="p-3">Fecha</th><th>Venta</th><th>Medio</th><th>Monto</th><th>Cobró</th></tr></thead>
      <tbody>
        {data.map((p) => (
          <tr key={p.id} className={`border-b last:border-0 ${p.cancelled ? 'text-gray-400 line-through' : ''}`}>
            <td className="p-3">{when(p.created_at)}</td>
            <td>#{p.sale_number}{p.table ? ` · ${p.table}` : ''}</td>
            <td>{p.method_name}</td>
            <td>{formatMoney(p.amount)}</td>
            <td>{p.created_by?.name}</td>
          </tr>
        ))}
        {data.length === 0 && <tr><td colSpan={5} className="p-6 text-center text-gray-500">No hay pagos sin caja.</td></tr>}
      </tbody>
    </table>
  )
}

export default function CashSessions() {
  const [from, setFrom] = useState(isoDay(daysAgo(6)))
  const [to, setTo] = useState(isoDay(today()))
  const [page, setPage] = useState(1)
  const [tab, setTab] = useState('sessions')
  const range = { from, to }
  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Cajas</h1>
      <div className="flex flex-wrap items-end gap-3">
        <label className="text-sm">Desde<input type="date" value={from} onChange={(e) => { setFrom(e.target.value); setPage(1) }} className="ml-2 rounded border px-2 py-1" /></label>
        <label className="text-sm">Hasta<input type="date" value={to} onChange={(e) => { setTo(e.target.value); setPage(1) }} className="ml-2 rounded border px-2 py-1" /></label>
      </div>
      <div className="flex gap-1 border-b">
        {[['sessions', 'Sesiones'], ['unassigned', 'Pagos sin caja']].map(([key, label]) => (
          <button key={key} type="button" onClick={() => setTab(key)}
            className={`px-4 py-2 font-medium ${tab === key ? 'border-b-2 border-galia-plum text-galia-plum' : 'text-gray-600'}`}>{label}</button>
        ))}
      </div>
      {tab === 'sessions' ? <Sessions params={{ ...range, page }} setPage={setPage} /> : <Unassigned params={range} />}
    </div>
  )
}
