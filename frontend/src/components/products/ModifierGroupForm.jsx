import { useState } from 'react'
import { ArrowDown, ArrowUp, Plus, Trash2, X } from 'lucide-react'
import { posConfigApi } from '@/pos/api/posApi'
import { errorMessage } from '@/pos/utils/errors'

const emptyOption = () => ({ key: `${Date.now()}-${Math.random()}`, name: '', price_delta: '0', supply_id: '', supply_quantity: '' })

const toRows = (group) => (group.options ?? [])
  .filter((o) => o.is_active)
  .map((o) => ({
    key: String(o.id), id: o.id, name: o.name, price_delta: String(o.price_delta),
    supply_id: o.supply_id ? String(o.supply_id) : '', supply_quantity: o.supply_quantity ? String(o.supply_quantity) : '',
  }))

// supplies = null cuando el usuario no tiene acceso a Stock: no se muestran los insumos.
export default function ModifierGroupForm({ group, supplies, onClose, onSaved }) {
  const isNew = !group.id
  const [form, setForm] = useState({
    name: group.name ?? '', min_select: String(group.min_select ?? 0), max_select: String(group.max_select ?? 1),
    is_active: group.is_active ?? true,
  })
  const [rows, setRows] = useState(isNew ? [emptyOption()] : toRows(group))
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const setRow = (key, field, value) => setRows((list) => list.map((r) => (r.key === key ? { ...r, [field]: value } : r)))
  const moveRow = (index, delta) => setRows((list) => {
    const next = [...list]
    const [row] = next.splice(index, 1)
    next.splice(index + delta, 0, row)
    return next
  })

  const submit = async (event) => {
    event.preventDefault()
    const body = {
      name: form.name.trim(),
      min_select: Number(form.min_select),
      max_select: Number(form.max_select),
      is_active: form.is_active,
      options: rows.map((r) => ({
        ...(r.id ? { id: r.id } : {}),
        name: r.name.trim(),
        price_delta: Number(r.price_delta || 0),
        supply_id: r.supply_id ? Number(r.supply_id) : null,
        supply_quantity: r.supply_id ? Number(r.supply_quantity) : null,
      })),
    }
    setSaving(true)
    setError('')
    try {
      if (isNew) await posConfigApi.createModifierGroup(body)
      else await posConfigApi.updateModifierGroup(group.id, body)
      onSaved()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4">
      <form onSubmit={submit} className="flex max-h-[90vh] w-full max-w-3xl flex-col rounded-lg bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-3">
          <h2 className="text-lg font-semibold">{isNew ? 'Nuevo grupo de modificadores' : `Editar ${group.name}`}</h2>
          <button type="button" onClick={onClose} aria-label="Cerrar" className="rounded p-1 hover:bg-gray-100"><X size={20} /></button>
        </div>
        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
            <label className="text-sm sm:col-span-2">Nombre
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} maxLength={100}
                className="mt-1 w-full rounded border px-3 py-2" placeholder="Ej.: Tipo de leche" />
            </label>
            <label className="text-sm">Mínimo
              <input type="number" min="0" value={form.min_select} onChange={(e) => setForm({ ...form, min_select: e.target.value })}
                className="mt-1 w-full rounded border px-3 py-2" />
            </label>
            <label className="text-sm">Máximo
              <input type="number" min="1" value={form.max_select} onChange={(e) => setForm({ ...form, max_select: e.target.value })}
                className="mt-1 w-full rounded border px-3 py-2" />
            </label>
          </div>
          <p className="text-xs text-gray-500">Con mínimo mayor a 0 el grupo es obligatorio al cargar el producto.</p>
          {!isNew && (
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
              Activo
            </label>
          )}

          <div>
            <h3 className="font-medium">Opciones</h3>
            <div className="mt-2 space-y-2">
              {rows.map((row, index) => (
                <div key={row.key} className="grid grid-cols-12 items-center gap-2">
                  <input required value={row.name} onChange={(e) => setRow(row.key, 'name', e.target.value)} maxLength={100}
                    placeholder="Opción" aria-label="Nombre de la opción" className="col-span-4 rounded border px-2 py-1.5" />
                  <input type="number" min="0" step="0.01" value={row.price_delta}
                    onChange={(e) => setRow(row.key, 'price_delta', e.target.value)} aria-label="Recargo"
                    className="col-span-2 rounded border px-2 py-1.5" />
                  {supplies ? (
                    <>
                      <select value={row.supply_id} onChange={(e) => setRow(row.key, 'supply_id', e.target.value)}
                        aria-label="Insumo" className="col-span-3 rounded border px-2 py-1.5">
                        <option value="">Sin insumo</option>
                        {supplies.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.unit})</option>)}
                      </select>
                      <input type="number" min="0" step="0.0001" value={row.supply_quantity} disabled={!row.supply_id}
                        required={Boolean(row.supply_id)} onChange={(e) => setRow(row.key, 'supply_quantity', e.target.value)}
                        aria-label="Cantidad de insumo" className="col-span-1 rounded border px-2 py-1.5 disabled:bg-gray-100" />
                    </>
                  ) : <span className="col-span-4" />}
                  <span className="col-span-2 flex justify-end gap-1">
                    <button type="button" aria-label="Subir opción" disabled={index === 0} onClick={() => moveRow(index, -1)}
                      className="rounded p-1 hover:bg-gray-100 disabled:opacity-30"><ArrowUp size={16} /></button>
                    <button type="button" aria-label="Bajar opción" disabled={index === rows.length - 1} onClick={() => moveRow(index, 1)}
                      className="rounded p-1 hover:bg-gray-100 disabled:opacity-30"><ArrowDown size={16} /></button>
                    <button type="button" aria-label="Quitar opción" disabled={rows.length === 1}
                      onClick={() => setRows((list) => list.filter((r) => r.key !== row.key))}
                      className="rounded p-1 text-red-600 hover:bg-red-50 disabled:opacity-30"><Trash2 size={16} /></button>
                  </span>
                </div>
              ))}
            </div>
            <button type="button" onClick={() => setRows((list) => [...list, emptyOption()])}
              className="mt-2 flex items-center gap-1 text-sm text-galia-plum"><Plus size={16} /> Agregar opción</button>
          </div>
          {error && <p className="text-sm text-red-700">{error}</p>}
        </div>
        <div className="flex justify-end gap-2 border-t px-5 py-3">
          <button type="button" onClick={onClose} className="rounded border px-4 py-2">Cancelar</button>
          <button type="submit" disabled={saving} className="rounded bg-galia-plum px-4 py-2 text-galia-cream disabled:opacity-50">Guardar</button>
        </div>
      </form>
    </div>
  )
}
