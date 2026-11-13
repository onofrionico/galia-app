import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import loyaltyService from '../../services/loyaltyService'
import { dateTime, input, loyaltyKeys } from './shared'

const ENTITIES = { '': 'Todo', variant: 'Cafecitos por producto', reward: 'Premios', settings: 'Configuración',
  adjustment: 'Ajustes', customer: 'Clientes' }

export default function HistoryTab() {
  const [entity, setEntity] = useState('')
  const { data: rows = [] } = useQuery({ queryKey: loyaltyKeys.changeLog(entity), queryFn: () => loyaltyService.changeLog(entity) })
  return (
    <div className="space-y-3">
      <select className={input} value={entity} onChange={(e) => setEntity(e.target.value)}>
        {Object.entries(ENTITIES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select>
      <table className="w-full text-sm">
        <thead><tr className="text-left text-gray-500"><th className="py-1">Fecha</th><th>Quién</th><th>Qué</th><th>Antes → Después</th><th>Motivo</th></tr></thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className="border-t">
              <td className="py-1.5">{dateTime(r.created_at)}</td>
              <td>{r.user ?? '—'}</td>
              <td>{ENTITIES[r.entity] ?? r.entity} #{r.entity_id} · {r.field}</td>
              <td>{r.old_value ?? '—'} → {r.new_value ?? '—'}</td>
              <td>{r.reason ?? ''}</td>
            </tr>
          ))}
          {rows.length === 0 && <tr><td colSpan={5} className="py-2 text-gray-500">Sin cambios registrados.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}
