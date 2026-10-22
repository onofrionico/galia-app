import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, ArrowDown, ArrowUp, ChevronDown, ChevronRight, Package, RefreshCw } from 'lucide-react'
import reportsService from '@/services/reportsService'
import { barWidths, defaultMonths, rankProducts, variation } from '@/utils/productsCompare'

const formatUnits = (value) => new Intl.NumberFormat('es-AR', { maximumFractionDigits: 2 }).format(Number(value) || 0)

const monthLabel = (month) => {
  const [year, number] = month.split('-').map(Number)
  return new Date(year, number - 1, 1).toLocaleDateString('es-AR', { month: 'long', year: 'numeric' })
}

const Variation = ({ a, b }) => {
  const value = variation(a, b)
  if (value == null) return <span className="text-xs text-gray-400">nuevo</span>
  const up = value >= 0
  return (
    <span className={`inline-flex items-center gap-0.5 text-sm ${up ? 'text-green-600' : 'text-red-600'}`}>
      {up ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
      {Math.abs(value)}%
    </span>
  )
}

const Bars = ({ width }) => (
  <div className="space-y-1">
    <div className="h-2 rounded bg-gray-300" style={{ width: `${width.a}%` }} />
    <div className="h-2 rounded bg-galia-plum" style={{ width: `${width.b}%` }} />
  </div>
)

const Daily = ({ productKey, months, measure, show }) => {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['reports', 'products-compare-daily', productKey, ...months],
    queryFn: () => reportsService.productsCompareDaily(productKey, ...months),
  })
  if (isLoading) return <p className="text-xs text-gray-500">Cargando el detalle…</p>
  if (isError) return <p className="text-xs text-red-600">No se pudo cargar el detalle.</p>
  const days = data.days.filter((d) => (d.a && Number(d.a[measure])) || (d.b && Number(d.b[measure])))
  if (!days.length) return <p className="text-xs text-gray-500">Sin ventas por día.</p>
  return (
    <table className="mt-2 w-full text-xs">
      <thead className="text-gray-500">
        <tr><th className="text-left font-normal">Día</th><th className="text-right font-normal">{monthLabel(months[0])}</th>
          <th className="text-right font-normal">{monthLabel(months[1])}</th></tr>
      </thead>
      <tbody>
        {days.map((d) => (
          <tr key={d.day}>
            <td>{d.day}</td>
            <td className="text-right text-gray-600">{d.a ? show(d.a[measure]) : '—'}</td>
            <td className="text-right">{d.b ? show(d.b[measure]) : '—'}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

// Ventas por producto, un mes contra otro: ranking con barras (gris = mes A, color = mes B).
const ProductsCompare = ({ formatCurrency }) => {
  const [months, setMonths] = useState(defaultMonths())
  const [measure, setMeasure] = useState('amount')
  const [open, setOpen] = useState(null)
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['reports', 'products-compare', ...months],
    queryFn: () => reportsService.productsCompare(...months),
    enabled: Boolean(months[0] && months[1]),
  })
  const show = (value) => (measure === 'amount' ? formatCurrency(Number(value) || 0) : formatUnits(value))
  const ranked = useMemo(() => rankProducts(data?.products, measure), [data, measure])
  const widths = useMemo(() => Object.fromEntries(barWidths(ranked, measure).map((w) => [w.key, w])), [ranked, measure])
  const setMonth = (index, value) => value && setMonths((current) => current.map((m, i) => (i === index ? value : m)))

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <input type="month" value={months[0]} onChange={(e) => setMonth(0, e.target.value)} className="rounded border px-2 py-1" />
        <span className="text-gray-500">contra</span>
        <input type="month" value={months[1]} onChange={(e) => setMonth(1, e.target.value)} className="rounded border px-2 py-1" />
        <div className="ml-auto inline-flex rounded-lg border border-gray-200 bg-white p-1">
          {[['amount', 'Monto'], ['quantity', 'Cantidad']].map(([key, label]) => (
            <button key={key} type="button" onClick={() => setMeasure(key)}
              className={`rounded-md px-3 py-1 ${measure === key ? 'bg-gray-900 text-white' : 'text-gray-600'}`}>{label}</button>
          ))}
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-12 text-gray-600">
          <RefreshCw className="mr-2 animate-spin text-blue-500" size={20} /> Cargando la comparación...
        </div>
      )}
      {isError && (
        <div className="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          <AlertTriangle size={20} /> No se pudo cargar la comparación.
          <button type="button" className="underline" onClick={() => refetch()}>Reintentar</button>
        </div>
      )}
      {data && ranked.length === 0 && (
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center text-gray-500">
          <Package className="mx-auto mb-3 text-gray-400" size={32} />
          No hay ventas con detalle de productos en esos meses.
        </div>
      )}
      {data && ranked.length > 0 && (
        <div className="rounded-xl bg-white shadow-sm">
          <div className="flex flex-wrap items-center gap-4 border-b px-4 py-3 text-sm text-gray-600">
            <span className="inline-flex items-center gap-2"><span className="h-2 w-4 rounded bg-gray-300" />{monthLabel(months[0])}: {show(data.totals.a[measure])}</span>
            <span className="inline-flex items-center gap-2"><span className="h-2 w-4 rounded bg-galia-plum" />{monthLabel(months[1])}: {show(data.totals.b[measure])}</span>
            <Variation a={data.totals.a[measure]} b={data.totals.b[measure]} />
          </div>
          <ul className="divide-y">
            {ranked.map((product) => (
              <li key={product.key} className="px-4 py-3">
                <button type="button" className="grid w-full grid-cols-[1.25rem_minmax(8rem,14rem)_1fr_auto] items-center gap-3 text-left"
                  onClick={() => setOpen(open === product.key ? null : product.key)}>
                  {open === product.key ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  <span className="truncate">
                    <span className="font-medium text-gray-900">{product.name}</span>
                    {product.category && <span className="block text-xs text-gray-500">{product.category}</span>}
                  </span>
                  <Bars width={widths[product.key]} />
                  <span className="flex flex-col items-end text-sm">
                    <span>{show(product.b[measure])}</span>
                    <Variation a={product.a[measure]} b={product.b[measure]} />
                  </span>
                </button>
                {open === product.key && (
                  <div className="ml-8 mt-3 space-y-2">
                    {product.variants.length > 1 && (
                      <ul className="text-xs text-gray-600">
                        {product.variants.map((v) => (
                          <li key={v.name} className="flex justify-between">
                            <span>{v.name}</span>
                            <span>{show(v.a[measure])} → {show(v.b[measure])}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                    <Daily productKey={product.key} months={months} measure={measure} show={show} />
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default ProductsCompare
