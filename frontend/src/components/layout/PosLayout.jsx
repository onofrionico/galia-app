import { Outlet, useNavigate } from 'react-router-dom'

const PosLayout = () => {
  const navigate = useNavigate()

  const handleSalir = () => {
    navigate('/dashboard')
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-900 text-white overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 border-b border-slate-700 bg-slate-800 shrink-0">
        <span className="text-lg font-bold tracking-wide">Galia POS</span>
        <button
          onClick={handleSalir}
          className="text-sm text-slate-300 hover:text-white border border-slate-600 px-3 py-1 rounded transition"
        >
          Salir
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  )
}

export default PosLayout
