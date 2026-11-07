import { useState, useEffect } from 'react'
import { Link2, Info } from 'lucide-react'
import productsService from '@/services/productsService'
import recipesService from '@/services/recipesService'

// Vincula una receta ya guardada con un producto y decide si gobierna el stock.
export default function ProductLinkPanel({ recipe, onLinked }) {
  const linked = recipe.product
  const [products, setProducts] = useState([])
  const [productId, setProductId] = useState(linked ? String(linked.id) : '')
  const [stockActive, setStockActive] = useState(Boolean(linked?.has_recipe))
  const [units, setUnits] = useState({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    let cancelled = false
    productsService
      .getProducts({ per_page: 200 })
      .then((res) => { if (!cancelled) setProducts(res.products || []) })
      .catch(() => { if (!cancelled) setError('No se pudieron cargar los productos') })
    return () => { cancelled = true }
  }, [])

  const isCurrent = Boolean(linked) && String(linked.id) === productId
  const selected = products.find((p) => String(p.id) === productId) || null
  const variants = isCurrent
    ? linked.variants
    : (selected?.variants || []).map((v) => ({ id: v.id, name: v.name, recipe_units: v.recipe_units ?? null }))

  const trackStock = selected ? Boolean(selected.track_stock) : isCurrent && Boolean(linked.track_stock)
  const hasYield = Number(recipe.yield_quantity) > 0 && Boolean(recipe.yield_unit)
  const blockedReason = !productId
    ? 'Elegí un producto'
    : !hasYield
      ? 'La receta necesita un rendimiento para descontar stock'
      : trackStock
        ? 'El producto ya controla stock propio; desactivalo en el producto para usar la receta'
        : ''

  const unitsFor = (v) => units[v.id] ?? v.recipe_units ?? 1

  const save = async () => {
    setSaving(true)
    setError('')
    setSaved(false)
    try {
      const variantUnits = {}
      if (productId) variants.forEach((v) => { variantUnits[v.id] = Number(unitsFor(v)) })
      await recipesService.linkProduct(recipe.id, {
        product_id: productId ? Number(productId) : null,
        stock_active: Boolean(productId) && stockActive && !blockedReason,
        variant_units: variantUnits,
      })
      setSaved(true)
      if (onLinked) await onLinked()
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo guardar el vínculo')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="space-y-4 p-4 border border-gray-200 rounded-xl bg-white">
      <div className="flex items-center gap-2">
        <Link2 className="w-5 h-5 text-galia-plum" />
        <h2 className="text-xl font-bold">Producto de la carta</h2>
      </div>

      {error && <p className="p-3 rounded-lg bg-red-50 border border-red-300 text-red-800">{error}</p>}
      {saved && !error && <p className="p-3 rounded-lg bg-green-50 border border-green-300 text-green-800">Vínculo guardado</p>}

      <label className="block text-sm text-gray-600">
        Producto
        <select
          value={productId}
          onChange={(e) => { setProductId(e.target.value); setUnits({}); setSaved(false) }}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-base text-gray-900"
        >
          <option value="">Sin producto (receta base)</option>
          {linked && !products.some((p) => p.id === linked.id) && <option value={linked.id}>{linked.name}</option>}
          {products.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
      </label>

      <div>
        <label className={`flex items-center gap-2 ${blockedReason ? 'text-gray-400' : 'text-gray-900'}`}>
          <input
            type="checkbox"
            checked={stockActive && !blockedReason}
            disabled={Boolean(blockedReason)}
            onChange={(e) => setStockActive(e.target.checked)}
            className="w-5 h-5"
          />
          Usar esta receta para el stock
        </label>
        {blockedReason && (
          <p className="mt-1 flex items-center gap-1 text-sm text-gray-500">
            <Info className="w-4 h-4 shrink-0" /> {blockedReason}
          </p>
        )}
      </div>

      {productId && variants.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-gray-600">Unidades de la tanda que usa cada variante</p>
          {variants.map((v) => (
            <div key={v.id} className="flex items-center justify-between gap-3">
              <span>{v.name}</span>
              <input
                type="number"
                inputMode="decimal"
                step="any"
                min="0"
                value={unitsFor(v)}
                onChange={(e) => setUnits({ ...units, [v.id]: e.target.value })}
                aria-label={`Unidades de ${v.name}`}
                className="w-28 border border-gray-300 rounded-lg px-3 py-2"
              />
            </div>
          ))}
        </div>
      )}

      <button
        type="button"
        onClick={save}
        disabled={saving}
        className="px-4 py-2 bg-galia-plum text-white rounded-lg hover:bg-galia-plum-dark font-medium disabled:opacity-50"
      >
        {saving ? 'Guardando…' : 'Guardar vínculo'}
      </button>
    </section>
  )
}
