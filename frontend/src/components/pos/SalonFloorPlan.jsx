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
        relative bg-white border-4 border-gray-400 rounded-xl
        ${isEditMode ? 'cursor-move' : 'cursor-default'}
      `}
      style={{
        height: '800px',
        minHeight: '800px',
        width: '1400px',
        minWidth: '1400px',
        backgroundColor: '#fafafa',
        backgroundImage: 'linear-gradient(0deg, transparent 24%, rgba(200,200,200,.05) 25%, rgba(200,200,200,.05) 26%, transparent 27%, transparent 74%, rgba(200,200,200,.05) 75%, rgba(200,200,200,.05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(200,200,200,.05) 25%, rgba(200,200,200,.05) 26%, transparent 27%, transparent 74%, rgba(200,200,200,.05) 75%, rgba(200,200,200,.05) 76%, transparent 77%, transparent)',
        backgroundSize: '50px 50px',
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
          x = Math.max(0, Math.min(100 - (mesa.width || 5), x - (mesa.width || 5) / 2))
          y = Math.max(0, Math.min(100 - (mesa.height || 5), y - (mesa.height || 5) / 2))
        }
        handleDrop(e, x, y)
      }}
    >
      {/* Grid lines for reference */}
      <div className="absolute inset-0 opacity-10 pointer-events-none">
        {[...Array(5)].map((_, i) => (
          <div key={`v${i}`} className="absolute border-l border-gray-400" style={{ left: `${i * 20}%`, height: '100%' }} />
        ))}
        {[...Array(5)].map((_, i) => (
          <div key={`h${i}`} className="absolute border-t border-gray-400" style={{ top: `${i * 20}%`, width: '100%' }} />
        ))}
      </div>

      {/* Mesas */}
      {mesas.map((mesa) => (
        <div
          key={mesa.id}
          onClick={() => !isEditMode && onMesaClick?.(mesa)}
          draggable={isEditMode}
          onDragStart={(e) => handleDragStart(e, mesa)}
          style={{
            position: 'absolute',
            left: `${mesa.pos_x || 0}%`,
            top: `${mesa.pos_y || 0}%`,
            width: `${mesa.width || 5}%`,
            height: `${mesa.height || 5}%`,
            minWidth: '80px',
            minHeight: '80px',
          }}
          className={`${isEditMode ? 'opacity-85 hover:opacity-100' : ''} transition-opacity`}
        >
          <div className={`w-full h-full rounded-lg border-2 flex items-center justify-center font-bold text-lg cursor-grab active:cursor-grabbing shadow-md transition-all ${
            isEditMode ? 'bg-blue-100 border-blue-400 hover:shadow-lg' : 'bg-white border-gray-300'
          }`} style={{ color: mesa.status === 'libre' ? '#22c55e' : '#f59e0b' }}>
            {mesa.numero || mesa.number || mesa.id}
          </div>
        </div>
      ))}

      {/* Legend */}
      {isEditMode && (
        <div className="absolute bottom-4 left-4 bg-white border-2 border-gray-300 rounded-lg p-3 text-xs">
          <div className="font-bold mb-2">Total de mesas: {mesas.length}</div>
          <div>Libre: <span style={{ color: '#22c55e' }}>●</span></div>
          <div>Ocupada: <span style={{ color: '#f59e0b' }}>●</span></div>
        </div>
      )}

      {isEditMode && (
        <div className="absolute bottom-4 right-4 bg-yellow-400 text-gray-900 text-xs px-3 py-2 rounded-lg font-semibold">
          ✓ Modo edición - arrastra para mover
        </div>
      )}
    </div>
  )
}

export default SalonFloorPlan
