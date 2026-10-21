import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, AlertTriangle } from 'lucide-react'
import cutoverService from '@/services/cutoverService'
import fudoService from '@/services/fudoService'
import { CUTOVER_KEY, useCutover } from '@/pos/hooks/useCutover'
import { formatRunDate, isRunFinished } from '@/components/fudo/syncRunSummary'
import { errorMessage } from '@/pos/utils/errors'

const card = 'space-y-3 rounded-xl bg-white p-5 shadow-sm'
const primary = 'rounded bg-galia-plum px-4 py-2 text-galia-cream disabled:opacity-50'
const secondary = 'rounded border px-3 py-1.5 text-sm disabled:opacity-50'
const money = (value) => new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' }).format(Number(value) || 0)
const MONTHS_KEY = ['fudo', 'import-months']

function Toggle({ label, checked, disabled, onChange }) {
  return (
    <label className={`inline-flex items-center gap-3 ${disabled ? 'opacity-50' : 'cursor-pointer'}`}>
      <input type="checkbox" className="h-5 w-5" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
      <span className="font-medium">{label}</span>
    </label>
  )
}

// Sistema → Corte con Fudo (admin): historia, modo práctica, catálogo en Galia y Fudo apagado.
export default function FudoCutover() {
  const queryClient = useQueryClient()
  const flags = useCutover()
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)
  const [runId, setRunId] = useState(null)
  const { data: months = [] } = useQuery({ queryKey: MONTHS_KEY, queryFn: fudoService.importMonths })
  const { data: run } = useQuery({
    queryKey: ['fudo', 'sync-run', runId],
    queryFn: () => fudoService.getSyncRun(runId),
    enabled: runId !== null,
    refetchInterval: (query) => (isRunFinished(query.state.data) ? false : 3000),
  })
  const runFinished = isRunFinished(run)
  useEffect(() => {
    if (runFinished) queryClient.invalidateQueries({ queryKey: MONTHS_KEY })
  }, [runFinished, queryClient])

  const act = async (fn, ok) => {
    setMessage(null)
    setBusy(true)
    try {
      const result = await fn()
      queryClient.invalidateQueries({ queryKey: CUTOVER_KEY })
      setMessage({ ok: true, text: typeof ok === 'function' ? ok(result) : ok })
      return result
    } catch (err) {
      setMessage({ ok: false, text: errorMessage(err) })
      return null
    } finally {
      setBusy(false)
    }
  }

  const importHistory = () => act(fudoService.importHistory, (r) => {
    setRunId(r.run_id)
    return 'Importación iniciada: puede tardar varios minutos.'
  })
  const setFlag = (flag, value, confirmText) => {
    if (confirmText && !window.confirm(confirmText)) return
    act(() => cutoverService.update({ [flag]: value }), (r) => {
      if (r.link) {
        const { variants_linked: linked, variants_unlinked: unlinked } = r.link
        return `Catálogo en Galia. Carta: ${linked} precios vinculados${unlinked ? `, ${unlinked} sin vínculo para revisar` : ''}.`
      }
      return 'Listo'
    })
  }
  const clearPractice = () => {
    if (!window.confirm('Se borran todas las ventas y cajas de práctica. ¿Seguimos?')) return
    act(cutoverService.clearPractice, (r) => `Práctica borrada: ${r.sales} ventas y ${r.cash_sessions} cajas.`)
  }
  const running = run && !isRunFinished(run)
  const changed = months.filter((m) => m.changed > 0)

  return (
    <div className="max-w-4xl space-y-5">
      <h1 className="text-3xl">Corte con Fudo</h1>
      {message && (
        <p className={`rounded-lg p-3 ${message.ok ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>{message.text}</p>
      )}

      <section className={card}>
        <h2 className="text-lg font-semibold">1. Historia de Fudo</h2>
        <p className="text-sm text-gray-600">
          Trae todas las ventas de Fudo con sus productos, mes por mes. Se puede repetir: no duplica nada y retoma donde quedó.
        </p>
        <button type="button" className={primary} disabled={busy || running || flags.fudo_off} onClick={importHistory}>
          {running ? 'Importando…' : 'Importar historia'}
        </button>
        {run && (
          <p className="text-sm text-gray-600">
            Corrida #{run.id}: {run.status === 'running' ? 'en curso' : run.status === 'ok' ? 'terminada' : `con error: ${run.error}`}
            {run.finished_at ? ` · ${formatRunDate(run.finished_at)}` : ''}
          </p>
        )}
        {changed.length > 0 && (
          <p className="rounded bg-amber-50 p-2 text-sm text-amber-900">
            Cambiaron ventas ya importadas en {changed.map((m) => m.month).join(', ')}: los reportes de esos meses se corrigieron.
          </p>
        )}
        {months.length > 0 && (
          <div className="max-h-80 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-white text-left text-gray-500">
                <tr><th className="py-1">Mes</th><th className="text-right">Ventas Fudo</th><th className="text-right">Total Fudo</th>
                  <th className="text-right">Ventas Galia</th><th className="text-right">Total Galia</th><th /></tr>
              </thead>
              <tbody className="divide-y">
                {months.map((m) => (
                  <tr key={m.month}>
                    <td className="py-1">{m.month}</td>
                    <td className="text-right">{m.fudo_count}</td>
                    <td className="text-right">{money(m.fudo_total)}</td>
                    <td className="text-right">{m.galia_count}</td>
                    <td className="text-right">{money(m.galia_total)}</td>
                    <td className="pl-2" title={m.errors.length ? `${m.errors.length} ventas con error` : ''}>
                      {m.matches && !m.errors.length
                        ? <CheckCircle2 className="h-4 w-4 text-green-600" />
                        : <AlertTriangle className="h-4 w-4 text-amber-600" />}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className={card}>
        <h2 className="text-lg font-semibold">2. Modo práctica</h2>
        <p className="text-sm text-gray-600">
          Para practicar antes del corte: las ventas y cajas de práctica no cuentan en reportes, stock, facturación ni MercadoPago.
        </p>
        <Toggle label="Modo práctica" checked={flags.practice_mode} disabled={busy}
          onChange={(value) => setFlag('practice_mode', value,
            value ? 'Todo lo que se cargue desde ahora es de práctica. ¿Prendemos el modo práctica?' : null)} />
        <div>
          <button type="button" className={secondary} disabled={busy || flags.practice_mode} onClick={clearPractice}>
            Borrar práctica
          </button>
          {flags.practice_mode && <span className="ml-2 text-xs text-gray-500">Apagá el modo práctica para borrarla.</span>}
        </div>
      </section>

      <section className={card}>
        <h2 className="text-lg font-semibold">3. Catálogo en Galia</h2>
        <p className="text-sm text-gray-600">El día del corte: los precios y productos pasan a editarse en Galia, y la carta se arma con ese catálogo.</p>
        <Toggle label="Catálogo en Galia" checked={flags.catalog_in_galia} disabled={busy || flags.fudo_off}
          onChange={(value) => setFlag('catalog_in_galia', value,
            value ? 'Desde ahora los precios y productos se editan en Galia; Fudo deja de actualizarlos. ¿Seguimos?' : null)} />
        {flags.catalog_in_galia && (
          <p className="text-sm"><Link to="/menu/inbox" className="underline">Revisar la carta</Link> (ítems sin vínculo o nuevos).</p>
        )}
      </section>

      <section className={card}>
        <h2 className="text-lg font-semibold">4. Fudo apagado</h2>
        <p className="text-sm text-gray-600">Al final del período en paralelo: hacé una última importación de la historia y apagá Fudo.</p>
        <Toggle label="Fudo apagado" checked={flags.fudo_off} disabled={busy || !flags.catalog_in_galia}
          onChange={(value) => setFlag('fudo_off', value,
            value ? 'Se desactivan las sincronizaciones con Fudo. ¿Ya hiciste la última importación de la historia?' : null)} />
        {!flags.catalog_in_galia && <p className="text-xs text-gray-500">Primero pasá el catálogo a Galia.</p>}
      </section>
    </div>
  )
}
