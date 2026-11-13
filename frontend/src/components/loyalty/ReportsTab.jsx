import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import loyaltyService, { monthRange } from '../../services/loyaltyService'
import { input, loyaltyKeys } from './shared'

const money = (n) => (n ?? 0).toLocaleString('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 })
const thisMonth = () => new Date().toISOString().slice(0, 7)

function Block({ title, children }) {
  return <section className="rounded-lg border p-4"><h3 className="mb-2 font-semibold">{title}</h3>{children}</section>
}

function CustomerList({ rows, empty }) {
  if (!rows.length) return <p className="text-sm text-gray-500">{empty}</p>
  return (
    <ul className="max-h-60 divide-y overflow-y-auto text-sm">
      {rows.map((r) => (
        <li key={r.id} className="flex justify-between py-1">
          <span>{r.full_name}</span>
          <span className="text-gray-500">
            {r.never_visited ? 'nunca vino' : `última: ${r.last_visit}`}{r.visits ? ` · ${r.visits} visitas` : ''}
          </span>
        </li>
      ))}
    </ul>
  )
}

export default function ReportsTab() {
  const [mode, setMode] = useState('month')
  const [month, setMonth] = useState(thisMonth())
  const [custom, setCustom] = useState(monthRange(thisMonth()))
  const range = mode === 'month' ? monthRange(month) : custom
  const { data: settings } = useQuery({ queryKey: loyaltyKeys.settings, queryFn: loyaltyService.getSettings })
  const { data: active = [] } = useQuery({ queryKey: loyaltyKeys.report('active'), queryFn: loyaltyService.activeReport })
  const { data: inactive = [] } = useQuery({ queryKey: loyaltyKeys.report('inactive'), queryFn: loyaltyService.inactiveReport })
  const { data: redemptions } = useQuery({
    queryKey: loyaltyKeys.report('redemptions', range), queryFn: () => loyaltyService.redemptionsReport(range),
  })
  const { data: comparison } = useQuery({
    queryKey: loyaltyKeys.report('sales', range), queryFn: () => loyaltyService.salesComparisonReport(range),
  })
  const days = settings?.active_days ?? 30

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Block title={`Clientes activos (${active.length}) · últimos ${days} días`}>
          <CustomerList rows={active} empty="Nadie vino en el período." />
        </Block>
        <Block title={`Clientes inactivos (${inactive.length})`}>
          <CustomerList rows={inactive} empty="No hay inactivos." />
        </Block>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <select className={input} value={mode} onChange={(e) => setMode(e.target.value)}>
          <option value="month">Por mes</option>
          <option value="range">Rango libre</option>
        </select>
        {mode === 'month' ? (
          <input className={input} type="month" value={month} onChange={(e) => setMonth(e.target.value)} />
        ) : (
          <>
            <input className={input} type="date" value={custom.from} onChange={(e) => setCustom({ ...custom, from: e.target.value })} />
            <input className={input} type="date" value={custom.to} onChange={(e) => setCustom({ ...custom, to: e.target.value })} />
          </>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Block title="Canjes">
          {redemptions && (
            <>
              <p className="text-sm">{redemptions.total} canjes · {redemptions.cafecitos} ☕ · {money(redemptions.pesos)} regalados</p>
              <table className="mt-2 w-full text-sm">
                <tbody>
                  {redemptions.by_reward.map((r) => (
                    <tr key={r.reward} className="border-t">
                      <td className="py-1">{r.reward}</td><td>{r.count}</td><td>{r.cafecitos} ☕</td><td className="text-right">{money(r.pesos)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </Block>
        <Block title="Ventas: registrados vs. no registrados">
          {comparison && (
            <table className="w-full text-sm">
              <thead><tr className="text-left text-gray-500"><th /><th>Facturado</th><th>Ventas</th><th>Ticket promedio</th></tr></thead>
              <tbody>
                <tr className="border-t"><td className="py-1">Registrados</td><td>{money(comparison.registered.total)}</td><td>{comparison.registered.count}</td><td>{money(comparison.registered.avg_ticket)}</td></tr>
                <tr className="border-t"><td className="py-1">No registrados</td><td>{money(comparison.unregistered.total)}</td><td>{comparison.unregistered.count}</td><td>{money(comparison.unregistered.avg_ticket)}</td></tr>
              </tbody>
            </table>
          )}
          <p className="mt-2 text-xs text-gray-600">
            Las ventas sin cliente identificado, incluidas todas las importadas de Fudo, cuentan como no registradas.
          </p>
        </Block>
      </div>
    </div>
  )
}
