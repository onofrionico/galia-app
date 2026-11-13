import { Fragment, useEffect, useMemo, useState } from 'react'
import { AlertTriangle, CalendarDays, ChevronLeft, ChevronRight, RefreshCw, Search, Settings } from 'lucide-react'
import { reportsService } from '@/services/reportsService'
import { addDays, formatUnits, groupByCategory, latestOnly, productName, shortDay, tomorrowArgentina } from '@/utils/productionForecast'
import ProductionSettingsModal from './ProductionSettingsModal'

const WEEK_COLUMNS = [['0', 'Lun'], ['1', 'Mar'], ['2', 'Mié'], ['3', 'Jue'], ['4', 'Vie'], ['5', 'Sáb'], ['6', 'Dom'], ['feriado', 'Feriado']]

// Qué preparar para un día: unidades esperadas por producto y turno, según días comparables.
const ProductionTab = () => {
  const [date, setDate] = useState(tomorrowArgentina)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState('')
  const [view, setView] = useState('day') // 'day' | 'week'
  const [showSettings, setShowSettings] = useState(false)

  const fetchForecast = useMemo(() => latestOnly(reportsService.getProductionForecast), [])

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const { stale, value } = await fetchForecast(date)
      if (stale) return
      setData(value)
      setLoading(false)
    } catch (err) {
      // Sin datos: no dejar en pantalla la tabla de otro día debajo del error.
      setData(null)
      setError(err.response?.data?.error || 'No se pudo cargar el pronóstico')
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [date])

  const groups = useMemo(() => groupByCategory(data?.products, query), [data, query])
  const parts = data?.day_parts || []
  const showOutOfShift = (data?.products || []).some((p) => p.fuera_de_turno > 0)

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-wrap items-center gap-3">
        <CalendarDays className="text-gray-400" size={20} />
        <div className="flex items-center gap-1">
          <button type="button" onClick={() => setDate(addDays(date, -1))}
            className="p-1.5 rounded-lg hover:bg-gray-100" aria-label="Día anterior"><ChevronLeft size={18} /></button>
          <input type="date" value={date} onChange={(e) => e.target.value && setDate(e.target.value)}
            className="border rounded-lg px-2 py-1.5 text-sm" />
          <button type="button" onClick={() => setDate(addDays(date, 1))}
            className="p-1.5 rounded-lg hover:bg-gray-100" aria-label="Día siguiente"><ChevronRight size={18} /></button>
        </div>
        {date !== tomorrowArgentina() && (
          <button type="button" onClick={() => setDate(tomorrowArgentina())} className="text-sm text-blue-600 hover:text-blue-700">
            Mañana
          </button>
        )}
        <div className="flex rounded-lg border overflow-hidden text-sm ml-auto">
          <button type="button" onClick={() => setView('day')}
            className={`px-3 py-1.5 ${view === 'day' ? 'bg-blue-50 text-blue-700' : 'text-gray-600'}`}>Por turno</button>
          <button type="button" onClick={() => setView('week')}
            className={`px-3 py-1.5 border-l ${view === 'week' ? 'bg-blue-50 text-blue-700' : 'text-gray-600'}`}>Semana</button>
        </div>
        <button type="button" onClick={() => setShowSettings(true)}
          className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg text-gray-600 hover:bg-gray-50">
          <Settings size={14} /> Turnos
        </button>
      </div>

      {data && (
        <div className="text-sm text-gray-600 space-y-1">
          {data.is_holiday && (
            <p className="text-amber-700">
              Feriado: {data.holiday_name} — se compara con feriados anteriores y domingos.
            </p>
          )}
          {data.based_on.length > 0 && (
            <p>Basado en {data.based_on.length} {data.based_on.length === 1 ? 'día' : 'días'}: {data.based_on.map(shortDay).join(', ')}</p>
          )}
          {data.coverage.ventas_total > data.coverage.ventas_con_detalle && (
            <p className="text-amber-700">
              {data.coverage.ventas_total - data.coverage.ventas_con_detalle} de {data.coverage.ventas_total} ventas
              de esos días no tienen el detalle de productos.
            </p>
          )}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="text-red-500" size={20} />
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {loading && !data && (
        <div className="flex items-center justify-center py-12 text-gray-500"><RefreshCw className="animate-spin mr-2" size={18} /> Cargando…</div>
      )}

      {data && data.based_on.length === 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500">
          Todavía no hay días comparables con ventas para este día.
        </div>
      )}

      {data && data.based_on.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-3 border-b">
            <div className="relative max-w-xs">
              <Search className="absolute left-2.5 top-2.5 text-gray-400" size={16} />
              <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar producto"
                className="w-full pl-8 pr-3 py-2 border rounded-lg text-sm" />
            </div>
          </div>
          <div className={`overflow-x-auto ${loading ? 'opacity-60' : ''}`}>
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="px-4 py-3 text-left font-medium">Producto</th>
                  {view === 'day' ? (
                    <>
                      <th className="px-4 py-3 text-right font-medium">Total</th>
                      {parts.map((part) => (
                        <th key={part.id} className="px-4 py-3 text-right font-medium whitespace-nowrap">
                          {part.name}<span className="block text-xs font-normal text-gray-400">{part.start}–{part.end}</span>
                        </th>
                      ))}
                      {showOutOfShift && <th className="px-4 py-3 text-right font-medium">Fuera de turno</th>}
                    </>
                  ) : (
                    WEEK_COLUMNS.map(([key, label]) => <th key={key} className="px-3 py-3 text-right font-medium">{label}</th>)
                  )}
                </tr>
              </thead>
              <tbody>
                {groups.map((group) => (
                  <Fragment key={group.categoria}>
                    <tr className="bg-gray-50/60">
                      <td colSpan={20} className="px-4 py-2 text-xs font-semibold uppercase tracking-wide text-gray-500">{group.categoria}</td>
                    </tr>
                    {group.products.map((product) => (
                      <tr key={product.key} className="border-t border-gray-100">
                        <td className="px-4 py-2 text-gray-900">{productName(product)}</td>
                        {view === 'day' ? (
                          <>
                            <td className="px-4 py-2 text-right font-semibold text-gray-900">
                              {formatUnits(product.total)}
                              {product.desde_combos > 0 && (
                                <span className="block text-xs font-normal text-gray-400 whitespace-nowrap">
                                  {formatUnits(product.total - product.desde_combos)} sueltas + {formatUnits(product.desde_combos)} en combos
                                </span>
                              )}
                            </td>
                            {parts.map((part) => (
                              <td key={part.id} className="px-4 py-2 text-right text-gray-700">
                                {product.por_turno[String(part.id)] ? formatUnits(product.por_turno[String(part.id)]) : <span className="text-gray-300">–</span>}
                              </td>
                            ))}
                            {showOutOfShift && (
                              <td className="px-4 py-2 text-right text-gray-500">
                                {product.fuera_de_turno ? formatUnits(product.fuera_de_turno) : <span className="text-gray-300">–</span>}
                              </td>
                            )}
                          </>
                        ) : (
                          WEEK_COLUMNS.map(([key]) => (
                            <td key={key} className="px-3 py-2 text-right text-gray-700">
                              {product.semana?.[key] == null ? <span className="text-gray-300">–</span> : formatUnits(product.semana[key])}
                            </td>
                          ))
                        )}
                      </tr>
                    ))}
                  </Fragment>
                ))}
                {groups.length === 0 && (
                  <tr><td colSpan={20} className="px-4 py-6 text-center text-gray-500">Ningún producto coincide con la búsqueda.</td></tr>
                )}
              </tbody>
            </table>
          </div>
          {view === 'week' && (
            <p className="px-4 py-2 text-xs text-gray-500 border-t">
              Promedio de unidades por día de la semana en las últimas {data.settings.comparable_weeks} semanas (sin feriados),
              y de los feriados de los últimos {data.settings.holiday_window_months} meses.
            </p>
          )}
        </div>
      )}

      {showSettings && (
        <ProductionSettingsModal
          onClose={() => setShowSettings(false)}
          onSaved={() => { setShowSettings(false); load() }}
        />
      )}
    </div>
  )
}

export default ProductionTab
