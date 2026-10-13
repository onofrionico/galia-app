import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { posCashApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { useCashSession, useMainRegister } from '../hooks/useCash'
import CenteredMessage from '../ui/CenteredMessage'
import { btn } from '../ui/buttons'
import { formatMoney } from '../utils/money'
import { timeLabel } from '../utils/time'
import CashSummaryCards from './CashSummaryCards'
import CloseSessionModal, { CloseSummaryModal } from './CloseSessionModal'
import MovementList from './MovementList'
import MovementModal from './MovementModal'
import OpenSessionModal from './OpenSessionModal'

function LastClosed({ registerId }) {
  const params = { register_id: registerId, page: 1 }
  const { data } = useQuery({ queryKey: posKeys.cashSessions(params), queryFn: () => posCashApi.listSessions(params) })
  const last = data?.sessions?.find((s) => s.status === 'closed')
  if (!last) return null
  return (
    <p className="text-sm text-gray-600">
      Último cierre: {timeLabel(last.closed_at)} por {last.closed_by?.name} · cobrado {formatMoney(last.collected_net)}
      {last.cash_difference ? ` · diferencia en efectivo ${formatMoney(last.cash_difference)}` : ''}
    </p>
  )
}

export default function CashPage() {
  const { register, openSessionId, isLoading, isError } = useMainRegister()
  const { data: session, isError: sessionError } = useCashSession(openSessionId)
  const [modal, setModal] = useState(null)
  const [closedResult, setClosedResult] = useState(null)
  const close = () => setModal(null)
  // El resultado del cierre vive acá: al cerrar, la caja deja de estar abierta y este componente cambia de rama.
  const closeSummary = closedResult && <CloseSummaryModal result={closedResult} onClose={() => setClosedResult(null)} />

  if (isLoading) return <CenteredMessage>Cargando caja…</CenteredMessage>
  if (isError) return <CenteredMessage>No se pudo cargar la caja.</CenteredMessage>
  if (!register) return <CenteredMessage>No hay ninguna caja configurada.</CenteredMessage>

  if (!openSessionId) {
    return (
      <div className="mx-auto max-w-xl space-y-4 p-6 text-center">
        <h2 className="text-2xl font-semibold text-galia-plum">{register.name} cerrada</h2>
        <button type="button" className={btn('primary', 'text-lg')} onClick={() => setModal('open')}>Abrir caja</button>
        <LastClosed registerId={register.id} />
        {modal === 'open' && <OpenSessionModal register={register} onClose={close} />}
        {closeSummary}
      </div>
    )
  }
  if (!session && sessionError) return <CenteredMessage>No se pudo cargar la caja.</CenteredMessage>
  if (!session) return <CenteredMessage>Cargando caja…</CenteredMessage>

  return (
    <div className="h-full space-y-4 overflow-y-auto p-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-galia-plum">{session.register.name}</h2>
          <p className="text-sm text-gray-600">
            Abierta {timeLabel(session.opened_at)} por {session.opened_by?.name} · fondo {formatMoney(session.opening_float)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className={btn('secondary')} onClick={() => setModal('expense')}>Gasto</button>
          <button type="button" className={btn('secondary')} onClick={() => setModal('withdrawal')}>Retiro</button>
          <button type="button" className={btn('secondary')} onClick={() => setModal('deposit')}>Ingreso</button>
          <button type="button" className={btn('primary')} onClick={() => setModal('close')}>Cerrar caja</button>
        </div>
      </header>
      <CashSummaryCards summary={session.summary} />
      <h3 className="font-semibold">Movimientos</h3>
      <MovementList session={session} />
      {['expense', 'withdrawal', 'deposit'].includes(modal) && <MovementModal session={session} kind={modal} onClose={close} />}
      {modal === 'close' && (
        <CloseSessionModal session={session} onClose={close}
          onClosed={(result) => { setClosedResult(result); setModal(null) }} />
      )}
      {closeSummary}
    </div>
  )
}
