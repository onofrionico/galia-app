import { useState, useEffect, useCallback } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Plus, Save, Power } from 'lucide-react'
import recipesService from '@/services/recipesService'
import IngredientRow, { UNIT_SUGGESTIONS } from '@/components/recipes/IngredientRow'
import StepEditor from '@/components/recipes/StepEditor'
import ProductLinkPanel from '@/components/recipes/ProductLinkPanel'

const str = (v) => (v === null || v === undefined ? '' : String(v))
const orNull = (v) => {
  const t = String(v).trim()
  return t === '' ? null : t
}
const numOrNull = (v) => {
  const t = String(v).trim()
  return t === '' ? null : Number(t)
}

let keySeed = 0
const nextKey = () => `k${++keySeed}`

const emptyIngredient = () => ({ key: nextKey(), kind: 'supply', ref_id: null, name: '', quantity: '', unit: '', note: '' })
const emptyStep = () => ({
  key: nextKey(), title: '', instruction: '', temperature_c: '', time_min: '', time_max: '', doneness: '', tip: '',
})

const emptyForm = () => ({
  name: '', yield_quantity: '', yield_unit: '', total_time_minutes: '', advance_notes: '', notes: '', pending_notes: '',
})

const fromRecipe = (r) => ({
  form: {
    name: r.name || '',
    yield_quantity: str(r.yield_quantity),
    yield_unit: str(r.yield_unit),
    total_time_minutes: str(r.total_time_minutes),
    advance_notes: str(r.advance_notes),
    notes: str(r.notes),
    pending_notes: str(r.pending_notes),
  },
  ingredients: r.ingredients.map((i) => ({
    key: nextKey(),
    kind: i.sub_recipe ? 'recipe' : 'supply',
    ref_id: i.sub_recipe ? i.sub_recipe.id : i.supply?.id ?? null,
    name: i.sub_recipe ? i.sub_recipe.name : i.supply?.name ?? '',
    quantity: str(i.quantity),
    unit: str(i.unit),
    note: str(i.note),
  })),
  steps: r.steps.map((s) => ({
    key: nextKey(),
    title: str(s.title),
    instruction: str(s.instruction),
    temperature_c: str(s.temperature_c),
    time_min: str(s.time_min),
    time_max: str(s.time_max),
    doneness: str(s.doneness),
    tip: str(s.tip),
  })),
})

const inputClass = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-base text-gray-900'

const Field = ({ label, className = '', children }) => (
  <label className={`block text-sm text-gray-600 ${className}`}>
    {label}
    {children}
  </label>
)

