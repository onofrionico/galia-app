import { useState, useEffect } from 'react'
import { Settings2 } from 'lucide-react'
import salonsService from '../services/salonsService'
import salesService from '../services/salesService'
import PosModal from '../components/pos/PosModal'
import OrderDrawer from '../components/pos/OrderDrawer'
import SalonFloorPlan from '../components/pos/SalonFloorPlan'

const Pos = () => {
  const [salons, setSalons] = useState([])
  const [activeSalon, setActiveSalon] = useState(null)
  const [mesas, setMesas] = useState([])
  const [dailySummary, setDailySummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editMode, setEditMode] = useState(false)

  const [showPosModal, setShowPosModal] = useState(false)
  const [selectedMesa, setSelectedMesa] = useState(null)
  const [showOrderDrawer, setShowOrderDrawer] = useState(false)
  const [orderData, setOrderData] = useState(null)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchDailySummary, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (activeSalon) {
      fetchMesas(activeSalon)
    }
  }, [activeSalon])

  const fetchData = async () => {
    try {
      const salonRes = await salonsService.getSalons({
        include_inactive: false,
      })
      setSalons(salonRes.salons || [])

      if (salonRes.salons && salonRes.salons.length > 0) {
        setActiveSalon(salonRes.salons[0].id)
      }

      await fetchDailySummary()
    } catch (err) {
      setError('Error al cargar salones')
    } finally {
      setLoading(false)
    }
  }

  const fetchMesas = async (salonId) => {
    try {
      const response = await salonsService.getMesas(salonId)
      setMesas(response.mesas || [])
    } catch (err) {
      setError('Error al cargar mesas')
    }
  }

  const fetchDailySummary = async () => {
    try {
      const response = await salesService.getDailySummary()
      setDailySummary(response)
    } catch (err) {
      console.error('Error fetching daily summary:', err)
    }
  }

  const handleMesaClick = (mesa) => {
    if (mesa.status === 'libre') {
      setSelectedMesa(mesa)
      setShowPosModal(true)
    } else if (mesa.status === 'ocupada') {
      setSelectedMesa(mesa)
      setOrderData({
        items: [
          {
            product_name: 'Sample',
            variant_name: 'Test',
            quantity: 1,
            subtotal: 100,
          },
        ],
      })
      setShowOrderDrawer(true)
    }
  }

  const handleSale = async (saleData) => {
    try {
      await salesService.createSale(
        saleData.items,
        saleData.mesa_id,
        saleData.medio_pago
      )

      await fetchMesas(activeSalon)
      await fetchDailySummary()

      setShowPosModal(false)
      setSelectedMesa(null)
      setError('')
    } catch (err) {
      setError(err.response?.data?.error || 'Error al registrar venta')
    }
  }

  const handleAddItem = () => {
    setShowOrderDrawer(false)
    setShowPosModal(true)
  }

  if (loading) {
    return <div className="p-6">Cargando POS...</div>
  }

  const currentSalon = salons.find((s) => s.id === activeSalon)

  return (
    <div className="h-screen flex flex-col bg-slate-900 text-white">
      <div className="p-4 border-b border-slate-700">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold">🛒 Caja — {currentSalon?.name}</h1>
          <div className="flex gap-2 text-xs">
            <span className="text-green-400">● {mesas.filter((m) => m.status === 'libre').length} libres</span>
            <span className="text-red-400">● {mesas.filter((m) => m.status === 'ocupada').length} ocupadas</span>
            {mesas.filter((m) => m.status === 'reservada').length > 0 && (
              <span className="text-yellow-400">
                ● {mesas.filter((m) => m.status === 'reservada').length} reservadas
              </span>
            )}
          </div>
        </div>

        <div className="flex gap-2 overflow-x-auto">
          {salons.map((salon) => (
            <button
              key={salon.id}
              onClick={() => setActiveSalon(salon.id)}
              className={`px-4 py-2 rounded whitespace-nowrap transition ${
                activeSalon === salon.id
                  ? 'bg-green-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {salon.name}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="bg-red-900 border-b border-red-700 text-red-200 px-4 py-2">
          {error}
        </div>
      )}

      <div className="flex-1 relative overflow-hidden p-4">
        {activeSalon && (
          <SalonFloorPlan
            mesas={mesas}
            onMesaClick={handleMesaClick}
            isEditMode={editMode}
            style={{
              background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
            }}
          />
        )}

        <button
          onClick={() => setEditMode(!editMode)}
          className={`absolute bottom-6 right-6 flex items-center gap-2 px-4 py-2 rounded transition ${
            editMode
              ? 'bg-yellow-600 hover:bg-yellow-700'
              : 'bg-slate-700 hover:bg-slate-600'
          }`}
        >
          <Settings2 size={18} /> {editMode ? 'Guardar Plano' : '⚙️ Editar Plano'}
        </button>
      </div>

      <div className="border-t border-slate-700 p-4 bg-slate-800">
        <div className="flex gap-6 text-sm justify-center">
          {dailySummary && (
            <>
              <div>
                <span className="text-green-400 font-bold">
                  ${dailySummary.total_vendido.toFixed(2)}
                </span>
                <span className="text-slate-400 ml-2">vendidos hoy</span>
              </div>
              <div>
                <span className="text-purple-400 font-bold">
                  {dailySummary.cantidad_ventas}
                </span>
                <span className="text-slate-400 ml-2">ventas</span>
              </div>
              {dailySummary.bajo_stock_count > 0 && (
                <div className="text-red-400">
                  ⚠️ {dailySummary.bajo_stock_count} con stock bajo
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {showPosModal && (
        <PosModal
          mesaId={selectedMesa?.id}
          onClose={() => {
            setShowPosModal(false)
            setSelectedMesa(null)
          }}
          onSale={handleSale}
        />
      )}

      {showOrderDrawer && selectedMesa && (
        <OrderDrawer
          mesa={selectedMesa}
          saleData={orderData}
          onAddItem={handleAddItem}
          onClose={() => {
            setShowOrderDrawer(false)
            setSelectedMesa(null)
            setOrderData(null)
          }}
          onCobrar={() => {
            setShowOrderDrawer(false)
            setSelectedMesa(null)
          }}
        />
      )}
    </div>
  )
}

export default Pos
