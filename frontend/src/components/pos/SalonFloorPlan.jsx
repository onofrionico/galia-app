import MesaCard from './MesaCard'

const SalonFloorPlan = ({ mesas = [], onMesaClick, isEditMode, onMesaDrag, style }) => {
  const handleDragStart = (e, mesa) => {
    if (!isEditMode) return
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('mesaId', mesa.id)
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
        const x = ((e.clientX - rect.left) / rect.width) * 100
        const y = ((e.clientY - rect.top) / rect.height) * 100
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
