import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { posMpApi } from '@/pos/api/posApi'
import { posKeys } from '@/pos/hooks/keys'
import { channelLabel, monthDays, statusLabel } from '@/pos/mercadopago/reconciliation'
import { errorMessage } from '@/pos/utils/errors'
import { formatMoney } from '@/pos/utils/money'
import { parseServerDate } from '@/pos/utils/time'

const TONE = {
  conciliado: 'bg-green-100 text-green-800',
  con_diferencias: 'bg-red-100 text-red-800',
  sin_traer: 'bg-gray-100 text-gray-600',
}
const WEEKDAYS = ['L', 'M', 'M', 'J', 'V', 'S', 'D']
const today = () => new Date().toLocaleDateString('sv-SE', { timeZone: 'America/Argentina/Buenos_Aires' })
const time = (iso) => parseServerDate(iso).toLocaleTimeString('es-AR', {
  hour: '2-digit', minute: '2-digit', timeZone: 'America/Argentina/Buenos_Aires',
})
const card = 'rounded-xl bg-white p-4 shadow-sm'

function OnlyMpRow({ row, act, methods, sales, busy }) {
  const [mode, setMode] = useState(null)
  const [note, setNote] = useState('')
  const [saleId, setSaleId] = useState('')
  const [methodId, setMethodId] = useState(methods[0]?.id ?? '')
  return (
    <li className="space-y-2 py-2">
      <p>
        {time(row.date_created)} · <span className="font-medium">{formatMoney(row.amount)}</span> · {channelLabel(row.channel)}
        {row.payment_method ? ` · ${row.payment_method}` : ''}{row.description ? ` · ${row.description}` : ''}
      </p>
      {row.suggestions.map((s) => (
        <button key={s.payment_id} type="button" disabled={busy} className="mr-2 rounded bg-galia-plum/10 px-2 py-1 text-xs"
          onClick={() => act({ kind: 'matched_manual', movement_id: row.movement_id, payment_id: s.payment_id })}>
          Asociar a venta #{s.sale_number} · {s.method_name} {formatMoney(s.amount)} ({time(s.created_at)})
        </button>
      ))}
      <div className="flex flex-wrap gap-3 text-xs">
        <button type="button" className="underline" onClick={() => setMode(mode === 'create' ? null : 'create')}>Crear pago en una venta</button>
        <button type="button" className="underline" onClick={() => setMode(mode === 'not_a_sale' ? null : 'not_a_sale')}>No es una venta</button>
      </div>
      {mode === 'create' && (
        sales.length === 0 ? (
          <p className="text-xs text-gray-500">No hay ventas del día en cobro. Si la venta ya está cerrada, asocialo o marcalo como "No es una venta".</p>
        ) : (
          <div className="flex flex-wrap gap-2 text-xs">
            <select className="rounded border px-2 py-1" value={saleId} onChange={(e) => setSaleId(e.target.value)}>
              <option value="">Elegí la venta</option>
              {sales.map((s) => <option key={s.id} value={s.id}>#{s.number} · {s.label} · saldo {formatMoney(s.balance)}</option>)}
            </select>
            <select className="rounded border px-2 py-1" value={methodId} onChange={(e) => setMethodId(e.target.value)}>
              {methods.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
            <button type="button" className="underline" disabled={busy || !saleId || !methodId}
              onClick={() => act({ kind: 'payment_created', movement_id: row.movement_id, sale_id: Number(saleId), payment_method_id: Number(methodId) })}>
              Crear
            </button>
          </div>
        )
      )}
      {mode === 'not_a_sale' && (
        <div className="flex gap-2 text-xs">
          <input className="flex-1 rounded border px-2 py-1" placeholder="¿Qué es? (obligatorio)" value={note} onChange={(e) => setNote(e.target.value)} />
          <button type="button" className="underline" disabled={busy || !note.trim()}
            onClick={() => act({ kind: 'not_a_sale', movement_id: row.movement_id, note: note.trim() })}>Guardar</button>
        </div>
      )}
    </li>
  )
}

function OnlyGaliaRow({ payment, act, busy }) {
  const [open, setOpen] = useState(false)
  const [note, setNote] = useState('')
  return (
    <li className="space-y-2 py-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span>{time(payment.created_at)} · Venta #{payment.sale_number} · {payment.method_name} · {formatMoney(payment.amount)}</span>
        <button type="button" className="text-xs underline" onClick={() => setOpen(!open)}>Marcar revisado</button>
      </div>
      {open && (
        <div className="flex gap-2 text-xs">
          <input className="flex-1 rounded border px-2 py-1" placeholder="¿Qué revisaste? (obligatorio)" value={note} onChange={(e) => setNote(e.target.value)} />
          <button type="button" className="underline" disabled={busy || !note.trim()}
            onClick={() => act({ kind: 'reviewed', payment_id: payment.payment_id, note: note.trim() })}>Guardar</button>
        </div>
      )}
    </li>
  )
}

// Finanzas → Conciliación MercadoPago: calendario del mes y detalle del día.
export default function MpReconciliation() {
  const queryClient = useQueryClient()
  const [day, setDay] = useState(today())
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)
  const [year, month] = day.split('-').map(Number)
  const days = monthDays(year, month)
  const { data: summary = [] } = useQuery({
    queryKey: posKeys.mpReconciliationSummary(days[0], days.at(-1)),
    queryFn: () => posMpApi.reconciliationSummary(days[0], days.at(-1)),
  })
  const { data, isLoading, isError } = useQuery({
    queryKey: posKeys.mpReconciliation(day), queryFn: () => posMpApi.reconciliationDay(day),
  })

  const run = async (fn, ok) => {
    setMessage(null)
    setBusy(true)
    try {
      const result = await fn()
      setMessage({ ok: true, text: typeof ok === 'function' ? ok(result) : ok })
      queryClient.invalidateQueries({ queryKey: posKeys.mp })
    } catch (err) {
      setMessage({ ok: false, text: errorMessage(err) })
    } finally {
      setBusy(false)
    }
  }
  const act = (body) => run(() => posMpApi.resolve(body), 'Resuelto')
  const offset = (new Date(`${days[0]}T12:00:00Z`).getUTCDay() + 6) % 7  // lunes primero
  const shiftMonth = (delta) => {
    const first = new Date(Date.UTC(year, month - 1 + delta, 1))
    setDay(first.toISOString().slice(0, 10))
  }

  return (
    <div className="space-y-4">
      <h1 className="text-3xl">Conciliación MercadoPago</h1>
      <section className={card}>
        <div className="mb-2 flex items-center justify-between">
          <button type="button" className="px-2" aria-label="Mes anterior" onClick={() => shiftMonth(-1)}>‹</button>
          <span className="font-medium capitalize">
            {new Date(Date.UTC(year, month - 1, 15)).toLocaleDateString('es-AR', { month: 'long', year: 'numeric', timeZone: 'UTC' })}
          </span>
          <button type="button" className="px-2" aria-label="Mes siguiente" onClick={() => shiftMonth(1)}>›</button>
        </div>
        <div className="grid grid-cols-7 gap-1 text-center text-xs">
          {WEEKDAYS.map((w, i) => <span key={i} className="text-gray-500">{w}</span>)}
          {Array.from({ length: offset }, (_, i) => <span key={`pad-${i}`} />)}
          {summary.map((d) => (
            <button key={d.day} type="button" onClick={() => setDay(d.day)}
              title={statusLabel(d.status)}
              className={`rounded p-1 ${TONE[d.status]} ${d.day === day ? 'ring-2 ring-galia-plum' : ''}`}>
              {Number(d.day.slice(-2))}{d.pending ? ` · ${d.pending}` : ''}
            </button>
          ))}
        </div>
      </section>

      <div className="flex flex-wrap items-center gap-3">
        <input type="date" value={day} onChange={(e) => e.target.value && setDay(e.target.value)} className="rounded border px-2 py-1" />
        <button type="button" className="rounded bg-galia-plum px-3 py-1.5 text-galia-cream disabled:opacity-50" disabled={busy}
          onClick={() => run(() => posMpApi.fetchDay(day),
            (r) => `Se trajeron ${r.fetched} movimientos${r.truncated ? ' (hay más de 1000: revisá el día en MercadoPago)' : ''}`)}>
          Traer de MercadoPago
        </button>
        {data && <span className={`rounded-full px-2 py-0.5 text-sm ${TONE[data.status]}`}>{statusLabel(data.status)}</span>}
      </div>
      {message && <p className={`text-sm ${message.ok ? 'text-green-700' : 'text-red-700'}`}>{message.text}</p>}
      {isLoading && <p>Cargando…</p>}
      {isError && <p className="text-red-700">No se pudo cargar el día.</p>}
      {data && (
        <div className="grid gap-4 lg:grid-cols-2">
          <section className={card}>
            <h2 className="font-semibold">Solo en MercadoPago · {formatMoney(data.totals.only_mp)}</h2>
            <ul className="divide-y text-sm">
              {data.only_mp.map((row) => (
                <OnlyMpRow key={row.movement_id} row={row} act={act} methods={data.payment_methods}
                  sales={data.billing_sales} busy={busy} />
              ))}
              {data.only_mp.length === 0 && <li className="py-2 text-gray-500">Nada pendiente.</li>}
            </ul>
          </section>
          <section className={card}>
            <h2 className="font-semibold">Solo en Galia · {formatMoney(data.totals.only_galia)}</h2>
            <ul className="divide-y text-sm">
              {data.only_galia.map((p) => <OnlyGaliaRow key={p.payment_id} payment={p} act={act} busy={busy} />)}
              {data.only_galia.length === 0 && <li className="py-2 text-gray-500">Nada pendiente.</li>}
            </ul>
          </section>
          <section className={`${card} lg:col-span-2`}>
            <h2 className="font-semibold">Coinciden · {formatMoney(data.totals.matched)}</h2>
            <ul className="divide-y text-sm">
              {data.matched.map((row, i) => (
                <li key={row.movement?.movement_id ?? `p-${row.payment?.payment_id ?? i}`} className="flex flex-wrap items-center justify-between gap-2 py-2">
                  <span>
                    {row.movement
                      ? `${time(row.movement.date_created)} · ${formatMoney(row.movement.amount)} · ${channelLabel(row.movement.channel)}`
                      : 'Sin movimiento'}
                    {row.payment ? ` ↔ Venta #${row.payment.sale_number} (${row.payment.method_name})` : ''}
                    {row.resolution?.note ? ` · ${row.resolution.note}` : ''}
                    {Number(row.difference) !== 0 ? ` · diferencia ${formatMoney(row.difference)}` : ''}
                  </span>
                  {row.resolution && (
                    <button type="button" className="text-xs underline" disabled={busy}
                      onClick={() => run(() => posMpApi.undo(row.resolution.id), 'Deshecho')}>Deshacer</button>
                  )}
                </li>
              ))}
              {data.matched.length === 0 && <li className="py-2 text-gray-500">Nada todavía.</li>}
            </ul>
          </section>
          {data.rejected.length > 0 && (
            <details className={`${card} text-sm lg:col-span-2`}>
              <summary>Rechazados o cancelados ({data.rejected.length})</summary>
              <ul className="mt-2 space-y-1">
                {data.rejected.map((m) => <li key={m.movement_id}>{time(m.date_created)} · {formatMoney(m.amount)} · {m.status}</li>)}
              </ul>
            </details>
          )}
        </div>
      )}
    </div>
  )
}
