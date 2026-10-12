import { useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import Chip from '../ui/Chip'
import { btn } from '../ui/buttons'
import { formatMoney } from '../utils/money'
import { groupHint, linePreview, selectionError, toggleOption } from '../utils/modifiers'

export default function ProductDetailStep({ product, busy, onBack, onAdd }) {
  const [variantId, setVariantId] = useState(product.variants[0].id)
  const [selected, setSelected] = useState([])
  const [note, setNote] = useState('')
  const [quantity, setQuantity] = useState(1)
  const variant = product.variants.find((v) => v.id === variantId)
  const groups = product.modifier_groups
  const error = selectionError(groups, selected)

  const submit = () => onAdd({ variantId, quantity, optionIds: selected, note: note.trim() || null })

  return (
    <div className="space-y-5">
      <button type="button" className="flex items-center gap-1 text-sm text-galia-plum" onClick={onBack}>
        <ArrowLeft size={16} /> Volver a la lista
      </button>
      <h3 className="text-xl font-semibold">{product.name}</h3>

      {product.variants.length > 1 && (
        <fieldset>
          <legend className="text-sm font-medium text-gray-700">Variante</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {product.variants.map((v) => (
              <Chip key={v.id} active={v.id === variantId} onClick={() => setVariantId(v.id)}>
                {v.name} · {formatMoney(v.price)}
              </Chip>
            ))}
          </div>
        </fieldset>
      )}

      {groups.map((group) => (
        <fieldset key={group.id}>
          <legend className="text-sm font-medium text-gray-700">
            {group.name} <span className="font-normal text-gray-500">({groupHint(group)})</span>
          </legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {group.options.map((option) => (
              <Chip key={option.id} active={selected.includes(option.id)}
                onClick={() => setSelected((current) => toggleOption(group, current, option.id))}>
                {option.name}{option.price_delta > 0 ? ` +${formatMoney(option.price_delta)}` : ''}
              </Chip>
            ))}
          </div>
        </fieldset>
      ))}

      <label className="block">
        <span className="text-sm font-medium text-gray-700">Nota</span>
        <input value={note} onChange={(e) => setNote(e.target.value)} maxLength={255} placeholder="Ej.: bien caliente"
          className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-galia-plum focus:outline-none" />
      </label>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button type="button" className={btn('secondary', 'w-12 text-xl')} aria-label="Uno menos"
            onClick={() => setQuantity((q) => Math.max(1, q - 1))}>−</button>
          <span className="w-10 text-center text-xl font-semibold">{quantity}</span>
          <button type="button" className={btn('secondary', 'w-12 text-xl')} aria-label="Uno más"
            onClick={() => setQuantity((q) => Math.min(1000, q + 1))}>+</button>
        </div>
        <button type="button" className={btn('primary')} disabled={busy || Boolean(error)} onClick={submit}>
          Agregar {formatMoney(linePreview(variant, groups, selected, quantity))}
        </button>
      </div>
      {error && <p className="text-sm text-amber-700">{error}</p>}
    </div>
  )
}
