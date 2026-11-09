import { useState } from 'react'
import { Trash2, Layers } from 'lucide-react'

export const UNIT_SUGGESTIONS = ['g', 'kg', 'ml', 'L', 'unidad', 'cda', 'cdita', 'pizca']

const norm = (s) => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')

// Buscador combinado de insumos y bases. `options`: [{ kind: 'supply' | 'recipe', id, name, unit }]
function IngredientPicker({ ingredient, options, onPick }) {
  const [text, setText] = useState(ingredient.name)
  const [open, setOpen] = useState(false)

  const query = norm(text.trim())
  const matches = (query ? options.filter((o) => norm(o.name).includes(query)) : options).slice(0, 8)

  return (
    <div className="relative">
      <input
        type="text"
        value={text}
        onChange={(e) => { setText(e.target.value); setOpen(true) }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => { setOpen(false); setText(ingredient.name) }, 150)}
        placeholder="Buscar insumo o base"
        aria-label="Insumo o base"
        className={`w-full border rounded-lg px-3 py-2 ${ingredient.ref_id ? 'border-gray-300' : 'border-amber-400'}`}
      />
      {open && (
        <ul className="absolute z-20 mt-1 w-full max-h-60 overflow-auto bg-white border border-gray-300 rounded-lg shadow-lg">
          {matches.length === 0 && <li className="px-3 py-2 text-gray-500">Sin resultados</li>}
          {matches.map((o) => (
            <li key={`${o.kind}-${o.id}`}>
              <button
                type="button"
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => { onPick(o); setText(o.name); setOpen(false) }}
                className="w-full text-left px-3 py-2 hover:bg-gray-50 flex items-center justify-between gap-2"
              >
                <span>{o.name}</span>
                <span className="text-sm text-gray-500 shrink-0">
                  {o.kind === 'recipe' ? 'base' : o.unit}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function IngredientRow({ ingredient, options, onChange, onRemove }) {
  const pick = (o) =>
    onChange({
      kind: o.kind,
      ref_id: o.id,
      name: o.name,
      // Al cambiar de insumo o base la unidad vieja puede no convertirse: se toma la del elegido.
      unit: o.unit || '',
    })

  return (
    <div className="grid grid-cols-12 gap-2 items-start p-3 border border-gray-200 rounded-lg bg-white">
      <div className="col-span-12 md:col-span-4">
        <IngredientPicker key={`${ingredient.kind}-${ingredient.ref_id}`} ingredient={ingredient} options={options} onPick={pick} />
        {ingredient.kind === 'recipe' && (
          <span className="mt-1 inline-flex items-center gap-1 text-sm text-galia-plum">
            <Layers className="w-4 h-4" /> Base
          </span>
        )}
      </div>
      <input
        type="number"
        inputMode="decimal"
        step="any"
        min="0"
        value={ingredient.quantity}
        onChange={(e) => onChange({ quantity: e.target.value })}
        placeholder="Cantidad"
        aria-label="Cantidad"
        className="col-span-4 md:col-span-2 border border-gray-300 rounded-lg px-3 py-2"
      />
      <input
        type="text"
        list="recipe-unit-suggestions"
        value={ingredient.unit}
        onChange={(e) => onChange({ unit: e.target.value })}
        placeholder="Unidad"
        aria-label="Unidad"
        className="col-span-4 md:col-span-2 border border-gray-300 rounded-lg px-3 py-2"
      />
      <input
        type="text"
        value={ingredient.note}
        onChange={(e) => onChange({ note: e.target.value })}
        placeholder="Nota (opcional)"
        aria-label="Nota"
        className="col-span-12 md:col-span-3 border border-gray-300 rounded-lg px-3 py-2"
      />
      <button
        type="button"
        onClick={onRemove}
        aria-label="Quitar ingrediente"
        className="col-span-4 md:col-span-1 justify-self-end p-2 text-red-600 hover:bg-red-50 rounded-lg"
      >
        <Trash2 className="w-5 h-5" />
      </button>
    </div>
  )
}
