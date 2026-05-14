// frontend/src/components/layout/PosLayout.jsx
import { Outlet } from 'react-router-dom'
import GALIA from '../../constants/colors'

const PosLayout = () => {
  return (
    <div className="h-screen w-screen flex flex-col" style={{ backgroundColor: GALIA.crema }}>
      {/* POS Header will be rendered inside Pos.jsx */}
      <div className="flex-1 overflow-hidden">
        <Outlet />
      </div>
    </div>
  )
}

export default PosLayout
