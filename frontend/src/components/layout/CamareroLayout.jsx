import { Outlet } from 'react-router-dom'
import GALIA from '../../constants/colors'

const CamareroLayout = () => {
  return (
    <div className="h-screen w-screen flex flex-col" style={{ backgroundColor: GALIA.crema }}>
      {/* Camarero Header - sticky */}
      <header className="h-14 flex items-center justify-center" style={{ backgroundColor: GALIA.marron }}>
        <h1 className="text-white text-lg font-semibold">Mi Turno - Camarero</h1>
      </header>

      {/* Content area */}
      <div className="flex-1 overflow-hidden">
        <Outlet />
      </div>
    </div>
  )
}

export default CamareroLayout
