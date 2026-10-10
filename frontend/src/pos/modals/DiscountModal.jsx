import { useState } from 'react'
import { posApi } from '../api/posApi'
import { useLookup } from '../hooks/usePosQueries'
import { usePosPermissions } from '../hooks/usePosPermissions'
import { useSaleMutation } from '../hooks/useSaleMutation'
import Chip from '../ui/Chip'
import Modal from '../ui/Modal'
import { btn } from '../ui/buttons'
import { discountLabel, parseAmount } from '../utils/money'

// Descuento a la venta (item = null) o a un ítem confirmado.
export default function DiscountModal({ sale, item, onClose }) {
  const perms = usePosPermissions()
  const { data: templates = [], isLoading } = useLookup('discount-templates')
  const [kind, setKind] = useState('percent')
  const [value, setValue] = useState('')
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  const { run, busy } = useSaleMutation()

  const scope = item ? 'item' : 'sale'
  const visible = templates.filter((t) => t.scope === scope && (!t.restricted || perms.discounts))

  const apply = async (body) => {
    const result = await run(sale.id, () => posApi.addDiscount(sale.id, { ...body, item_id: item?.id ?? null }))
    if (result) onClose()
  }

  const applyFree = () => {
    const number = parseAmount(value)
    if (!(number > 0)) return setError('Indicá el valor')
    if (kind === 'percent' && number > 100) return setError('El porcentaje no puede superar 100')
    if (!reason.trim()) return setError('Indicá el motivo')
    setError('')
    apply({ kind, value: number, reason: reason.trim() })
  }

  return (
    <Modal title={item ? `Descuento a ${item.product_name}` : 'Descuento a la venta'} onClose={onClose} size="md">
      <p className="text-sm font-medium text-gray-700">Plantillas</p>
      {isLoading && <p className="mt-2 text-sm text-gray-500">Cargando…</p>}
      {!isLoading && visible.length === 0 && <p className="mt-2 text-sm text-gray-500">No hay plantillas disponibles.</p>}
      <div className="mt-2 grid grid-cols-2 gap-2">
        {visible.map((template) => (
          <button key={template.id} type="button" disabled={busy} onClick={() => apply({ template_id: template.id })}
            className={btn('secondary', 'flex-col items-start py-2')}>
            <span>{template.name}</span>
            <span className="text-xs text-gray-500">
              {discountLabel(template)}{template.restricted ? ' · restringida' : ''}
            </span>
          </button>
        ))}
      </div>

      {perms.discounts && (
        <div className="mt-6 border-t pt-4">
          <p className="text-sm font-medium text-gray-700">Descuento libre</p>
          <div className="mt-2 flex gap-2">
            <Chip active={kind === 'percent'} onClick={() => setKind('percent')}>Porcentaje</Chip>
            <Chip active={kind === 'amount'} onClick={() => setKind('amount')}>Monto</Chip>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <input inputMode="decimal" value={value} onChange={(e) => setValue(e.target.value)}
              placeholder={kind === 'percent' ? '%' : '$'} aria-label="Valor del descuento"
              className="rounded-lg border border-gray-300 px-3 py-2" />
            <input value={reason} onChange={(e) => setReason(e.target.value)} maxLength={200}
              placeholder="Motivo" aria-label="Motivo del descuento" className="rounded-lg border border-gray-300 px-3 py-2" />
          </div>
          {error && <p className="mt-2 text-sm text-red-700">{error}</p>}
          <button type="button" className={btn('primary', 'mt-3')} disabled={busy} onClick={applyFree}>Aplicar</button>
        </div>
      )}
    </Modal>
  )
}
