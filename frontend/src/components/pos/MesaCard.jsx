import GALIA from '../../constants/colors'

const MesaCard = ({ mesa, onClick, isDragging, style }) => {
  const getStatusBadgeColor = () => {
    switch (mesa.status) {
      case 'libre':
        return { bg: GALIA.verde, text: 'white' }
      case 'ocupada':
        return { bg: GALIA.amarillo, text: GALIA.marron }
      case 'reservada':
        return { bg: GALIA.grisLigero, text: GALIA.grisClaro }
      default:
        return { bg: GALIA.grisLigero, text: GALIA.grisClaro }
    }
  }

  const getStatusText = () => {
    switch (mesa.status) {
      case 'libre':
        return 'Libre'
      case 'ocupada':
        return 'Ocupada'
      case 'reservada':
        return 'Reservada'
      default:
        return 'Desconocido'
    }
  }

  const statusColors = getStatusBadgeColor()

  return (
    <div
      onClick={onClick}
      style={{
        backgroundColor: GALIA.blanco,
        borderWidth: '2px',
        borderColor: isDragging ? GALIA.amarillo : GALIA.grisLigero,
        boxShadow: isDragging ? '0 10px 15px rgba(0, 0, 0, 0.1)' : 'none',
        ...style
      }}
      className="rounded-lg p-4 cursor-pointer transition-all duration-200"
    >
      {/* Mesa Number */}
      <div className="text-4xl font-bold mb-2" style={{ color: GALIA.marron }}>
        {mesa.number}
      </div>

      {/* Status Badge */}
      <div
        className="rounded-full px-3 py-1 text-xs font-semibold mb-2 inline-block"
        style={{ backgroundColor: statusColors.bg, color: statusColors.text }}
      >
        {getStatusText()}
      </div>

      {/* Items & Total (only if occupied) */}
      {mesa.status === 'ocupada' && mesa.openOrder && (
        <div className="text-sm mt-2" style={{ color: GALIA.grisClaro }}>
          <div>{mesa.openOrder.items?.length || 0} ítems</div>
          <div className="font-semibold" style={{ color: GALIA.marron }}>
            ${parseFloat(mesa.openOrder.total).toFixed(2)}
          </div>
        </div>
      )}

      {/* Capacity */}
      {mesa.capacity && (
        <div className="text-xs mt-2" style={{ color: GALIA.grisClaro }}>
          Cap: {mesa.capacity}
        </div>
      )}
    </div>
  )
}

export default MesaCard
