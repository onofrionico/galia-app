import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import suppliesService from '@/services/suppliesService'
import { posConfigApi } from '@/pos/api/posApi'
import { groupHint } from '@/pos/utils/modifiers'
import { formatMoney } from '@/pos/utils/money'
import ModifierGroupForm from '@/components/products/ModifierGroupForm'

export default function ModifierGroups() {
  const queryClient = useQueryClient()
  const { hasModuleAccess } = useAuth()
  const { data: groups = [], isLoading, isError } = useQuery({
    queryKey: ['modifier-groups'],
    queryFn: posConfigApi.listModifierGroups,
  })
  // Sin el módulo Stock no se piden insumos (un 403 dispararía la redirección global).
  const { data: supplies = null } = useQuery({
    queryKey: ['modifier-supplies'],
    queryFn: () => suppliesService.getSupplies({ per_page: 200 }).then((d) => d.supplies),
    enabled: hasModuleAccess('Stock'),
  })
  const [editing, setEditing] = useState(null)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl">Modificadores</h1>
        <button type="button" onClick={() => setEditing({})}
          className="flex items-center gap-2 rounded-lg bg-galia-plum px-4 py-2 text-galia-cream">
          <Plus size={18} /> Nuevo grupo
        </button>
      </div>
      <p className="text-gray-600">Opciones que se eligen al cargar un producto en el POS (tipo de leche, extras, punto de la carne…). Se asignan a cada producto desde su ficha.</p>
      {isLoading && <p className="text-gray-500">Cargando…</p>}
      {isError && <p className="text-red-700">No se pudieron cargar los grupos.</p>}
      <div className="overflow-x-auto rounded-lg bg-white shadow">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr><th className="px-4 py-2">Grupo</th><th className="px-4 py-2">Regla</th><th className="px-4 py-2">Opciones</th><th className="px-4 py-2">Estado</th><th /></tr>
          </thead>
          <tbody>
            {groups.map((group) => (
              <tr key={group.id} className="border-t">
                <td className="px-4 py-2 font-medium">{group.name}</td>
                <td className="px-4 py-2">{groupHint(group)}</td>
                <td className="px-4 py-2">
                  {group.options.filter((o) => o.is_active)
                    .map((o) => (o.price_delta > 0 ? `${o.name} (+${formatMoney(o.price_delta)})` : o.name)).join(', ')}
                </td>
                <td className="px-4 py-2">{group.is_active ? 'Activo' : 'Inactivo'}</td>
                <td className="px-4 py-2 text-right">
                  <button type="button" onClick={() => setEditing(group)} className="text-galia-plum underline">Editar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {editing && (
        <ModifierGroupForm group={editing} supplies={supplies} onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); queryClient.invalidateQueries({ queryKey: ['modifier-groups'] }) }} />
      )}
    </div>
  )
}
