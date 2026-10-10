import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowDown, ArrowUp, X } from 'lucide-react'
import { posConfigApi } from '@/pos/api/posApi'
import { errorMessage } from '@/pos/utils/errors'
import { groupHint } from '@/pos/utils/modifiers'

export default function ProductModifiersTab({ productId }) {
  const queryClient = useQueryClient()
  const groupsQuery = useQuery({ queryKey: ['modifier-groups'], queryFn: posConfigApi.listModifierGroups })
  const assignedQuery = useQuery({
    queryKey: ['product-modifier-groups', productId],
    queryFn: () => posConfigApi.getProductModifierGroups(productId),
  })
  const [ids, setIds] = useState([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (assignedQuery.data) setIds(assignedQuery.data)
  }, [assignedQuery.data])

  const groups = groupsQuery.data ?? []
  const byId = new Map(groups.map((g) => [g.id, g]))
  const available = groups.filter((g) => g.is_active && !ids.includes(g.id))

  const move = (index, delta) => setIds((list) => {
    const next = [...list]
    const [id] = next.splice(index, 1)
    next.splice(index + delta, 0, id)
    return next
  })

  const save = async () => {
    setSaving(true)
    setError('')
    setMessage('')
    try {
      const result = await posConfigApi.setProductModifierGroups(productId, ids)
      queryClient.setQueryData(['product-modifier-groups', productId], result.group_ids)
      setMessage('Guardado')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  if (groupsQuery.isLoading || assignedQuery.isLoading) return <p className="text-gray-500">Cargando…</p>

  return (
    <div className="max-w-2xl space-y-4">
      <p className="text-sm text-gray-600">
        Grupos que el POS pide al cargar este producto, en este orden. Los grupos se crean en{' '}
        <Link to="/products/modifiers" className="text-galia-plum underline">Modificadores</Link>.
      </p>
      <ul className="divide-y rounded-lg border">
        {ids.length === 0 && <li className="px-4 py-3 text-sm text-gray-500">Sin modificadores.</li>}
        {ids.map((id, index) => (
          <li key={id} className="flex items-center justify-between px-4 py-2">
            <span>
              <span className="font-medium">{byId.get(id)?.name ?? `Grupo ${id}`}</span>
              <span className="ml-2 text-xs text-gray-500">{byId.get(id) ? groupHint(byId.get(id)) : ''}</span>
            </span>
            <span className="flex gap-1">
              <button type="button" aria-label="Subir" disabled={index === 0} onClick={() => move(index, -1)}
                className="rounded p-1 hover:bg-gray-100 disabled:opacity-30"><ArrowUp size={16} /></button>
              <button type="button" aria-label="Bajar" disabled={index === ids.length - 1} onClick={() => move(index, 1)}
                className="rounded p-1 hover:bg-gray-100 disabled:opacity-30"><ArrowDown size={16} /></button>
              <button type="button" aria-label="Quitar" onClick={() => setIds((list) => list.filter((x) => x !== id))}
                className="rounded p-1 text-red-600 hover:bg-red-50"><X size={16} /></button>
            </span>
          </li>
        ))}
      </ul>
      {available.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {available.map((group) => (
            <button key={group.id} type="button" onClick={() => setIds((list) => [...list, group.id])}
              className="rounded-full border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50">
              + {group.name}
            </button>
          ))}
        </div>
      )}
      <div className="flex items-center gap-3">
        <button type="button" onClick={save} disabled={saving}
          className="rounded bg-galia-plum px-4 py-2 text-galia-cream disabled:opacity-50">Guardar modificadores</button>
        {message && <span className="text-sm text-green-700">{message}</span>}
        {error && <span className="text-sm text-red-700">{error}</span>}
      </div>
    </div>
  )
}
