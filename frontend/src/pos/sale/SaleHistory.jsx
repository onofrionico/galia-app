import { useSaleEvents } from '../hooks/usePosQueries'
import { eventDetail, eventLabel } from '../utils/events'
import { timeLabel } from '../utils/time'

export default function SaleHistory({ saleId }) {
  const { data: events = [], isLoading, isError } = useSaleEvents(saleId)
  if (isLoading) return <p className="p-4 text-sm text-gray-500">Cargando historial…</p>
  if (isError) return <p className="p-4 text-sm text-red-700">No se pudo cargar el historial.</p>
  return (
    <ol className="space-y-3 px-4 py-3">
      {events.map((event) => (
        <li key={event.id} className="text-sm">
          <p>
            <span className="font-mono text-gray-500">{timeLabel(event.created_at)}</span>{' '}
            <span className="font-medium">{event.user_name}</span> · {eventLabel(event.event_type)}
          </p>
          {eventDetail(event) && <p className="text-gray-600">{eventDetail(event)}</p>}
        </li>
      ))}
    </ol>
  )
}
