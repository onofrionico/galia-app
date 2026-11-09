import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, Search, Plus, Clock, Utensils, AlertCircle } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import recipesService from '@/services/recipesService'
import { formatMoney } from '@/utils/moneyFormat'
import { formatStepTime, formatYield } from '@/components/recipes/format'

const FILTERS = [
  { id: 'all', label: 'Todas' },
  { id: 'products', label: 'Productos' },
  { id: 'bases', label: 'Bases' },
]

export default function Recipes() {
  const { hasModuleAccess } = useAuth()
  const [recipes, setRecipes] = useState([])
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    recipesService
      .list({ q: search.trim(), bases: filter === 'bases' })
      .then((data) => { if (!cancelled) setRecipes(data) })
      .catch(() => { if (!cancelled) setError('No se pudieron cargar las recetas') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [search, filter])

  const visible = filter === 'products' ? recipes.filter((r) => !r.is_base) : recipes

  return (
    <div className="p-4 sm:p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-3">
          <BookOpen className="w-6 h-6 text-galia-plum" />
          <h1 className="text-2xl font-bold text-gray-900">Recetas</h1>
        </div>
        {hasModuleAccess('RecipesAdmin') && (
          <Link
            to="/recipes/new"
            className="flex items-center gap-2 px-4 py-2 bg-galia-plum text-white rounded-lg hover:bg-galia-plum-dark text-sm font-medium"
          >
            <Plus className="w-4 h-4" /> Nueva receta
          </Link>
        )}
      </div>

      <div className="relative mb-3">
        <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar receta"
          className="w-full pl-10 pr-3 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-galia-plum-light"
        />
      </div>

      <div className="flex gap-2 mb-5">
        {FILTERS.map((f) => (
          <button
            key={f.id}
            type="button"
            onClick={() => setFilter(f.id)}
            className={`px-4 py-2 rounded-full text-sm font-medium border ${
              filter === f.id
                ? 'bg-galia-plum text-white border-galia-plum'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>}

      {loading ? (
        <p className="text-gray-500">Cargando…</p>
      ) : visible.length === 0 ? (
        <p className="text-gray-500">No hay recetas para mostrar.</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {visible.map((r) => {
            const yieldText = formatYield(r.yield_quantity, r.yield_unit)
            const timeText = r.total_time_minutes ? formatStepTime(r.total_time_minutes, null) : ''
            return (
              <Link
                key={r.id}
                to={`/recipes/${r.id}`}
                className="block bg-white border border-gray-200 rounded-xl p-4 hover:border-galia-plum-light hover:shadow-sm"
              >
                <div className="flex items-start justify-between gap-2">
                  <h2 className="text-lg font-semibold text-gray-900">{r.name}</h2>
                  {r.has_pending && (
                    <span className="shrink-0 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 text-xs font-medium">
                      <AlertCircle className="w-3 h-3" /> A completar
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-500 mt-0.5">{r.is_base ? 'Base' : r.product?.name}</p>
                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3 text-sm text-gray-700">
                  {yieldText && (
                    <span className="inline-flex items-center gap-1"><Utensils className="w-4 h-4 text-gray-400" /> Rinde {yieldText}</span>
                  )}
                  {timeText && (
                    <span className="inline-flex items-center gap-1"><Clock className="w-4 h-4 text-gray-400" /> {timeText}</span>
                  )}
                </div>
                {r.unit_cost != null && (
                  <p className="mt-2 text-sm text-gray-600">
                    Costo por unidad: <span className="font-semibold">$ {formatMoney(r.unit_cost)}</span>
                    {r.cost_complete === false && <span className="text-amber-700"> (incompleto)</span>}
                  </p>
                )}
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
