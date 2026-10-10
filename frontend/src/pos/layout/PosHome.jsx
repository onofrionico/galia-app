import { Link, Navigate } from 'react-router-dom'
import { useFloor } from '../hooks/usePosQueries'
import { usePosPermissions } from '../hooks/usePosPermissions'
import CenteredMessage from '../ui/CenteredMessage'

export default function PosHome() {
  const { data, isLoading, isError } = useFloor(undefined)
  const perms = usePosPermissions()
  if (isLoading) return <CenteredMessage>Cargando…</CenteredMessage>
  if (isError) return <CenteredMessage>No se pudo cargar el plano.</CenteredMessage>
  if (data.salon_id) return <Navigate to={`/pos/salon/${data.salon_id}`} replace />
  return (
    <CenteredMessage>
      {perms.pos ? (
        <p>
          No hay salones activos. <Link to="/pos/config" className="underline">Configurá el primero</Link> o
          usá el <Link to="/pos/mostrador" className="underline">mostrador</Link>.
        </p>
      ) : (
        <p>No hay salones activos. Pedile a la caja que configure uno.</p>
      )}
    </CenteredMessage>
  )
}
