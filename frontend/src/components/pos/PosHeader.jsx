import { useNavigate } from 'react-router-dom'
import { LogOut, Search } from 'lucide-react'
import GALIA from '../../constants/colors'

const POS_MODES = ['Mesas', 'Mostrador', 'Delivery', 'Mostrador express']

const PosHeader = ({ activeMode = 'Mesas', onModeChange, onSearch }) => {
  const navigate = useNavigate()

  const handleExit = () => {
    navigate('/dashboard')
  }

  return (
    <header style={{ backgroundColor: '#4a4a4a' }} className="flex flex-col">
      {/* Top bar with modes */}
      <div className="h-12 flex items-center px-6 gap-6 text-white text-sm font-medium">
        {POS_MODES.map((mode) => (
          <button
            key={mode}
            onClick={() => onModeChange?.(mode)}
            className="transition-colors"
            style={{
              color: activeMode === mode ? '#fff' : '#ccc',
              borderBottom: activeMode === mode ? `3px solid ${GALIA.amarillo}` : 'none',
              paddingBottom: '6px'
            }}
          >
            {mode}
          </button>
        ))}

        <div className="ml-auto flex items-center gap-3">
          {/* Search */}
          <div className="flex items-center gap-2 bg-gray-600 rounded px-3 py-1">
            <Search size={16} className="text-gray-400" />
            <input
              type="text"
              placeholder="Ir a mesa"
              className="bg-transparent text-white text-sm outline-none placeholder-gray-400"
              onChange={(e) => onSearch?.(e.target.value)}
            />
          </div>

          {/* Hamburger menu */}
          <button className="p-1 hover:bg-gray-600 rounded">
            <div className="space-y-1">
              <div className="w-5 h-0.5 bg-white"></div>
              <div className="w-5 h-0.5 bg-white"></div>
              <div className="w-5 h-0.5 bg-white"></div>
            </div>
          </button>
        </div>
      </div>
    </header>
  )
}

export default PosHeader
