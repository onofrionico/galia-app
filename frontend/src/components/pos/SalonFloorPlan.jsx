import MesaCard from './MesaCard'

const SalonFloorPlan = ({ mesas = [], onMesaClick, isEditMode, onMesaDrag, style }) => {
  const handleDragStart = (e, mesa) => {
    if (!isEditMode) return
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('mesaId', mesa.id)

    // Create a custom drag image to fix cursor offset
    const img = new Image()
    img.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60"><rect width="60" height="60" fill="%23ddd" stroke="%23999" stroke-width="2" rx="4"/><text x="30" y="35" text-anchor="middle" font-size="12" fill="%23333">Moving</text></svg>'
    e.dataTransfer.setDragImage(img, 30, 30)
  }

  const handleDragOver = (e) => {
    if (!isEditMode) return
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = (e, x, y) => {
    if (!isEditMode) return
    e.preventDefault()
    const mesaId = parseInt(e.dataTransfer.getData('mesaId'))
    if (onMesaDrag) {
      onMesaDrag(mesaId, x, y)
    }
  }

  return (
    <div
      className={`
        relative w-full bg-slate-100 border-2 border-slate-300 rounded-lg
        ${isEditMode ? 'cursor-move' : 'cursor-default'}
      `}
      style={{
        height: '400px',
        minHeight: '400px',
        ...style,
      }}
      onDragOver={handleDragOver}
      onDrop={(e) => {
        const rect = e.currentTarget.getBoundingClientRect()
        let x = ((e.clientX - rect.left) / rect.width) * 100
        let y = ((e.clientY - rect.top) / rect.height) * 100
        // Center the mesa on the cursor position
        const mesaId = parseInt(e.dataTransfer.getData('mesaId'))
        const mesa = mesas.find(m => m.id === mesaId)
        if (mesa) {
          x = Math.max(0, x - mesa.width / 2)
          y = Math.max(0, y - mesa.height / 2)
        }
        handleDrop(e, x, y)
      }}
    >
      {mesas.map((mesa) => (
        <div
          key={mesa.id}
          onClick={() => !isEditMode && onMesaClick?.(mesa)}
          draggable={isEditMode}
          onDragStart={(e) => handleDragStart(e, mesa)}
          style={{
            position: 'absolute',
            left: `${mesa.pos_x}%`,
            top: `${mesa.pos_y}%`,
            width: `${mesa.width}%`,
            height: `${mesa.height}%`,
            minWidth: '60px',
            minHeight: '60px',
          }}
          className={isEditMode ? 'opacity-70' : ''}
        >
          <MesaCard mesa={mesa} />
        </div>
      ))}

      {isEditMode && (
        <div className="absolute bottom-2 right-2 bg-blue-500 text-white text-xs px-2 py-1 rounded">
          Modo edición activado
        </div>
      )}
    </div>
  )
}

export default SalonFloorPlan
