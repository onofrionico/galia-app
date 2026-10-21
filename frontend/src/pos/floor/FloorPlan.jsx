import { useRef } from 'react'
import { useElementSize } from '../hooks/useElementWidth'
import { useNow } from '../hooks/useNow'
import { LOGICAL_WIDTH, canvasHeight, fitScale } from '../utils/floor'
import TableTile from './TableTile'

const BORDER = 2 // borde de 1px a cada lado del plano

// `fit`: el plano entra completo en el contenedor (ancho y alto), sin scroll. Sin `fit` se escala al ancho.
export default function FloorPlan({ tables, selectedTableId, picking = false, onTableClick, isDimmed = () => false,
  fit = false, className = '' }) {
  const ref = useRef(null)
  const { width, height } = useElementSize(ref)
  const now = useNow()
  const scale = Math.max(0, fitScale(width - BORDER, fit ? height - BORDER : null, tables))

  return (
    <div ref={ref} className={`w-full ${className}`}>
      <div className="relative rounded-xl border border-gray-200 bg-white"
        style={{
          width: fit && width ? LOGICAL_WIDTH * scale + BORDER : '100%',
          height: width ? canvasHeight(tables) * scale + BORDER : 400,
        }}>
        {width > 0 && tables.map((table) => (
          <TableTile key={table.id} table={table} scale={scale} now={now} picking={picking}
            selected={table.id === selectedTableId} dimmed={isDimmed(table)} onClick={() => onTableClick(table)} />
        ))}
        {tables.length === 0 && (
          <p className="absolute inset-0 flex items-center justify-center text-gray-500">Este salón no tiene mesas.</p>
        )}
      </div>
    </div>
  )
}
