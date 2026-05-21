import { useNavigate } from 'react-router-dom'
import { LogOut, Search, Settings, MapPin, List } from 'lucide-react'
import GALIA from '../../constants/colors'

const PosHeader = ({ salons = [], activeSalon, onSalonChange, onSearch, isEditMode, onEditModeToggle, viewMode = 'map', onViewModeChange }) => {
  const navigate = useNavigate()

  const handleExit = () => {
    navigate('/dashboard')
  }

  const activeSalonName = salons.find(s => s.id === activeSalon)?.name || 'Seleccionar salón'

  return (
    <header style={{ backgroundColor: '#4a4a4a' }} className="flex flex-col">
      {/* Top bar with salon dropdown */}
      <div className="h-12 flex items-center px-4 md:px-6 gap-3 md:gap-6 text-white text-sm font-medium">
        {/* Salon selector dropdown */}
        <select
          value={activeSalon || ''}
          onChange={(e) => onSalonChange?.(e.target.value)}
          className="bg-gray-600 text-white rounded px-3 py-1.5 text-sm font-medium cursor-pointer hover:bg-gray-500 transition-colors"
        >
          <option value="">Seleccionar salón</option>
          {salons.map((salon) => (
            <option key={salon.id} value={salon.id}>
              {salon.name}
            </option>
          ))}
        </select>

        {/* View mode toggle buttons */}
        <div className="flex gap-1 bg-gray-600 rounded p-1">
          <button
            onClick={() => onViewModeChange?.('map')}
            className={`flex items-center gap-2 px-3 py-1 rounded transition-colors ${
              viewMode === 'map'
                ? 'bg-white text-gray-900 font-medium'
                : 'text-white hover:bg-gray-500'
            }`}
            title="Vista de mapa"
          >
            <MapPin size={16} />
            <span className="hidden sm:inline text-xs font-medium">Mapa</span>
          </button>
          <button
            onClick={() => onViewModeChange?.('list')}
            className={`flex items-center gap-2 px-3 py-1 rounded transition-colors ${
              viewMode === 'list'
                ? 'bg-white text-gray-900 font-medium'
                : 'text-white hover:bg-gray-500'
            }`}
            title="Vista de lista"
          >
            <List size={16} />
            <span className="hidden sm:inline text-xs font-medium">Lista</span>
          </button>
        </div>

        <div className="ml-auto flex items-center gap-2">
          {/* Edit mode toggle */}
          <button
            onClick={onEditModeToggle}
            className={`flex items-center gap-2 px-2 md:px-4 py-1.5 rounded transition-colors ${
              isEditMode
                ? 'bg-yellow-500 text-gray-900 hover:bg-yellow-600'
                : 'text-white hover:bg-gray-600'
            }`}
            title={isEditMode ? 'Desactivar modo edición' : 'Activar modo edición (arrastra mesas)'}
          >
            <Settings size={18} />
            <span className="hidden md:inline text-sm font-medium">{isEditMode ? 'Edición' : 'Organizar'}</span>
          </button>

          {/* Exit button */}
          <button
            onClick={handleExit}
            className="flex items-center gap-2 px-2 md:px-4 py-1.5 rounded transition-colors hover:bg-gray-600"
            title="Salir del POS"
          >
            <LogOut size={18} />
            <span className="hidden md:inline text-sm font-medium">Salir</span>
          </button>
        </div>
      </div>
    </header>
  )
}

export default PosHeader
