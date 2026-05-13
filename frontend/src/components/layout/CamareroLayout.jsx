import { Outlet, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

const CamareroLayout = () => {
  const navigate = useNavigate()

  return (
    <div className="h-screen w-screen flex flex-col bg-gray-50 overflow-hidden">
      <header className="flex items-center gap-3 px-4 py-3 bg-white border-b shadow-sm shrink-0">
        <button onClick={() => navigate(-1)} className="p-1 rounded hover:bg-gray-100">
          <ArrowLeft className="h-5 w-5 text-gray-700" />
        </button>
        <span className="font-semibold text-gray-800 flex-1">Camarero</span>
      </header>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}

export default CamareroLayout
