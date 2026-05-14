import { useNavigate } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import GALIA from '../../constants/colors'

const PosHeader = ({ salons, activeSalon, onSalonChange }) => {
  const navigate = useNavigate()

  const handleExit = () => {
    navigate('/dashboard')
  }

  return (
    <header
      className="h-16 flex items-center justify-between px-6"
      style={{ backgroundColor: GALIA.crema }}
    >
      {/* Logo/Title */}
      <h1 className="text-2xl font-bold" style={{ color: GALIA.marron }}>
        GALIA POS
      </h1>

      {/* Salon Selector - Tabs */}
      <div className="flex gap-4">
        {salons.map((salon) => (
          <button
            key={salon.id}
            onClick={() => onSalonChange(salon.id)}
            className="px-4 py-2 text-sm font-medium transition-colors duration-200"
            style={{
              color: activeSalon === salon.id ? GALIA.marron : GALIA.grisClaro,
              borderBottom: activeSalon === salon.id ? `2px solid ${GALIA.amarillo}` : 'none',
            }}
          >
            {salon.name}
          </button>
        ))}
      </div>

      {/* Exit Button */}
      <button
        onClick={handleExit}
        className="flex items-center gap-2 px-4 py-2 rounded transition-colors duration-200"
        style={{
          color: GALIA.marron,
          backgroundColor: 'transparent',
        }}
        onMouseEnter={(e) => (e.target.style.backgroundColor = GALIA.amarillo)}
        onMouseLeave={(e) => (e.target.style.backgroundColor = 'transparent')}
      >
        <LogOut size={18} />
        Salir
      </button>
    </header>
  )
}

export default PosHeader
