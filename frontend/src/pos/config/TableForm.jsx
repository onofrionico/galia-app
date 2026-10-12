import { useEffect, useState } from 'react'
import { btn } from '../ui/buttons'

const toForm = (table) => ({ number: String(table.number), name: table.name ?? '', capacity: table.capacity ?? '' })

export default function TableForm({ table, busy, onSave }) {
  const [form, setForm] = useState(toForm(table))
  // Solo se reinicia si cambian los datos de la mesa: un objeto nuevo con los mismos valores
  // (refetch del plano) no debe borrar lo que se está tipeando.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => setForm(toForm(table)), [table.id, table.number, table.name, table.capacity, table.is_active])
  const set = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }))

  const submit = (event) => {
    event.preventDefault()
    onSave({
      number: Number(form.number),
      name: form.name.trim() || null,
      capacity: form.capacity === '' ? null : Number(form.capacity),
    })
  }

  return (
    <form onSubmit={submit} className="space-y-3 rounded-xl border border-gray-200 bg-white p-4">
      <h3 className="font-semibold text-galia-plum">{table.label}</h3>
      <label className="block text-sm">Número
        <input type="number" min="1" value={form.number} onChange={set('number')} className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
      </label>
      <label className="block text-sm">Nombre (opcional)
        <input value={form.name} onChange={set('name')} maxLength={50} placeholder="Ej.: Barra" className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
      </label>
      <label className="block text-sm">Capacidad
        <input type="number" min="1" value={form.capacity} onChange={set('capacity')} className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2" />
      </label>
      <div className="flex gap-2">
        <button type="submit" className={btn('primary', 'flex-1')} disabled={busy}>Guardar</button>
        <button type="button" className={btn(table.is_active ? 'danger' : 'secondary')} disabled={busy}
          onClick={() => onSave({ is_active: !table.is_active })}>
          {table.is_active ? 'Desactivar' : 'Activar'}
        </button>
      </div>
    </form>
  )
}
