import GALIA from '../../constants/colors'
import MesaCard from './MesaCard'

const PosMain = ({ mesas, onMesaClick, activeSalonMesas }) => {
  // Responsive grid: 6 cols (1440+), 4 cols (1080), 3 cols (768), 2 cols (mobile)
  const gridColsClass = 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6'

  return (
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
  )
}

export default PosMain
