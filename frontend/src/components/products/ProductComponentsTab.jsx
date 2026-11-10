import { useEffect, useState } from 'react'
import { Plus, Search, X } from 'lucide-react'
import productsService from '@/services/productsService'

const errorText = (err, fallback) => err.response?.data?.error || fallback

// Buscador de variantes del catálogo para elegir un componente.
function VariantPicker({ onPick }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([])
      return undefined
    }
    const timer = setTimeout(() => {
      productsService.searchVariants(query.trim()).then(setResults).catch(() => setResults([]))
    }, 250)
    return () => clearTimeout(timer)
  }, [query])

  return (
    <div className="relative">
      <Search className="absolute left-2.5 top-2.5 text-gray-400" size={16} />
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar producto para agregar…"
        className="w-full pl-8 pr-3 py-2 border rounded-lg text-sm" />
      {results.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {results.map((variant) => (
            <li key={variant.id}>
              <button type="button" onClick={() => { onPick(variant); setQuery(''); setResults([]) }}
                className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50">
                {variant.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// Productos que trae este producto (por ejemplo, un combo con 2 medialunas), para el reporte de Producción.
export default function ProductComponentsTab({ productId }) {
  const [variants, setVariants] = useState([])
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const apply = (data) => {
    setVariants(data.variants)
    setRows(data.components.map((c) => ({
      variant_id: c.variant_id, component_variant_id: c.component_variant_id, label: c.component_label,
      quantity: String(c.quantity),
    })))
  }

  useEffect(() => {
    setLoading(true)
    productsService.getComponents(productId)
      .then(apply)
      .catch((err) => setError(errorText(err, 'No se pudieron cargar los componentes')))
      .finally(() => setLoading(false))
  }, [productId])

  const addComponent = (variant) => {
    if (!variants.length) return
    setRows((prev) => [...prev, {
      variant_id: variants[0].id, component_variant_id: variant.id, label: variant.label, quantity: '1',
    }])
    setMessage('')
  }

  const update = (index, changes) => {
    setRows((prev) => prev.map((row, i) => (i === index ? { ...row, ...changes } : row)))
    setMessage('')
  }

  const save = async () => {
    setSaving(true)
    setError('')
    setMessage('')
    try {
      const data = await productsService.saveComponents(productId, rows.map((row) => ({
        variant_id: Number(row.variant_id), component_variant_id: row.component_variant_id,
        quantity: Number(String(row.quantity).replace(',', '.')),
      })))
      apply(data)
      setMessage('Guardado')
    } catch (err) {
      setError(errorText(err, 'No se pudo guardar'))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="py-8 text-center text-gray-500">Cargando…</div>

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600">
        Si este producto trae otros productos —por ejemplo, un combo con 2 medialunas— cargalos acá y el reporte de
        Producción los va a contar. Lo genérico (como “infusión”) no hace falta cargarlo.
      </p>

      {rows.length === 0 && <p className="text-sm text-gray-500">Este producto no tiene componentes.</p>}

      {rows.length > 0 && (
        <div className="space-y-2">
          {rows.map((row, index) => (
            <div key={`${row.variant_id}-${row.component_variant_id}-${index}`} className="flex flex-wrap items-center gap-2">
              {variants.length > 1 && (
                <select value={row.variant_id} onChange={(e) => update(index, { variant_id: Number(e.target.value) })}
                  className="border rounded-lg px-2 py-1.5 text-sm" aria-label="Variante del combo">
                  {variants.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}
                </select>
              )}
              <span className="flex-1 min-w-[10rem] text-sm text-gray-900">{row.label}</span>
              <input value={row.quantity} onChange={(e) => update(index, { quantity: e.target.value })}
                inputMode="decimal" className="w-20 border rounded-lg px-2 py-1.5 text-sm text-right" aria-label="Cantidad" />
              <span className="text-sm text-gray-500">u.</span>
              <button type="button" onClick={() => setRows((prev) => prev.filter((_, i) => i !== index))}
                className="p-1 text-gray-400 hover:text-red-600" aria-label="Quitar"><X size={16} /></button>
            </div>
          ))}
        </div>
      )}

      <div className="max-w-md flex items-center gap-2">
        <Plus size={16} className="text-gray-400" />
        <div className="flex-1"><VariantPicker onPick={addComponent} /></div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {message && <p className="text-sm text-green-600">{message}</p>}

      <button type="button" onClick={save} disabled={saving}
        className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
        {saving ? 'Guardando…' : 'Guardar'}
      </button>
    </div>
  )
}
