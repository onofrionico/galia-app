import { useNow } from '@/pos/hooks/useNow'
import CenteredMessage from '@/pos/ui/CenteredMessage'
import TableCard from './TableCard'

export default function TableList({ tables, userId, onTableClick }) {
  const now = useNow()
  if (tables.length === 0) return <CenteredMessage>No hay mesas para mostrar.</CenteredMessage>
  return (
    <div className="grid grid-cols-2 gap-3 p-3 pb-[calc(env(safe-area-inset-bottom)+0.75rem)] min-[600px]:grid-cols-3">
      {tables.map((table) => (
        <TableCard key={table.id} table={table} userId={userId} now={now} onClick={() => onTableClick(table)} />
      ))}
    </div>
  )
}
