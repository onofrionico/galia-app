import { useLayoutEffect, useRef, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { useFloor, useSale } from '@/pos/hooks/usePosQueries'
import SalePanel from '@/pos/sale/SalePanel'
import MoveSheet from './MoveSheet'

// La venta a pantalla completa: el panel de la caja en su variante 'screen'.
export default function SaleScreen() {
  const saleId = Number(useParams().saleId)
  const location = useLocation()
  const navigate = useNavigate()
  // "Agregar productos" se abre solo al llegar recién abierta la mesa (state.openAdd), una vez.
  const pendingAdd = useRef(location.state?.openAdd ? saleId : null)
  const [moving, setMoving] = useState(false)
  const { data: sale } = useSale(saleId)
  const salonId = sale?.table?.salon_id
  const { data: floor } = useFloor(salonId, { enabled: Boolean(salonId) })
  const siblings = floor?.tables.find((table) => table.id === sale?.table?.id)?.sales ?? []

  // SalePanel lee initialModal solo al montar. Corre antes del efecto que apila la hoja, y el
  // replaceState crudo conserva idx/key para no afectar al router; así recargar o volver no reabre la hoja.
  useLayoutEffect(() => {
    pendingAdd.current = null
    if (window.history.state?.usr?.openAdd) {
      window.history.replaceState({ ...window.history.state, usr: null }, '')
    }
  }, [])

  // Si hay una hoja abierta (p. ej. "Venta cerrada"), se reemplaza su entrada de historial en vez de apilar encima.
  const backToTables = () =>
    navigate(salonId ? `/camarero?salon=${salonId}` : '/camarero', { replace: Boolean(window.history.state?.posSheet) })

  return (
    <div className="h-full">
      <SalePanel key={saleId} saleId={saleId} variant="screen" closeLabel="Mesas" siblings={siblings}
        initialModal={pendingAdd.current === saleId ? 'add' : null}
        onSelect={(id) => navigate(`/camarero/venta/${id}`, { replace: true })}
        onClose={backToTables}
        onStartMove={() => setMoving(true)} />
      {moving && sale && <MoveSheet sale={sale} onClose={() => setMoving(false)} />}
    </div>
  )
}
