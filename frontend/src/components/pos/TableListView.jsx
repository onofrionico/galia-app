import { ChevronRight, Users, Clock } from 'lucide-react'

const TableListView = ({ mesas = [], onMesaClick }) => {
  const getMesaStatusColor = (status) => {
    switch (status) {
      case 'libre':
        return 'bg-green-50 border-l-4 border-green-500'
      case 'ocupada':
        return 'bg-yellow-50 border-l-4 border-yellow-500'
      case 'reservada':
        return 'bg-blue-50 border-l-4 border-blue-500'
      default:
        return 'bg-gray-50 border-l-4 border-gray-300'
    }
  }

  const getMesaStatusLabel = (status) => {
    switch (status) {
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

  const getMesaStatusBadgeColor = (status) => {
    switch (status) {
      case 'libre':
        return 'bg-green-100 text-green-800'
      case 'ocupada':
        return 'bg-yellow-100 text-yellow-800'
      case 'reservada':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  // Ordenar mesas por número/id
  const sortedMesas = [...mesas].sort((a, b) => {
    const aNum = parseInt(a.numero || a.id) || 0
    const bNum = parseInt(b.numero || b.id) || 0
    return aNum - bNum
  })

  if (sortedMesas.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <Users size={48} className="mx-auto mb-4 opacity-50" />
          <p>No hay mesas disponibles</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="divide-y divide-gray-200">
          {sortedMesas.map((mesa) => (
            <div
              key={mesa.id}
              onClick={() => onMesaClick(mesa)}
              className={`${getMesaStatusColor(
                mesa.status
              )} p-4 cursor-pointer hover:shadow-md transition-shadow duration-200 flex items-center justify-between`}
            >
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-bold text-gray-900">
                    Mesa {mesa.numero || mesa.id}
                  </h3>
                  <span
                    className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${getMesaStatusBadgeColor(
                      mesa.status
                    )}`}
                  >
                    {getMesaStatusLabel(mesa.status)}
                  </span>
                </div>

                {/* Capacidad */}
                <div className="flex items-center gap-2 text-sm text-gray-700 mb-2">
                  <Users size={16} />
                  <span>Capacidad: {mesa.capacidad || 4} personas</span>
                </div>

                {/* Orden abierta */}
                {mesa.openOrder && (
                  <div className="flex items-center gap-2 text-sm text-gray-700">
                    <Clock size={16} />
                    <span>
                      Orden #{mesa.openOrder.id} - {mesa.openOrder.items_count || 0}{' '}
                      item{mesa.openOrder.items_count !== 1 ? 's' : ''}
                    </span>
                    {mesa.openOrder.total && (
                      <span className="ml-auto font-semibold text-gray-900">
                        ${parseFloat(mesa.openOrder.total).toFixed(2)}
                      </span>
                    )}
                  </div>
                )}

                {mesa.status === 'libre' && (
                  <div className="text-sm text-gray-600 mt-2">
                    Haz clic para crear una nueva orden
                  </div>
                )}
              </div>

              <div className="ml-4 flex-shrink-0">
                <ChevronRight size={24} className="text-gray-400" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default TableListView
