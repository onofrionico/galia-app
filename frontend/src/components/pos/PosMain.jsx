import GALIA from '../../constants/colors'
import MesaCard from './MesaCard'

const PosMain = ({ salons, mesas, onMesaClick, activeSalonMesas, activeSalon, onSalonChange }) => {
  // Responsive grid: 6 cols (1440+), 4 cols (1080), 3 cols (768), 2 cols (mobile)
  const gridColsClass = 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6'

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Left sidebar - Salon selector */}
      <div className="w-32 border-r" style={{ backgroundColor: GALIA.crema, borderColor: GALIA.grisLigero }}>
        <div className="p-2 space-y-1">
          {salons.map((salon) => (
            <button
              key={salon.id}
              onClick={() => onSalonChange(salon.id)}
              className="w-full px-3 py-2 rounded text-sm font-medium transition text-left"
              style={{
                backgroundColor: activeSalon === salon.id ? GALIA.amarillo : 'transparent',
                color: activeSalon === salon.id ? GALIA.marron : GALIA.marron
              }}
            >
              {salon.name}
            </button>
          ))}
        </div>
      </div>

      {/* Center - Mesas grid */}
      <div
        className={`flex-1 overflow-auto p-6 grid ${gridColsClass} gap-4 auto-rows-max`}
        style={{ backgroundColor: GALIA.crema }}
      >
        {activeSalonMesas.map((mesa) => (
          <MesaCard
            key={mesa.id}
            mesa={mesa}
            onClick={() => onMesaClick(mesa)}
          />
        ))}
      </div>
    </div>
  )
}

export default PosMain
