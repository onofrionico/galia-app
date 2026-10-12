import { Minus, Plus } from 'lucide-react'
import FloorPlan from '@/pos/floor/FloorPlan'
import { usePinchZoom } from './hooks/usePinchZoom'
import { isDimmed } from './utils/tableFilters'
import { MAX_ZOOM, MIN_ZOOM, stepZoom } from './utils/zoom'

const zoomButton =
  'flex h-12 w-12 items-center justify-center rounded-full bg-white text-galia-plum shadow-md disabled:opacity-40'

// Plano de solo lectura con zoom (pellizco o +/−); FloorPlan se escala al ancho de su contenedor.
export default function FloorView({ tables, filter, userId, onTableClick }) {
  const { zoom, setZoom, handlers } = usePinchZoom()

  return (
    <div className="relative h-full">
      <div className="h-full overflow-auto p-3" style={{ touchAction: 'pan-x pan-y' }} {...handlers}>
        <div style={{ width: `${zoom * 100}%` }}>
          <FloorPlan tables={tables} isDimmed={(table) => isDimmed(table, filter, userId)} onTableClick={onTableClick} />
        </div>
      </div>
      <div className="absolute bottom-[calc(env(safe-area-inset-bottom)+1rem)] right-4 flex flex-col gap-2">
        <button type="button" aria-label="Acercar" disabled={zoom >= MAX_ZOOM}
          onClick={() => setZoom((z) => stepZoom(z, 1))} className={zoomButton}>
          <Plus size={22} />
        </button>
        <button type="button" aria-label="Alejar" disabled={zoom <= MIN_ZOOM}
          onClick={() => setZoom((z) => stepZoom(z, -1))} className={zoomButton}>
          <Minus size={22} />
        </button>
      </div>
    </div>
  )
}
