import { useState } from 'react'
import { ChevronUp, ChevronDown, Pencil, Trash2, Plus, Check, X } from 'lucide-react'
import menuService from '../../services/menuService'
import { swap, errorMessage } from '../../utils/menuFormat'

const GroupRow = ({ group, index, total, onMove, onChanged, onError }) => {
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(group.name)

  const save = async () => {
    try {
      await menuService.updateGroup(group.id, { name })
      setEditing(false)
      onChanged()
    } catch (err) {
      onError(errorMessage(err, 'Error al renombrar el grupo'))
    }
  }

  const remove = async () => {
    if (!window.confirm(`¿Borrar el grupo "${group.name}"? Sus categorías quedan sin grupo.`)) return
    try {
      await menuService.deleteGroup(group.id)
      onChanged()
    } catch (err) {
      onError(errorMessage(err, 'Error al borrar el grupo'))
    }
  }

  return (
    <li className="flex items-center gap-2 py-2">
      {editing ? (
        <>
          <input value={name} onChange={(e) => setName(e.target.value)} className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm" />
          <button type="button" onClick={save} className="p-1.5 text-rose-700" aria-label="Guardar"><Check className="h-4 w-4" /></button>
          <button type="button" onClick={() => { setEditing(false); setName(group.name) }} className="p-1.5 text-gray-500" aria-label="Cancelar"><X className="h-4 w-4" /></button>
        </>
      ) : (
        <>
          <span className="flex-1 font-medium text-gray-900">{group.name}</span>
          <button type="button" disabled={index === 0} onClick={() => onMove(index, -1)} className="p-1.5 text-gray-500 disabled:opacity-30" aria-label="Subir"><ChevronUp className="h-4 w-4" /></button>
          <button type="button" disabled={index === total - 1} onClick={() => onMove(index, 1)} className="p-1.5 text-gray-500 disabled:opacity-30" aria-label="Bajar"><ChevronDown className="h-4 w-4" /></button>
          <button type="button" onClick={() => setEditing(true)} className="p-1.5 text-gray-500" aria-label="Renombrar"><Pencil className="h-4 w-4" /></button>
          <button type="button" onClick={remove} className="p-1.5 text-gray-500 hover:text-red-600" aria-label="Borrar"><Trash2 className="h-4 w-4" /></button>
        </>
      )}
    </li>
  )
}

const GroupsPanel = ({ groups, onChanged }) => {
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  const add = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await menuService.createGroup({ name })
      setName('')
      onChanged()
    } catch (err) {
      setError(errorMessage(err, 'Error al crear el grupo'))
    }
  }

  const move = async (index, direction) => {
    const ids = swap(groups.map((g) => g.id), index, index + direction)
    if (!ids) return
    try {
      await menuService.reorderGroups(ids)
      onChanged()
    } catch (err) {
      setError(errorMessage(err, 'Error al reordenar'))
    }
  }

  return (
    <section className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
      <div>
        <h2 className="font-semibold text-gray-900">Grupos de la carta</h2>
        <p className="text-sm text-gray-600">Organizan las secciones de la carta pública. Asigná cada categoría a un grupo desde la pestaña "Carta".</p>
      </div>
      {error && <div className="p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>}
      <ul className="divide-y divide-gray-100">
        {groups.length === 0 && <li className="py-2 text-sm text-gray-500">Sin grupos: la carta se muestra por categorías.</li>}
        {groups.map((group, index) => (
          <GroupRow key={`${group.id}-${group.name}`} group={group} index={index} total={groups.length} onMove={move} onChanged={onChanged} onError={setError} />
        ))}
      </ul>
      <form onSubmit={add} className="flex gap-2">
        <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Nuevo grupo (ej: Desayuno y merienda)" className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm" />
        <button type="submit" className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-rose-600 text-white rounded hover:bg-rose-700"><Plus className="h-4 w-4" /> Agregar</button>
      </form>
    </section>
  )
}

export default GroupsPanel
