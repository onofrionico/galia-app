import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useFloor, useSale } from '@/pos/hooks/usePosQueries'
import SalePanel from '@/pos/sale/SalePanel'
import MoveSheet from './MoveSheet'

// La venta a pantalla completa: el panel de la caja en su variante 'screen'.
export default function SaleScreen() {
  const saleId = Number(useParams().saleId)
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  // "Agregar productos" se abre solo al llegar con ?add=1 (recién abierta la mesa), una vez.
  const [initial] = useState(() => ({ saleId, modal: params.get('add') === '1' ? 'add' : null }))
  const [moving, setMoving] = useState(false)
  const { data: sale } = useSale(saleId)
  const salonId = sale?.table?.salon_id
  const { data: floor } = useFloor(salonId, { enabled: Boolean(salonId) })
  const siblings = floor?.tables.find((table) => table.id === sale?.table?.id)?.sales ?? []

  useEffect(() => {
    if (params.has('add')) setParams({}, { replace: true })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const backToTables = () => navigate(salonId ? `/camarero?salon=${salonId}` : '/camarero')

  return (
    <div className="h-full">
      <SalePanel key={saleId} saleId={saleId} variant="screen" closeLabel="Mesas" siblings={siblings}
        initialModal={initial.saleId === saleId ? initial.modal : null}
        onSelect={(id) => navigate(`/camarero/venta/${id}`, { replace: true })}
        onClose={backToTables}
        onStartMove={() => setMoving(true)} />
      {moving && sale && <MoveSheet sale={sale} onClose={() => setMoving(false)} />}
    </div>
  )
}
