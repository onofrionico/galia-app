import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import salonsService from '../services/salonsService'
import ordersService from '../services/ordersService'
import GALIA from '../constants/colors'
import { ChevronLeft } from 'lucide-react'

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

  if (loading) return <div className="flex items-center justify-center h-full" style={{ backgroundColor: GALIA.crema }}>Cargando...</div>

  const activeMesas = allMesas[activeSalon] || []
  const mesasWithOrders = activeMesas.map(m => ({
    ...m,
    openOrder: openOrders.find(o => o.mesa_id === m.id) || null
  }))

  return (
    <div className="h-full w-full flex flex-col" style={{ backgroundColor: GALIA.crema }}>
      {/* Header */}
      <div className="h-14 flex items-center px-4 text-white font-semibold text-lg" style={{ backgroundColor: GALIA.marron }}>
        Mi Turno - Camarero
      </div>

      {/* Salon tabs */}
      <div className="flex gap-2 px-3 py-2 overflow-x-auto border-b" style={{ borderColor: GALIA.grisLigero }}>
        {salons.map(salon => (
          <button
            key={salon.id}
            onClick={() => setActiveSalon(salon.id)}
            className="px-4 py-2 whitespace-nowrap text-sm rounded transition"
            style={{
              borderBottom: activeSalon === salon.id ? `3px solid ${GALIA.amarillo}` : 'none',
              color: activeSalon === salon.id ? GALIA.marron : GALIA.grisClaro,
              fontWeight: activeSalon === salon.id ? '600' : '400'
            }}
          >
            {salon.name}
          </button>
        ))}
      </div>

      {/* Mesas grid */}
      <div className="flex-1 overflow-y-auto p-3">
        <div className="grid grid-cols-2 gap-3">
          {mesasWithOrders.map(mesa => (
            <button
              key={mesa.id}
              onClick={() => handleMesaClick(mesa)}
              className="p-3 rounded-lg border transition-all cursor-pointer"
              style={{
                backgroundColor: GALIA.blanco,
                borderColor: mesa.status === 'ocupada' ? GALIA.amarillo : GALIA.grisLigero,
                borderWidth: mesa.status === 'ocupada' ? '2px' : '1px'
              }}
            >
              <div className="text-2xl font-bold" style={{ color: GALIA.marron }}>
                {mesa.numero}
              </div>
              <div className="mt-2 flex items-center justify-between">
                <div className="text-xs font-semibold rounded-full px-2 py-1" style={{
                  backgroundColor: mesa.status === 'libre' ? GALIA.verde : GALIA.amarillo,
                  color: mesa.status === 'libre' ? 'white' : GALIA.marron
                }}>
                  {mesa.status === 'libre' ? 'Libre' : 'Ocupada'}
                </div>
              </div>
              {mesa.openOrder && (
                <div className="mt-2 text-xs" style={{ color: GALIA.grisClaro }}>
                  {mesa.openOrder.items?.length || 0} ítems
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-3 text-sm" style={{ backgroundColor: '#fee', color: '#c33' }}>
          {error}
        </div>
      )}
    </div>
  )
}

export default Camarero
