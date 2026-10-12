import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { useFloor } from '@/pos/hooks/usePosQueries'
import OpenTableModal from '@/pos/modals/OpenTableModal'
import CenteredMessage from '@/pos/ui/CenteredMessage'
import { btn } from '@/pos/ui/buttons'
import { useDevicePrefs } from './hooks/useDevicePrefs'
import { pickSalonId } from './utils/salons'
import { filterTables } from './utils/tableFilters'
import FloorView from './FloorView'
import TableList from './TableList'
import TablesTopBar from './TablesTopBar'

export default function TablesScreen() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [params, setParams] = useSearchParams()
  const [prefs, setPrefs] = useDevicePrefs()
  const [openTable, setOpenTable] = useState(null)
  const fromUrl = Number(params.get('salon')) || null
  const requested = fromUrl ?? prefs.salonId ?? undefined
  const { data, isLoading, isError, refetch } = useFloor(requested)
  const chosen = data ? pickSalonId({ fromUrl, saved: prefs.salonId, salons: data.salons }) : null

  const selectSalon = (id) => {
    setPrefs({ salonId: id })
    setParams(id ? { salon: String(id) } : {}, { replace: true })
  }

  // Si el salón pedido ya no está activo (o no había ninguno), se pasa al elegido; el de la URL queda guardado.
  useEffect(() => {
    if (!data || chosen === null) return
    if (chosen !== requested) selectSalon(chosen)
    else if (prefs.salonId !== chosen) setPrefs({ salonId: chosen })
  }, [data, chosen, requested]) // eslint-disable-line react-hooks/exhaustive-deps

  if (isLoading) return <CenteredMessage>Cargando mesas…</CenteredMessage>
  if (isError || !data) {
    return (
      <CenteredMessage>
        <div className="flex flex-col items-center gap-3">
          <p>No se pudieron cargar las mesas.</p>
          <button type="button" className={btn('secondary')} onClick={() => refetch()}>Reintentar</button>
        </div>
      </CenteredMessage>
    )
  }
  if (data.salons.length === 0) {
    return <CenteredMessage>No hay salones configurados. Pedile a la caja que los cree.</CenteredMessage>
  }

  const userId = user?.id
  const ready = chosen === data.salon_id

  const onTableClick = (table) => {
    if (table.sales.length > 0) navigate(`/camarero/venta/${table.sales[0].id}`, { state: { fromTables: true } })
    else setOpenTable(table)
  }

  return (
    <div className="flex h-full flex-col">
      <TablesTopBar salons={data.salons} salonId={chosen} onSalon={selectSalon}
        view={prefs.view} onView={(view) => setPrefs({ view })}
        filter={prefs.filter} onFilter={(filter) => setPrefs({ filter })} />
      <div className="min-h-0 flex-1 overflow-auto">
        {!ready && <CenteredMessage>Cargando mesas…</CenteredMessage>}
        {ready && prefs.view === 'floor' && (
          <FloorView tables={data.tables} filter={prefs.filter} userId={userId} onTableClick={onTableClick} />
        )}
        {ready && prefs.view !== 'floor' && (
          <TableList tables={filterTables(data.tables, prefs.filter, userId)} userId={userId} onTableClick={onTableClick} />
        )}
      </div>
      {openTable && (
        <OpenTableModal table={openTable} allowWaiterPick={false} onClose={() => setOpenTable(null)}
          onOpened={(id, isNew) => {
            setOpenTable(null)
            // Si la hoja sigue abierta, se reemplaza su entrada de historial en vez de apilar encima (quedaría huérfana).
            // fromTables: "← Mesas" vuelve atrás a esta entrada en vez de apilar otra.
            navigate(`/camarero/venta/${id}`, {
              replace: Boolean(window.history.state?.posSheet),
              state: isNew ? { fromTables: true, openAdd: true } : { fromTables: true },
            })
          }} />
      )}
    </div>
  )
}
