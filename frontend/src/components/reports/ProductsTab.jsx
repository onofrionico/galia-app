import { useMemo, useState } from 'react'
import { AlertTriangle, ArrowDown, ArrowUp, Package, RefreshCw, Search } from 'lucide-react'
import { coverageLevel, filterAndSortProducts, nextSort, productLabel } from '@/utils/productsReport'
import ProductsCompare from './ProductsCompare'

const CLASS_STYLES = {
  A: 'bg-green-100 text-green-700',
  B: 'bg-amber-100 text-amber-700',
  C: 'bg-gray-100 text-gray-600',
}

const formatUnits = (value) =>
  new Intl.NumberFormat('es-AR', { maximumFractionDigits: 2 }).format(value || 0)

const Variation = ({ value }) => {
  if (value == null) return <span className="text-gray-400">nuevo</span>
  const positive = value >= 0
  return (
    <span className={`inline-flex items-center gap-0.5 ${positive ? 'text-green-600' : 'text-red-600'}`}>
      {positive ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
      {Math.abs(value).toFixed(1)}%
    </span>
  )
}

const SortHeader = ({ label, column, sort, onSort, align = 'right' }) => (
  <th className={`px-4 py-3 font-medium text-${align}`}>
    <button
      type="button"
      onClick={() => onSort(column)}
      className={`inline-flex items-center gap-1 hover:text-gray-900 ${sort.sortKey === column ? 'text-gray-900' : ''}`}
    >
      {label}
      {sort.sortKey === column && (sort.sortDir === 'desc' ? <ArrowDown size={12} /> : <ArrowUp size={12} />)}
    </button>
  </th>
)

const CoverageNotice = ({ summary }) => {
  const level = coverageLevel(summary.cobertura_monto_pct)
  if (level === 'ok') return null
  const styles = level === 'low'
    ? 'bg-red-50 border-red-200 text-red-700'
    : 'bg-amber-50 border-amber-200 text-amber-700'
  return (
    <div className={`border rounded-lg p-4 flex items-start gap-3 ${styles}`}>
      <AlertTriangle className="flex-shrink-0 mt-0.5" size={18} />
      <p className="text-sm">
        Solo {summary.ventas_con_detalle} de {summary.ventas_total} ventas del período tienen el detalle de
        productos ({summary.cobertura_monto_pct}% de lo facturado). Para completar el historial, sincronizá
        las ventas de Fudo de este período desde Ventas.
      </p>
    </div>
  )
}

const PeriodView = ({ data, loading, error, formatCurrency }) => {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')
  const [sort, setSort] = useState({ sortKey: 'facturacion', sortDir: 'desc' })

  const products = useMemo(
    () => filterAndSortProducts(data?.by_product, { query, category, ...sort }),
    [data, query, category, sort]
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="animate-spin text-blue-500 mr-2" size={20} />
        <span className="text-gray-600">Cargando ventas por producto...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
        <AlertTriangle className="text-red-500 flex-shrink-0" size={20} />
        <p className="text-red-700">{error}</p>
      </div>
    )
  }

  if (!data) return null

  const { summary, by_category: categories } = data

  if (summary.productos === 0) {
    return (
      <div className="space-y-4">
        <CoverageNotice summary={summary} />
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <Package className="mx-auto text-gray-400 mb-3" size={32} />
          <p className="text-gray-500">No hay productos vendidos con detalle en este período</p>
        </div>
      </div>
    )
  }

  const onSort = (column) => setSort((current) => nextSort(current, column))
  const maxCategory = Math.max(...categories.map((c) => c.porcentaje), 1)

  return (
    <div className="space-y-6">
      <CoverageNotice summary={summary} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          ['Facturación por productos', formatCurrency(summary.facturacion)],
          ['Unidades vendidas', formatUnits(summary.unidades)],
          ['Productos distintos', summary.productos],
          ['Ventas con detalle', `${summary.cobertura_ventas_pct}%`],
        ].map(([label, value]) => (
          <div key={label} className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <p className="text-xs text-gray-500">{label}</p>
            <p className="text-xl font-bold text-gray-900 mt-1">{value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h3 className="text-base font-semibold text-gray-900">Por categoría</h3>
        </div>
        <div className="divide-y divide-gray-50">
          {categories.map((c) => (
            <button
              key={c.categoria}
              type="button"
              onClick={() => setCategory(category === c.categoria ? '' : c.categoria)}
              className={`w-full text-left px-6 py-3 hover:bg-gray-50 ${category === c.categoria ? 'bg-blue-50' : ''}`}
            >
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-gray-900">{c.categoria}</span>
                <span className="text-gray-600">
                  {formatCurrency(c.facturacion)} · {formatUnits(c.unidades)} u. · {c.porcentaje}%
                </span>
              </div>
              <div className="mt-2 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full" style={{ width: `${(c.porcentaje / maxCategory) * 100}%` }} />
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-gray-900">Por producto</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              A: el grupo que hace el 80% de la facturación · B: hasta el 95% · C: el resto
              {category && <> · filtrando <strong>{category}</strong></>}
            </p>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar producto"
              className="pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm w-full md:w-64"
            />
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500">
              <tr>
                <SortHeader label="Producto" column="producto" sort={sort} onSort={onSort} align="left" />
                <th className="px-4 py-3 font-medium text-left">Categoría</th>
                <SortHeader label="Unidades" column="unidades" sort={sort} onSort={onSort} />
                <SortHeader label="Facturación" column="facturacion" sort={sort} onSort={onSort} />
                <SortHeader label="Precio prom." column="precio_promedio" sort={sort} onSort={onSort} />
                <SortHeader label="% fact." column="porcentaje" sort={sort} onSort={onSort} />
                <SortHeader label="vs. anterior" column="variacion" sort={sort} onSort={onSort} />
                <th className="px-4 py-3 font-medium text-center">Clase</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {products.map((p) => (
                <tr key={`${p.producto}|${p.variante}|${p.categoria}`} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{productLabel(p)}</td>
                  <td className="px-4 py-3 text-gray-600">{p.categoria}</td>
                  <td className="px-4 py-3 text-right">{formatUnits(p.unidades)}</td>
                  <td className="px-4 py-3 text-right font-medium">{formatCurrency(p.facturacion)}</td>
                  <td className="px-4 py-3 text-right text-gray-600">{formatCurrency(p.precio_promedio)}</td>
                  <td className="px-4 py-3 text-right text-gray-600">{p.porcentaje}%</td>
                  <td className="px-4 py-3 text-right"><Variation value={p.variacion} /></td>
                  <td className="px-4 py-3 text-center">
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${CLASS_STYLES[p.clase]}`}>{p.clase}</span>
                  </td>
                </tr>
              ))}
              {products.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-6 text-center text-gray-500">Ningún producto coincide con la búsqueda</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

const VIEWS = [['period', 'Período'], ['compare', 'Comparar meses']]

// Pestaña Productos: la vista por período (con el selector de Reportes) o la comparación de dos meses.
const ProductsTab = (props) => {
  const [view, setView] = useState('period')
  return (
    <div className="space-y-4">
      <div className="inline-flex rounded-lg border border-gray-200 bg-white p-1">
        {VIEWS.map(([key, label]) => (
          <button key={key} type="button" onClick={() => setView(key)}
            className={`rounded-md px-3 py-1.5 text-sm ${view === key ? 'bg-galia-plum text-galia-cream' : 'text-gray-600 hover:text-gray-900'}`}>
            {label}
          </button>
        ))}
      </div>
      {view === 'period' ? <PeriodView {...props} /> : <ProductsCompare formatCurrency={props.formatCurrency} />}
    </div>
  )
}

export default ProductsTab