export default function RecipeEditor() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isNew = id === undefined

  const [recipe, setRecipe] = useState(null)
  const [form, setForm] = useState(emptyForm())
  const [ingredients, setIngredients] = useState([])
  const [steps, setSteps] = useState([])
  const [supplies, setSupplies] = useState([])
  const [bases, setBases] = useState([])
  const [loading, setLoading] = useState(!isNew)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const applyRecipe = useCallback((r) => {
    const parsed = fromRecipe(r)
    setRecipe(r)
    setForm(parsed.form)
    setIngredients(parsed.ingredients)
    setSteps(parsed.steps)
  }, [])

  useEffect(() => {
    let cancelled = false
    recipesService
      .supplies()
      .then((list) => { if (!cancelled) setSupplies(list) })
      .catch((err) => {
        if (!cancelled) setError(err.response?.status === 403
          ? 'No tenés permiso para elegir insumos'
          : 'No se pudieron cargar los insumos')
      })
    recipesService
      .list({ bases: true })
      .then((list) => { if (!cancelled) setBases(list) })
      .catch(() => { if (!cancelled) setError('No se pudieron cargar las bases') })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    if (isNew) return undefined
    let cancelled = false
    setLoading(true)
    recipesService
      .get(id)
      .then((r) => { if (!cancelled) applyRecipe(r) })
      .catch((err) => {
        if (!cancelled) setError(err.response?.status === 404 ? 'La receta no existe' : 'No se pudo cargar la receta')
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [id, isNew, applyRecipe])

  const options = [
    ...supplies.map((s) => ({ kind: 'supply', id: s.id, name: s.name, unit: s.unit })),
    ...bases
      .filter((b) => String(b.id) !== String(id))
      .map((b) => ({ kind: 'recipe', id: b.id, name: b.name, unit: b.yield_unit || '' })),
  ]

  const setField = (field) => (e) => setForm({ ...form, [field]: e.target.value })
  const patch = (setList) => (key, changes) =>
    setList((list) => list.map((item) => (item.key === key ? { ...item, ...changes } : item)))
  const patchIngredient = patch(setIngredients)
  const patchStep = patch(setSteps)

  const moveStep = (index, delta) =>
    setSteps((list) => {
      const target = index + delta
      if (target < 0 || target >= list.length) return list
      const copy = [...list]
      ;[copy[index], copy[target]] = [copy[target], copy[index]]
      return copy
    })

  const buildPayload = () => ({
    name: form.name.trim(),
    yield_quantity: numOrNull(form.yield_quantity),
    yield_unit: orNull(form.yield_unit),
    total_time_minutes: numOrNull(form.total_time_minutes),
    advance_notes: orNull(form.advance_notes),
    notes: orNull(form.notes),
    pending_notes: orNull(form.pending_notes),
    ingredients: ingredients.map((i) => ({
      ...(i.kind === 'recipe' ? { sub_recipe_id: i.ref_id } : { supply_id: i.ref_id }),
      quantity: numOrNull(i.quantity),
      unit: orNull(i.unit),
      note: orNull(i.note),
    })),
    steps: steps.map((s) => ({
      title: orNull(s.title),
      instruction: orNull(s.instruction),
      temperature_c: numOrNull(s.temperature_c),
      time_min: numOrNull(s.time_min),
      time_max: numOrNull(s.time_max),
      doneness: orNull(s.doneness),
      tip: orNull(s.tip),
    })),
  })

  const handleSave = async (e) => {
    e.preventDefault()
    setError('')
    setNotice('')
    if (!form.name.trim()) {
      setError('La receta necesita un nombre')
      return
    }
    if (ingredients.some((i) => !i.ref_id)) {
      setError('Elegí el insumo o la base de cada ingrediente, o quitá la fila vacía')
      return
    }
    const untitled = steps.findIndex((s) => !s.title.trim())
    if (untitled !== -1) {
      setError(`Paso ${untitled + 1}: falta el título`)
      return
    }
    setSaving(true)
    try {
      if (isNew) {
        const created = await recipesService.create(buildPayload())
        navigate(`/recipes/${created.id}/edit`, { replace: true })
      } else {
        const updated = await recipesService.update(id, buildPayload())
        applyRecipe(updated)
        setNotice('Receta guardada')
      }
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo guardar la receta')
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } finally {
      setSaving(false)
    }
  }

  const handleDeactivate = async () => {
    if (!window.confirm(`¿Desactivar la receta "${recipe.name}"? Dejará de aparecer en la lista.`)) return
    setError('')
    setNotice('')
    setSaving(true)
    try {
      await recipesService.remove(id)
      navigate('/recipes')
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo desactivar la receta')
      window.scrollTo({ top: 0, behavior: 'smooth' })
      setSaving(false)
    }
  }

  const refreshRecipe = async () => {
    try {
      setRecipe(await recipesService.get(id))
    } catch {
      /* el vínculo ya se guardó; el estado se refresca en la próxima carga */
    }
  }

  if (loading) return <div className="p-4 text-lg text-gray-500">Cargando…</div>
  if (!isNew && !recipe) {
    return (
      <div className="p-4 max-w-2xl mx-auto">
        <p className="text-lg text-red-700">{error || 'No se pudo cargar la receta'}</p>
        <Link to="/recipes" className="text-galia-plum underline">Volver a recetas</Link>
      </div>
    )
  }

  return (
    <div className="p-4 sm:p-6 max-w-4xl mx-auto text-gray-900 space-y-6">
      <form onSubmit={handleSave} className="space-y-6">
      <datalist id="recipe-unit-suggestions">
        {UNIT_SUGGESTIONS.map((u) => <option key={u} value={u} />)}
      </datalist>

      <div className="flex items-center justify-between gap-3">
        <Link to={isNew ? '/recipes' : `/recipes/${id}`} className="inline-flex items-center gap-1 text-base text-galia-plum">
          <ArrowLeft className="w-4 h-4" /> {isNew ? 'Recetas' : 'Ver receta'}
        </Link>
        <button
          type="submit"
          disabled={saving}
          className="inline-flex items-center gap-2 px-5 py-2 bg-galia-plum text-white rounded-lg hover:bg-galia-plum-dark font-medium disabled:opacity-50"
        >
          <Save className="w-4 h-4" /> {saving ? 'Guardando…' : 'Guardar'}
        </button>
      </div>

      <h1 className="text-2xl font-bold">{isNew ? 'Nueva receta' : `Editar ${recipe.name}`}</h1>

      {error && <p role="alert" className="p-3 rounded-lg bg-red-50 border border-red-300 text-red-800">{error}</p>}
      {notice && <p className="p-3 rounded-lg bg-green-50 border border-green-300 text-green-800">{notice}</p>}

      <section className="grid grid-cols-1 md:grid-cols-6 gap-3 p-4 border border-gray-200 rounded-xl bg-white">
        <Field label="Nombre" className="md:col-span-6">
          <input type="text" value={form.name} onChange={setField('name')} className={inputClass} />
        </Field>
        <Field label="Rinde (cantidad)" className="md:col-span-2">
          <input type="number" inputMode="decimal" step="any" min="0" value={form.yield_quantity}
            onChange={setField('yield_quantity')} className={inputClass} />
        </Field>
        <Field label="Unidad del rendimiento" className="md:col-span-2">
          <input type="text" list="recipe-unit-suggestions" value={form.yield_unit}
            onChange={setField('yield_unit')} placeholder="Ej: unidad, kg" className={inputClass} />
        </Field>
        <Field label="Tiempo total (min)" className="md:col-span-2">
          <input type="number" inputMode="numeric" min="0" value={form.total_time_minutes}
            onChange={setField('total_time_minutes')} className={inputClass} />
        </Field>
        <Field label="Para dejar listo con anticipación" className="md:col-span-6">
          <textarea rows={2} value={form.advance_notes} onChange={setField('advance_notes')} className={inputClass} />
        </Field>
        <Field label="Notas" className="md:col-span-6">
          <textarea rows={2} value={form.notes} onChange={setField('notes')} className={inputClass} />
        </Field>
        <Field label="A completar (lo que falta definir)" className="md:col-span-6">
          <textarea rows={2} value={form.pending_notes} onChange={setField('pending_notes')} className={inputClass} />
        </Field>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-bold">Ingredientes</h2>
        <p className="text-sm text-gray-500">La cantidad puede quedar vacía si todavía no está definida.</p>
        {ingredients.map((ing) => (
          <IngredientRow
            key={ing.key}
            ingredient={ing}
            options={options}
            onChange={(changes) => patchIngredient(ing.key, changes)}
            onRemove={() => setIngredients((list) => list.filter((i) => i.key !== ing.key))}
          />
        ))}
        <button
          type="button"
          onClick={() => setIngredients((list) => [...list, emptyIngredient()])}
          className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium"
        >
          <Plus className="w-4 h-4" /> Agregar ingrediente
        </button>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-bold">Pasos</h2>
        {steps.map((step, index) => (
          <StepEditor
            key={step.key}
            step={step}
            index={index}
            total={steps.length}
            onChange={(changes) => patchStep(step.key, changes)}
            onRemove={() => setSteps((list) => list.filter((s) => s.key !== step.key))}
            onMove={(delta) => moveStep(index, delta)}
          />
        ))}
        <button
          type="button"
          onClick={() => setSteps((list) => [...list, emptyStep()])}
          className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium"
        >
          <Plus className="w-4 h-4" /> Agregar paso
        </button>
      </section>

      </form>

      {isNew ? (
        <p className="text-sm text-gray-500">Guardá la receta para poder vincularla a un producto.</p>
      ) : (
        <>
          <ProductLinkPanel key={recipe.id} recipe={recipe} onLinked={refreshRecipe} />
          <div className="pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={handleDeactivate}
              disabled={saving}
              className="inline-flex items-center gap-2 px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 font-medium disabled:opacity-50"
            >
              <Power className="w-4 h-4" /> Desactivar receta
            </button>
          </div>
        </>
      )}
    </div>
  )
}
