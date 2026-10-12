import { useRef } from 'react'
import { useElementWidth } from '../hooks/useElementWidth'
import { useNow } from '../hooks/useNow'
import { LOGICAL_WIDTH, canvasHeight } from '../utils/floor'
import TableTile from './TableTile'

export default function FloorPlan({ tables, selectedTableId, picking = false, onTableClick, isDimmed = () => false }) {
  const ref = useRef(null)
  const width = useElementWidth(ref)
  const now = useNow()
  const scale = width / LOGICAL_WIDTH

  return (
    <div ref={ref} className="relative w-full rounded-xl border border-gray-200 bg-white"
      style={{ height: width ? canvasHeight(tables) * scale : 400 }}>
      {width > 0 && tables.map((table) => (
        <TableTile key={table.id} table={table} scale={scale} now={now} picking={picking}
          selected={table.id === selectedTableId} dimmed={isDimmed(table)} onClick={() => onTableClick(table)} />
      ))}
      {tables.length === 0 && (
        <p className="absolute inset-0 flex items-center justify-center text-gray-500">Este salón no tiene mesas.</p>
      )}
    </div>
  )
}
