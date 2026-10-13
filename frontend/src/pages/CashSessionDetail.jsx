import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { posCashApi } from '@/pos/api/posApi'
import CashSummaryCards from '@/pos/cash/CashSummaryCards'
import MovementList from '@/pos/cash/MovementList'
import { useCashMutation, useCashSession } from '@/pos/hooks/useCash'
import { ToastProvider } from '@/pos/ui/Toasts'
import { btn } from '@/pos/ui/buttons'
import { formatMoney } from '@/pos/utils/money'

const when = (iso) => (iso ? new Date(/[zZ]$/.test(iso) ? iso : `${iso}Z`).toLocaleString('es-AR', { dateStyle: 'short', timeStyle: 'short' }) : '—')
const EVENTS = { opened: 'Apertura', movement_added: 'Movimiento', movement_cancelled: 'Movimiento anulado', closed: 'Cierre', reopened: 'Reapertura' }

function Detail() {
  const id = Number(useParams().id)
  const { isAdmin } = useAuth()
  const { data: session, isLoading, isError } = useCashSession(id)
  const { run, busy } = useCashMutation()
  const [reason, setReason] = useState('')

  if (isLoading) return <p className="text-gray-500">Cargando…</p>
  if (isError || !session) return <p className="text-red-700">No se encontró la sesión.</p>

  return (
    <div className="space-y-4">
      <Link to="/cash-sessions" className="text-galia-plum underline">← Cajas</Link>
      <h1 className="text-3xl">{session.register.name} · {session.status === 'open' ? 'abierta' : 'cerrada'}</h1>
      <p className="text-sm text-gray-600">
        Apertura {when(session.opened_at)} por {session.opened_by?.name} · fondo {formatMoney(session.opening_float)}
        {session.closed_at && ` · cierre ${when(session.closed_at)} por ${session.closed_by?.name}`}
      </p>
      {session.closing_note && <p className="rounded bg-gray-50 p-3 text-sm">Nota: {session.closing_note}</p>}
      <CashSummaryCards summary={session.summary} />
      {session.counts.length > 0 && (
        <table className="w-full rounded-xl bg-white text-sm shadow-sm">
          <thead><tr className="border-b text-left text-gray-500"><th className="p-3">Medio</th><th>Esperado</th><th>Contado</th><th>Diferencia</th></tr></thead>
          <tbody>
            {session.counts.map((c) => (
              <tr key={c.payment_method_id} className="border-b last:border-0">
                <td className="p-3">{c.method_name}</td><td>{formatMoney(c.expected)}</td><td>{formatMoney(c.counted)}</td>
                <td className={c.difference < 0 ? 'text-red-700' : c.difference > 0 ? 'text-amber-700' : ''}>{formatMoney(c.difference)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <h2 className="text-xl">Movimientos</h2>
      <MovementList session={session} />
      <h2 className="text-xl">Historial</h2>
      <ol className="space-y-1 text-sm">
        {(session.events ?? []).map((e) => (
          <li key={e.id}>{when(e.created_at)} · {EVENTS[e.kind] ?? e.kind} · {e.user?.name}{e.payload?.reason ? ` · ${e.payload.reason}` : ''}</li>
        ))}
      </ol>
      {isAdmin() && session.status === 'closed' && (
        <div className="flex flex-wrap items-end gap-2 rounded-xl border border-gray-200 p-4">
          <label className="text-sm">Motivo de la reapertura
            <input value={reason} onChange={(e) => setReason(e.target.value)} maxLength={255}
              className="ml-2 rounded border px-2 py-1" />
          </label>
          <button type="button" className={btn('danger')} disabled={busy || !reason.trim()}
            onClick={async () => { if (await run(() => posCashApi.reopen(session.id, reason.trim()))) setReason('') }}>
            Reabrir
          </button>
        </div>
      )}
    </div>
  )
}

// Fuera del POS no hay ToastProvider: se provee acá para los avisos de las acciones de caja.
export default function CashSessionDetail() {
  return <ToastProvider><Detail /></ToastProvider>
}
