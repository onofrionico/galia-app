import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import salonsService from '../services/salonsService'
import ordersService from '../services/ordersService'
import SalonFloorPlan from '../components/pos/SalonFloorPlan'
import { ChefHat } from 'lucide-react'

const Camarero = () => {
  const navigate = useNavigate()

  const [salons, setSalons] = useState([])
  const [activeSalon, setActiveSalon] = useState(null)
  const [allMesas, setAllMesas] = useState({})
  const [openOrders, setOpenOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Polling every 10 seconds
  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchAll = async () => {
    try {
      const [salonRes, ordersRes] = await Promise.all([
        salonsService.getSalons({ include_inactive: false }),
        ordersService.getOrders({ status: 'abierta' })
      ])

      setSalons(salonRes.salons || [])
      setOpenOrders(ordersRes.orders || [])

      const mesasMap = {}
      for (const salon of salonRes.salons || []) {
        const mesasRes = await salonsService.getMesas(salon.id)
        mesasMap[salon.id] = mesasRes.mesas || []
      }
      setAllMesas(mesasMap)

      if (salonRes.salons && salonRes.salons.length > 0 && !activeSalon) {
        setActiveSalon(salonRes.salons[0].id)
      }
    } catch (err) {
      setError('Error al cargar datos')
    } finally {
      setLoading(false)
    }
  }

  const handleMesaClick = async (mesa) => {
    if (mesa.status === 'libre') {
      // Create new order
      try {
        const order = await ordersService.createOrder({
          mesa_id: mesa.id,
          salon_id: activeSalon
        })
        navigate(`/camarero/mesa/${mesa.id}`, { state: { orderId: order.id } })
      } catch (err) {
        setError('Error al crear orden')
      }
    } else if (mesa.status === 'ocupada') {
      // Open existing order
      const order = openOrders.find(o => o.mesa_id === mesa.id)
      if (order) {
        navigate(`/camarero/mesa/${mesa.id}`, { state: { orderId: order.id } })
      }
    }
  }

  if (loading) return <div className="flex items-center justify-center h-full">Cargando...</div>

  const activeMesas = allMesas[activeSalon] || []
  const mesasWithOrders = activeMesas.map(m => ({
    ...m,
    openOrder: openOrders.find(o => o.mesa_id === m.id) || null
  }))

  return (
    <div className="h-full w-full flex flex-col bg-gray-50">
      {/* Custom header for this page */}
      <div className="px-4 py-3 bg-white border-b">
        <div className="flex items-center gap-2">
          <ChefHat className="h-5 w-5 text-blue-600" />
          <h1 className="text-lg font-semibold text-gray-800">Mi Turno</h1>
        </div>
      </div>

      {/* Salon tabs */}
      <div className="flex gap-2 px-4 py-2 overflow-x-auto border-b bg-white">
        {salons.map(salon => (
          <button
            key={salon.id}
            onClick={() => setActiveSalon(salon.id)}
            className={`px-4 py-2 whitespace-nowrap rounded transition ${
              activeSalon === salon.id
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {salon.name}
          </button>
        ))}
      </div>

      {/* Floor plan */}
      <div className="flex-1 overflow-hidden p-4">
        <SalonFloorPlan
          mesas={mesasWithOrders}
          onMesaClick={handleMesaClick}
        />
      </div>

      {error && (
        <div className="p-4 bg-red-100 text-red-700 text-sm">
          {error}
        </div>
      )}
    </div>
  )
}

export default Camarero
