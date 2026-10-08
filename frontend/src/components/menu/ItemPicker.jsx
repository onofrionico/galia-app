import { useState } from 'react'
import { normalizeText, variantSummary } from '../../utils/menuFormat'

// items: [{ id, name, categoryName, variants }]
const ItemPicker = ({ items, excludeId, onSelect, onCancel }) => {
  const [query, setQuery] = useState('')
  const needle = normalizeText(query.trim())
  const visible = items
    .filter((i) => i.id !== excludeId)
    .filter((i) => !needle || normalizeText(`${i.name} ${i.categoryName}`).includes(needle))
    .slice(0, 50)

  return (
    <div className="mt-2 border border-gray-200 rounded p-2 bg-gray-50">
      <input autoFocus value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar ítem…" className="w-full px-3 py-2 border border-gray-300 rounded text-sm" />
      <ul className="max-h-56 overflow-y-auto mt-2 divide-y divide-gray-200">
        {visible.length === 0 && <li className="p-2 text-sm text-gray-500">Sin resultados.</li>}
        {visible.map((i) => (
          <li key={i.id}>
            <button type="button" onClick={() => onSelect(i)} className="w-full text-left p-2 text-sm hover:bg-white">
              {i.name} <span className="text-gray-500">· {i.categoryName} · {variantSummary(i.variants)}</span>
            </button>
          </li>
        ))}
      </ul>
      <button type="button" onClick={onCancel} className="mt-2 text-sm text-gray-600 hover:text-gray-900">Cancelar</button>
    </div>
  )
}

export default ItemPicker
