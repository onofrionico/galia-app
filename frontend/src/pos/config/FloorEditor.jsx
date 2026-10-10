import { useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { posConfigApi } from '../api/posApi'
import { posKeys } from '../hooks/keys'
import { useConfigMutation } from '../hooks/useConfigMutation'
import { useElementWidth } from '../hooks/useElementWidth'
import { btn } from '../ui/buttons'
import { LOGICAL_WIDTH, canvasHeight, clampPosition, clampSize, snap } from '../utils/floor'
import TableForm from './TableForm'

export default function FloorEditor({ salon }) {
  const queryClient = useQueryClient()
  const { data: tables = [] } = useQuery({
    queryKey: posKeys.tables(salon.id),
    queryFn: () => posConfigApi.listTables(salon.id),
  })
  const ref = useRef(null)
  const width = useElementWidth(ref)
  const scale = width / LOGICAL_WIDTH
  const [drafts, setDrafts] = useState({})
  const [selectedId, setSelectedId] = useState(null)
  const drag = useRef(null)
  const update = useConfigMutation(({ id, ...body }) => posConfigApi.updateTable(id, body))
  const create = useConfigMutation((body) => posConfigApi.createTable(body))

  const shown = tables.map((t) => ({ ...t, ...drafts[t.id] }))
  const selected = shown.find((t) => t.id === selectedId) ?? null

  const clearDraft = (id) => setDrafts(({ [id]: _removed, ...rest }) => rest)

  const save = (id, body, onDone) => update.mutate({ id, ...body }, {
    onSuccess: (table) => {
      queryClient.setQueryData(posKeys.tables(salon.id), (list = []) => list.map((t) => (t.id === table.id ? table : t)))
    },
    onSettled: onDone,
  })

  const startDrag = (event, table, mode) => {
    event.preventDefault()
    event.stopPropagation()
    event.currentTarget.setPointerCapture(event.pointerId)
    setSelectedId(table.id)
    drag.current = {
      id: table.id, mode, startX: event.clientX, startY: event.clientY,
      origin: { pos_x: table.pos_x, pos_y: table.pos_y, width: table.width, height: table.height },
    }
  }

  const onPointerMove = (event) => {
    const current = drag.current
    if (!current || !scale) return
    const dx = (event.clientX - current.startX) / scale
    const dy = (event.clientY - current.startY) / scale
    const { origin } = current
    const next = current.mode === 'move'
      ? clampPosition({ pos_x: snap(origin.pos_x + dx), pos_y: snap(origin.pos_y + dy), width: origin.width })
      : clampSize({ pos_x: origin.pos_x, width: snap(origin.width + dx), height: snap(origin.height + dy) })
    setDrafts((all) => ({ ...all, [current.id]: next }))
  }

  const onPointerUp = () => {
    const current = drag.current
    drag.current = null
    if (!current) return
    const draft = drafts[current.id]
    const changed = draft
      ? Object.fromEntries(Object.entries(draft).filter(([key, value]) => current.origin[key] !== value))
      : {}
    if (Object.keys(changed).length === 0) {
      clearDraft(current.id)
      return
    }
    save(current.id, changed, () => clearDraft(current.id))
  }

  const addTable = () => {
    const number = Math.max(0, ...tables.map((t) => t.number)) + 1
    create.mutate({ salon_id: salon.id, number, pos_x: 2, pos_y: 2, width: 10, height: 10 }, {
      onSuccess: (table) => setSelectedId(table.id),
    })
  }

  return (
    <div className="flex gap-4">
      <div className="min-w-0 flex-1">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-galia-plum">{salon.name}</h2>
          <button type="button" className={btn('primary')} onClick={addTable} disabled={create.isPending}>
            <Plus size={18} /> Agregar mesa
          </button>
        </div>
        <p className="mb-2 text-sm text-gray-600">Arrastrá las mesas para ubicarlas; la esquina inferior derecha cambia el tamaño.</p>
        <div ref={ref} onPointerMove={onPointerMove} onPointerUp={onPointerUp}
          className="relative w-full rounded-xl border border-dashed border-gray-300 bg-white"
          style={{
            height: width ? canvasHeight(shown) * scale : 400,
            backgroundImage: 'radial-gradient(circle, #d6d3d1 1px, transparent 1px)',
            backgroundSize: `${scale * 5}px ${scale * 5}px`,
          }}>
          {width > 0 && shown.map((table) => (
            <div key={table.id} onPointerDown={(e) => startDrag(e, table, 'move')}
              className={`absolute flex touch-none select-none items-center justify-center rounded-lg border-2 text-sm font-semibold ${
                table.id === selectedId ? 'border-galia-plum bg-galia-cream' : 'border-gray-400 bg-white'
              } ${table.is_active ? '' : 'opacity-40'}`}
              style={{ left: table.pos_x * scale, top: table.pos_y * scale, width: table.width * scale, height: table.height * scale, cursor: 'move' }}>
              {table.label}
              <span role="presentation" onPointerDown={(e) => startDrag(e, table, 'resize')}
                className="absolute bottom-0 right-0 h-4 w-4 cursor-se-resize rounded-tl bg-galia-plum/70" />
            </div>
          ))}
        </div>
      </div>
      <div className="w-72 flex-shrink-0">
        {selected
          ? <TableForm table={selected} busy={update.isPending} onSave={(body) => save(selected.id, body)} />
          : <p className="text-sm text-gray-600">Tocá una mesa para editar su número, nombre y capacidad.</p>}
      </div>
    </div>
  )
}
