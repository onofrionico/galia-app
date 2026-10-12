import { useState } from 'react'
import { ArrowDown, ArrowUp, Pencil } from 'lucide-react'
import { posConfigApi } from '../api/posApi'
import { useConfigMutation } from '../hooks/useConfigMutation'
import { btn } from '../ui/buttons'

export default function SalonList({ salons, selectedId, onSelect }) {
  const [name, setName] = useState('')
  const create = useConfigMutation((body) => posConfigApi.createSalon(body))
  const update = useConfigMutation(({ id, ...body }) => posConfigApi.updateSalon(id, body))

  const submit = (event) => {
    event.preventDefault()
    if (!name.trim()) return
    create.mutate({ name: name.trim(), position: salons.length }, {
      onSuccess: (salon) => { setName(''); onSelect(salon.id) },
    })
  }

  // Reordena y guarda la posición de cada salón según su lugar en la lista.
  const move = (index, delta) => {
    const list = [...salons]
    const [salon] = list.splice(index, 1)
    list.splice(index + delta, 0, salon)
    list.forEach((s, position) => {
      if (s.position !== position) update.mutate({ id: s.id, position })
    })
  }

  const rename = (salon) => {
    const value = window.prompt('Nuevo nombre del salón', salon.name)
    if (value && value.trim() && value.trim() !== salon.name) update.mutate({ id: salon.id, name: value.trim() })
  }

  return (
    <aside className="flex w-72 flex-shrink-0 flex-col border-r border-gray-200 bg-white p-4">
      <h2 className="text-lg font-semibold text-galia-plum">Salones</h2>
      <ul className="mt-3 flex-1 space-y-1 overflow-y-auto">
        {salons.map((salon, index) => (
          <li key={salon.id} className={`flex items-center gap-1 rounded-lg px-2 py-1 ${salon.id === selectedId ? 'bg-galia-cream' : ''}`}>
            <button type="button" onClick={() => onSelect(salon.id)}
              className={`flex-1 truncate py-2 text-left ${salon.is_active ? '' : 'text-gray-400 line-through'}`}>
              {salon.name}
            </button>
            <button type="button" aria-label={`Subir ${salon.name}`} disabled={index === 0} onClick={() => move(index, -1)}
              className="rounded p-1 hover:bg-gray-100 disabled:opacity-30"><ArrowUp size={16} /></button>
            <button type="button" aria-label={`Bajar ${salon.name}`} disabled={index === salons.length - 1}
              onClick={() => move(index, 1)} className="rounded p-1 hover:bg-gray-100 disabled:opacity-30"><ArrowDown size={16} /></button>
            <button type="button" aria-label={`Renombrar ${salon.name}`} onClick={() => rename(salon)}
              className="rounded p-1 hover:bg-gray-100"><Pencil size={16} /></button>
          </li>
        ))}
      </ul>
      {selectedId && (
        <button type="button" className={btn('secondary', 'mb-3')}
          onClick={() => {
            const salon = salons.find((s) => s.id === selectedId)
            update.mutate({ id: salon.id, is_active: !salon.is_active })
          }}>
          {salons.find((s) => s.id === selectedId)?.is_active ? 'Desactivar salón' : 'Activar salón'}
        </button>
      )}
      <form onSubmit={submit} className="flex gap-2">
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nuevo salón" maxLength={100}
          aria-label="Nombre del salón nuevo" className="min-w-0 flex-1 rounded-lg border border-gray-300 px-3" />
        <button type="submit" className={btn('primary')} disabled={create.isPending}>Crear</button>
      </form>
    </aside>
  )
}
