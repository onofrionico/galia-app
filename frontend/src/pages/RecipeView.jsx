import { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Pencil, Clock, Thermometer, Eye, AlertTriangle, Utensils, Info } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import recipesService from '@/services/recipesService'
import { formatMoney } from '@/utils/moneyFormat'
import { formatStepTime, formatQuantity, formatYield } from '@/components/recipes/format'

const Chip = ({ icon: Icon, className = 'bg-gray-100 text-gray-800', children }) => (
  <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-base font-medium ${className}`}>
    <Icon className="w-4 h-4 shrink-0" /> {children}
  </span>
)

export default function RecipeView() {
  const { id } = useParams()
  const { hasModuleAccess } = useAuth()
  const [recipe, setRecipe] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    recipesService
      .get(id)
      .then((data) => { if (!cancelled) setRecipe(data) })
      .catch((err) => {
        if (!cancelled) setError(err.response?.status === 404 ? 'La receta no existe' : 'No se pudo cargar la receta')
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [id])

  if (loading) return <div className="p-4 text-lg text-gray-500">Cargando…</div>
  if (error || !recipe) {
    return (
      <div className="p-4 max-w-2xl mx-auto">
        <p className="text-lg text-red-700">{error || 'No se pudo cargar la receta'}</p>
        <Link to="/recipes" className="text-galia-plum underline">Volver a recetas</Link>
      </div>
    )
  }

  const yieldText = formatYield(recipe.yield_quantity, recipe.yield_unit)
  const totalTime = recipe.total_time_minutes ? formatStepTime(recipe.total_time_minutes, null) : ''

  return (
    <div className="p-4 sm:p-6 max-w-2xl mx-auto text-lg text-gray-900 space-y-6">
      <div className="flex items-center justify-between">
        <Link to="/recipes" className="inline-flex items-center gap-1 text-base text-galia-plum">
          <ArrowLeft className="w-4 h-4" /> Recetas
        </Link>
        {hasModuleAccess('RecipesAdmin') && (
          <Link
            to={`/recipes/${recipe.id}/edit`}
            className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-base font-medium hover:bg-gray-50"
          >
            <Pencil className="w-4 h-4" /> Editar
          </Link>
        )}
      </div>

      <header className="space-y-3">
        <h1 className="text-3xl font-bold break-words">{recipe.name}</h1>
        <div className="flex flex-wrap gap-2">
          {yieldText && <Chip icon={Utensils}>Rinde {yieldText}</Chip>}
          {totalTime && <Chip icon={Clock}>{totalTime} en total</Chip>}
        </div>
        {recipe.product && <p className="text-base text-gray-500">Producto: {recipe.product.name}</p>}
        {recipe.advance_notes && (
          <div className="flex gap-3 p-4 rounded-xl bg-blue-50 border-2 border-blue-300 text-blue-900">
            <Info className="w-6 h-6 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Para dejar listo con anticipación</p>
              <p className="whitespace-pre-line">{recipe.advance_notes}</p>
            </div>
          </div>
        )}
        {recipe.pending_notes && (
          <div className="flex gap-3 p-4 rounded-xl bg-amber-50 border border-amber-300 text-amber-900">
            <AlertTriangle className="w-6 h-6 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Falta completar</p>
              <p className="whitespace-pre-line">{recipe.pending_notes}</p>
            </div>
          </div>
        )}
      </header>

      <section>
        <h2 className="text-2xl font-bold mb-3">Ingredientes</h2>
        <ul className="divide-y divide-gray-200 bg-white border border-gray-200 rounded-xl">
          {recipe.ingredients.map((ing) => {
            const name = ing.supply?.name || ing.sub_recipe?.name
            const pending = ing.quantity == null && !ing.note
            return (
              <li key={ing.id} className="flex gap-4 p-3">
                <span className={`w-28 shrink-0 font-bold ${pending ? 'text-amber-700' : ''}`}>
                  {formatQuantity(ing.quantity, ing.unit, ing.note)}
                </span>
                <span className="min-w-0 break-words">
                  {ing.sub_recipe ? (
                    <Link to={`/recipes/${ing.sub_recipe.id}`} className="text-galia-plum underline">{name}</Link>
                  ) : (
                    name
                  )}
                  {ing.note && ing.quantity != null && <span className="block text-base text-gray-500">{ing.note}</span>}
                </span>
              </li>
            )
          })}
        </ul>
      </section>

      {recipe.steps.length > 0 && (
        <section>
          <h2 className="text-2xl font-bold mb-3">Preparación</h2>
          <ol className="space-y-4">
            {recipe.steps.map((step, index) => {
              const time = formatStepTime(step.time_min, step.time_max)
              return (
                <li key={step.id} className="flex gap-3 bg-white border border-gray-200 rounded-xl p-4">
                  <span className="w-9 h-9 shrink-0 rounded-full bg-galia-plum text-white font-bold flex items-center justify-center">
                    {index + 1}
                  </span>
                  <div className="min-w-0 space-y-2">
                    {step.title && <h3 className="text-xl font-semibold">{step.title}</h3>}
                    <p className="whitespace-pre-line break-words">{step.instruction}</p>
                    {(step.temperature_c != null || time || step.doneness || step.tip) && (
                      <div className="flex flex-wrap gap-2 pt-1">
                        {step.temperature_c != null && (
                          <Chip icon={Thermometer} className="bg-red-50 text-red-800">{step.temperature_c} °C</Chip>
                        )}
                        {time && <Chip icon={Clock} className="bg-gray-100 text-gray-800">{time}</Chip>}
                        {step.doneness && <Chip icon={Eye} className="bg-green-50 text-green-800">{step.doneness}</Chip>}
                        {step.tip && <Chip icon={AlertTriangle} className="bg-amber-50 text-amber-900">{step.tip}</Chip>}
                      </div>
                    )}
                  </div>
                </li>
              )
            })}
          </ol>
        </section>
      )}

      {recipe.notes && (
        <section>
          <h2 className="text-2xl font-bold mb-2">Notas</h2>
          <p className="whitespace-pre-line">{recipe.notes}</p>
        </section>
      )}

      {recipe.used_in?.length > 0 && (
        <section>
          <h2 className="text-2xl font-bold mb-2">Se usa en</h2>
          <ul className="flex flex-wrap gap-2">
            {recipe.used_in.map((r) => (
              <li key={r.id}>
                <Link to={`/recipes/${r.id}`} className="inline-block px-3 py-1 rounded-full bg-gray-100 text-galia-plum underline">{r.name}</Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {recipe.cost && (
        <section className="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-1">
          <h2 className="text-2xl font-bold mb-1">Costo</h2>
          <p>Tanda: <span className="font-semibold">$ {formatMoney(recipe.cost.batch_cost)}</span></p>
          {recipe.cost.unit_cost != null && (
            <p>Por unidad: <span className="font-semibold">$ {formatMoney(recipe.cost.unit_cost)}</span></p>
          )}
          {!recipe.cost.complete && (
            <div className="pt-2 text-base text-amber-900">
              <p className="font-semibold">Costo incompleto:</p>
              <ul className="list-disc pl-5">
                {recipe.cost.issues.map((issue, i) => <li key={i}>{issue}</li>)}
              </ul>
            </div>
          )}
        </section>
      )}

      {(recipe.updated_at || recipe.updated_by_name) && (
        <p className="text-sm text-gray-500">
          Última edición
          {recipe.updated_at && ` el ${new Date(recipe.updated_at).toLocaleDateString('es-AR')}`}
          {recipe.updated_by_name && ` por ${recipe.updated_by_name}`}
        </p>
      )}
    </div>
  )
}
