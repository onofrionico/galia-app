import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { posConfigApi } from '@/pos/api/posApi'
import { errorMessage } from '@/pos/utils/errors'

// fields: [{ key, label, type: 'text' | 'number' | 'select' | 'checkbox', options?: [[value, label]] }]
const toValue = (field, value) => {
  if (field.type === 'number') return Number(value)
  if (field.type === 'checkbox') return Boolean(value)
  if (field.type === 'text') return String(value ?? '').trim()
  return value
}

const display = (field, value) => {
  if (field.type === 'checkbox') return value ? 'Sí' : 'No'
  if (field.type === 'select') return field.options.find(([v]) => v === value)?.[1] ?? value
  return value
}

export default function CatalogEditor({ resource, fields, emptyItem }) {
  const queryClient = useQueryClient()
  const key = ['pos-settings', resource]
  const { data: rows = [], isLoading, isError } = useQuery({ queryKey: key, queryFn: () => posConfigApi.listResource(resource) })
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState('')

  const save = useMutation({
    mutationFn: (row) => {
      const body = Object.fromEntries(fields.map((f) => [f.key, toValue(f, row[f.key])]))
      return row.id ? posConfigApi.updateResource(resource, row.id, body) : posConfigApi.createResource(resource, body)
    },
    onSuccess: () => {
      setEditing(null)
      setError('')
      queryClient.invalidateQueries({ queryKey: key })
    },
    onError: (err) => setError(errorMessage(err)),
  })

  const input = (field) => {
    const value = editing[field.key]
    const set = (v) => setEditing({ ...editing, [field.key]: v })
    if (field.type === 'checkbox') {
      return <input type="checkbox" checked={Boolean(value)} onChange={(e) => set(e.target.checked)} />
    }
    if (field.type === 'select') {
      return (
        <select value={value} onChange={(e) => set(e.target.value)} className="w-full rounded border px-2 py-1.5">
          {field.options.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
        </select>
      )
    }
    return (
      <input type={field.type === 'number' ? 'number' : 'text'} step="0.01" value={value ?? ''}
        onChange={(e) => set(e.target.value)} className="w-full rounded border px-2 py-1.5" />
    )
  }

  return (
    <div className="space-y-4">
      {editing ? (
        <form onSubmit={(e) => { e.preventDefault(); save.mutate(editing) }} className="space-y-3 rounded-lg bg-white p-4 shadow">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {fields.map((field) => (
              <label key={field.key} className="text-sm">
                <span className="block text-gray-700">{field.label}</span>
                <span className="mt-1 block">{input(field)}</span>
              </label>
            ))}
          </div>
          {error && <p className="text-sm text-red-700">{error}</p>}
          <div className="flex gap-2">
            <button type="submit" disabled={save.isPending} className="rounded bg-galia-plum px-4 py-2 text-galia-cream disabled:opacity-50">Guardar</button>
            <button type="button" onClick={() => { setEditing(null); setError('') }} className="rounded border px-4 py-2">Cancelar</button>
          </div>
        </form>
      ) : (
        <button type="button" onClick={() => setEditing({ ...emptyItem })}
          className="flex items-center gap-2 rounded-lg bg-galia-plum px-4 py-2 text-galia-cream">
          <Plus size={18} /> Agregar
        </button>
      )}
      {isLoading && <p className="text-gray-500">Cargando…</p>}
      {isError && <p className="text-red-700">No se pudo cargar la lista.</p>}
      <div className="overflow-x-auto rounded-lg bg-white shadow">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr>{fields.map((f) => <th key={f.key} className="px-4 py-2">{f.label}</th>)}<th /></tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className={`border-t ${row.is_active === false ? 'text-gray-400' : ''}`}>
                {fields.map((f) => <td key={f.key} className="px-4 py-2">{display(f, row[f.key])}</td>)}
                <td className="px-4 py-2 text-right">
                  <button type="button" onClick={() => setEditing({ ...row })} className="text-galia-plum underline">Editar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
