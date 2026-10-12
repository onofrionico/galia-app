import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { posApi } from '../api/posApi'
import { useFloor } from '../hooks/usePosQueries'
import { useSaleMutation } from '../hooks/useSaleMutation'
import OpenTableModal from '../modals/OpenTableModal'
import SalePanel from '../sale/SalePanel'
import CenteredMessage from '../ui/CenteredMessage'
import { useToast } from '../ui/Toasts'
import { btn } from '../ui/buttons'
import FloorPlan from './FloorPlan'

export default function SalonPage() {
  const salonId = Number(useParams().salonId)
  const [params, setParams] = useSearchParams()
  const saleId = Number(params.get('sale')) || null
  const { data, isLoading, isError } = useFloor(salonId)
  const [openTable, setOpenTable] = useState(null)
  const [moving, setMoving] = useState(false)
  const [initialModal, setInitialModal] = useState(null)
  const { run } = useSaleMutation()
  const toast = useToast()

  useEffect(() => {
    if (!moving) return undefined
    const onKey = (event) => { if (event.key === 'Escape') setMoving(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [moving])

  const select = (id, modal = null) => {
    setInitialModal(modal)
    setMoving(false)
    setParams(id ? { sale: String(id) } : {})
  }

  if (isLoading) return <CenteredMessage>Cargando plano…</CenteredMessage>
  if (isError || !data) return <CenteredMessage>No se pudo cargar el plano.</CenteredMessage>

  const tables = data.tables
  const selectedTable = tables.find((t) => t.sales.some((s) => s.id === saleId)) ?? null

  const onTableClick = async (table) => {
    if (moving) {
      if (table.sales.length > 0) return
      setMoving(false)
      const moved = await run(saleId, () => posApi.move(saleId, table.id))
      if (moved) toast.success(`Venta movida a ${table.label}`)
      return
    }
    if (table.sales.length > 0) select(table.sales[0].id)
    else setOpenTable(table)
  }

  return (
    <div className="flex h-full">
      <div className="min-w-0 flex-1 overflow-auto p-4">
        {moving && (
          <div className="mb-3 flex items-center justify-between rounded-lg bg-galia-lime/30 px-4 py-2">
            <span className="font-medium">Tocá la mesa libre de destino</span>
            <button type="button" className={btn('secondary')} onClick={() => setMoving(false)}>Cancelar</button>
          </div>
        )}
        <FloorPlan tables={tables} selectedTableId={selectedTable?.id} picking={moving} onTableClick={onTableClick} />
      </div>
      {saleId && (
        <SalePanel key={saleId} saleId={saleId} siblings={selectedTable?.sales ?? []} initialModal={initialModal}
          onSelect={(id) => select(id)} onClose={() => select(null)} onStartMove={() => setMoving(true)} />
      )}
      {openTable && (
        <OpenTableModal table={openTable} onClose={() => setOpenTable(null)}
          onOpened={(id, isNew) => { setOpenTable(null); select(id, isNew ? 'add' : null) }} />
      )}
    </div>
  )
}
