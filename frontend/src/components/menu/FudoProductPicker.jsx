import { useState } from 'react'
import { normalizeText, formatPrice } from '../../utils/menuFormat'

// products: [{ fudo_id, name, price, category_name, linked }]
// allowedIds: ids que se pueden elegir aunque estén vinculados (los del propio ítem)
// excludedIds: ids ya usados en otras variantes de este formulario
const FudoProductPicker = ({ products, allowedIds, excludedIds, onSelect, onCancel }) => {
  const [query, setQuery] = useState('')
  const needle = normalizeText(query.trim())
  const visible = products
    .filter((p) => !needle || normalizeText(`${p.name} ${p.category_name || ''}`).includes(needle))
    .slice(0, 50)

  return (
    <div className="mt-2 border border-gray-200 rounded p-2 bg-gray-50">
      <input
        autoFocus
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Buscar producto en Fudo…"
        className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
      />
      <ul className="max-h-56 overflow-y-auto mt-2 divide-y divide-gray-200">
        {products.length === 0 && <li className="p-2 text-sm text-gray-500">No hay productos: tocá "Sincronizar Fudo" primero.</li>}
        {visible.map((p) => {
          const taken = (p.linked && !allowedIds.has(p.fudo_id)) || excludedIds.has(p.fudo_id)
          return (
            <li key={p.fudo_id}>
              <button
                type="button"
                disabled={taken}
                onClick={() => onSelect(p)}
                className="w-full text-left p-2 text-sm hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed flex justify-between gap-2"
              >
                <span>
                  {p.name}
                  {p.category_name && <span className="text-gray-500"> · {p.category_name}</span>}
                  {taken && <span className="text-gray-500"> · ya en la carta</span>}
                </span>
                <span className="text-gray-700">{formatPrice(p.price)}</span>
              </button>
            </li>
          )
        })}
      </ul>
      <button type="button" onClick={onCancel} className="mt-2 text-sm text-gray-600 hover:text-gray-900">Cancelar</button>
    </div>
  )
}

export default FudoProductPicker
