const MesaCard = ({ mesa, onClick, isDragging, style }) => {
  const getStatusColor = () => {
    switch (mesa.status) {
      case 'libre':
        return 'bg-green-100 border-green-500'
      case 'ocupada':
        return 'bg-red-100 border-red-500'
      case 'reservada':
        return 'bg-yellow-100 border-yellow-500'
      default:
        return 'bg-gray-100 border-gray-400'
    }
  }

  const getStatusTextColor = () => {
    switch (mesa.status) {
      case 'libre':
        return 'text-green-700'
      case 'ocupada':
        return 'text-red-700'
      case 'reservada':
        return 'text-yellow-700'
      default:
        return 'text-gray-700'
    }
  }

  const getStatusIcon = () => {
    switch (mesa.status) {
      case 'ocupada':
        return '🪑'
      case 'reservada':
        return '📋'
      default:
        return '🪑'
    }
  }

  return (
    <div
      onClick={onClick}
      style={style}
      className={`
        border-2 rounded-lg p-3 text-center cursor-pointer transition-all
        ${getStatusColor()}
        ${isDragging ? 'shadow-lg scale-110' : 'hover:shadow-md'}
      `}
    >
      <div className="text-2xl mb-1">{getStatusIcon()}</div>
      <div className={`font-bold text-sm mb-1 ${getStatusTextColor()}`}>
        Mesa {mesa.number}
        {mesa.name && <span className="text-xs block">{mesa.name}</span>}
      </div>
      {mesa.status === 'ocupada' && mesa.total !== undefined && (
        <div className={`text-sm font-semibold ${getStatusTextColor()}`}>
          ${mesa.total}
        </div>
      )}
      {mesa.status === 'reservada' && mesa.time && (
        <div className="text-xs text-yellow-600">{mesa.time}</div>
      )}
      {mesa.capacity && (
        <div className="text-xs text-gray-600 mt-1">Cap: {mesa.capacity}</div>
      )}
      <div className={`text-xs font-medium mt-1 ${getStatusTextColor()}`}>
        {mesa.status === 'libre' && 'Libre'}
        {mesa.status === 'ocupada' && 'Ocupada'}
        {mesa.status === 'reservada' && 'Reservada'}
      </div>
    </div>
  )
}

export default MesaCard
