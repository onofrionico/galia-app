import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { posConfigApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import CenteredMessage from '../ui/CenteredMessage'
import FloorEditor from './FloorEditor'
import SalonList from './SalonList'

export default function PosConfigPage() {
  const { data: salons = [], isLoading } = useQuery({ queryKey: posKeys.salons, queryFn: posConfigApi.listSalons })
  const [salonId, setSalonId] = useState(null)
  const current = salons.find((s) => s.id === salonId) ?? salons[0] ?? null

  return (
    <div className="flex h-full">
      <SalonList salons={salons} selectedId={current?.id ?? null} onSelect={setSalonId} />
      <div className="min-w-0 flex-1 overflow-auto p-4">
        {isLoading && <CenteredMessage>Cargando…</CenteredMessage>}
        {!isLoading && !current && <CenteredMessage>Creá un salón para empezar.</CenteredMessage>}
        {current && <FloorEditor key={current.id} salon={current} />}
      </div>
    </div>
  )
}
