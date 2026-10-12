import { useLayoutEffect, useRef, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { useFloor, useSale } from '@/pos/hooks/usePosQueries'
import SalePanel from '@/pos/sale/SalePanel'
import MoveSheet from './MoveSheet'
import { afterSheetBack, backToTablesAction } from './utils/sheetHistory'

// La venta a pantalla completa: el panel de la caja en su variante 'screen'.
export default function SaleScreen() {
  const saleId = Number(useParams().saleId)
  const location = useLocation()
  const navigate = useNavigate()
  // "Agregar productos" se abre solo al llegar recién abierta la mesa (state.openAdd), una vez.
  const pendingAdd = useRef(location.state?.openAdd ? saleId : null)
  // Si se llegó desde las mesas, "← Mesas" vuelve atrás en el historial en vez de apilar otra entrada.
  // El componente sobrevive al cambio de cuenta (onSelect), así que el ref se conserva.
  const fromTables = useRef(Boolean(location.state?.fromTables))
  const [moving, setMoving] = useState(false)
  const { data: sale } = useSale(saleId)
  const salonId = sale?.table?.salon_id
  const { data: floor } = useFloor(salonId, { enabled: Boolean(salonId) })
  const siblings = floor?.tables.find((table) => table.id === sale?.table?.id)?.sales ?? []

  // SalePanel lee initialModal solo al montar. Corre antes del efecto que apila la hoja, y el
  // replaceState crudo conserva idx/key para no afectar al router; así recargar o volver no reabre la hoja.
  // Se quita solo openAdd: fromTables queda para que "← Mesas" siga volviendo atrás después de recargar.
  useLayoutEffect(() => {
    pendingAdd.current = null
    const state = window.history.state
    if (state?.usr?.openAdd) {
      const usr = { ...state.usr }
      delete usr.openAdd
      window.history.replaceState({ ...state, usr: Object.keys(usr).length ? usr : null }, '')
    }
  }, [])

  const goTables = (replace) => navigate(salonId ? `/camarero?salon=${salonId}` : '/camarero', { replace })

  // Si hay una hoja cerrándose (p. ej. "Venta cerrada"), su entrada se retira primero (o se reemplaza).
  const backToTables = () => {
    const action = backToTablesAction({
      fromTables: fromTables.current,
      sheetOnTop: Boolean(window.history.state?.posSheet),
    })
    if (action.kind === 'tables') goTables(action.replace)
    else if (action.afterSheet) afterSheetBack(() => navigate(-1), () => goTables(true))
    else navigate(-1)
  }

  // Al dividir, la hoja todavía está encima: se reemplaza la entrada de la venta después de que se retire.
  const selectSale = (id) => afterSheetBack(() =>
    navigate(`/camarero/venta/${id}`, { replace: true, state: fromTables.current ? { fromTables: true } : undefined }))

  return (
    <div className="h-full">
      <SalePanel key={saleId} saleId={saleId} variant="screen" closeLabel="Mesas" siblings={siblings}
        initialModal={pendingAdd.current === saleId ? 'add' : null}
        onSelect={selectSale}
        onClose={backToTables}
        onStartMove={() => setMoving(true)} />
      {moving && sale && <MoveSheet sale={sale} onClose={() => setMoving(false)} />}
    </div>
  )
}
