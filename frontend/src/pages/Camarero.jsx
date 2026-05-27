import { useState, useEffect, useCallback } from 'react'
import { Map, List } from 'lucide-react'
import salonsService from '../services/salonsService'
import ordersService from '../services/ordersService'
import GALIA from '../constants/colors'
import SalonFloorPlan from '../components/pos/SalonFloorPlan'
import CamareroTableListView from '../components/camarero/CamareroTableListView'
import CamareroOrderBottomSheet from '../components/camarero/CamareroOrderBottomSheet'

const Camarero = () => {
  // View and salon state
  const [viewMode, setViewMode] = useState('map') // 'map' or 'list'
  const [salons, setSalons] = useState([])
  const [activeSalon, setActiveSalon] = useState(null)
  const [allMesas, setAllMesas] = useState({})
  const [openOrders, setOpenOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Order sheet state
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [showOrderSheet, setShowOrderSheet] = useState(false)
  const [selectedMesa, setSelectedMesa] = useState(null)

  const fetchAll = useCallback(async () => {
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
  }, [activeSalon])

  // Polling every 10 seconds
  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, 10000)
    return () => clearInterval(interval)
  }, [fetchAll])

  const handleMesaClick = async (mesa) => {
    setSelectedMesa(mesa)
    setError('')
    if (mesa.status === 'libre') {
      // Create new order
      try {
        const order = await ordersService.createOrder({
          mesa_id: mesa.id,
          salon_id: activeSalon
        })
        setSelectedOrder(order)
        setShowOrderSheet(true)
      } catch (err) {
        setError('Error al crear orden')
      }
    } else if (mesa.status === 'ocupada') {
      // Open existing order
      const order = openOrders.find(o => o.mesa_id === mesa.id)
      if (order) {
        try {
          const fullOrder = await ordersService.getOrder(order.id)
          setSelectedOrder(fullOrder)
          setShowOrderSheet(true)
        } catch (err) {
          setError('Error al cargar la orden')
        }
      } else {
        setError('No se encontró orden para esta mesa')
      }
    }
  }

  const handleAddItem = async (productVariantId, quantity) => {
    setError('')
    try {
      const updated = await ordersService.addItem(selectedOrder.id, {
        product_variant_id: productVariantId,
        quantity
      })
      setSelectedOrder(updated)
      await fetchAll()
    } catch (err) {
      setError('Error al agregar item')
    }
  }

  const handleRemoveItem = async (itemId) => {
    setError('')
    try {
      const updated = await ordersService.removeItem(selectedOrder.id, itemId)
      setSelectedOrder(updated)
      await fetchAll()
    } catch (err) {
      setError('Error al eliminar item')
    }
  }

  const handleCobrar = async (methodoPago) => {
    setError('')
    try {
      await ordersService.cobrar(selectedOrder.id, methodoPago)
      setShowOrderSheet(false)
      setSelectedOrder(null)
      setSelectedMesa(null)
      await fetchAll()
    } catch (err) {
      setError('Error al cobrar')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full" style={{ backgroundColor: GALIA.crema, color: GALIA.grisClaro }}>
        Cargando...
      </div>
    )
  }

  const activeSalonMesas = (activeSalon && allMesas[activeSalon]) || []
  const mesasWithOrders = activeSalonMesas.map(m => ({
    ...m,
    openOrder: openOrders.find(o => o.mesa_id === m.id) || null
  }))

  return (
    <div className="h-full w-full flex flex-col" style={{ backgroundColor: GALIA.crema }}>
      {/* Header */}
      <div className="h-14 flex items-center justify-between px-4 text-white font-semibold text-lg" style={{ backgroundColor: GALIA.marron }}>
        <span>Mi Turno - Camarero</span>
        {/* View mode toggle */}
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('map')}
            className="p-2 rounded transition"
            title="Vista Mapa"
            aria-label="Vista Mapa"
            aria-pressed={viewMode === 'map'}
            style={{
              backgroundColor: viewMode === 'map' ? GALIA.amarillo : 'transparent',
              color: viewMode === 'map' ? GALIA.marron : 'white'
            }}
          >
            <Map size={20} />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className="p-2 rounded transition"
            title="Vista Lista"
            aria-label="Vista Lista"
            aria-pressed={viewMode === 'list'}
            style={{
              backgroundColor: viewMode === 'list' ? GALIA.amarillo : 'transparent',
              color: viewMode === 'list' ? GALIA.marron : 'white'
            }}
          >
            <List size={20} />
          </button>
        </div>
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

      {/* Main content area */}
      <div className="flex-1 overflow-hidden">
        {viewMode === 'map' ? (
          <div className="h-full w-full p-2 md:p-4">
            <SalonFloorPlan
              mesas={mesasWithOrders}
              onMesaClick={handleMesaClick}
              isEditMode={false}
            />
          </div>
        ) : (
          <div className="h-full w-full">
            <CamareroTableListView
              mesas={mesasWithOrders}
              onMesaClick={handleMesaClick}
            />
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="p-3 text-sm" style={{ backgroundColor: '#fee', color: '#c33' }}>
          {error}
        </div>
      )}

      {/* Order Bottom Sheet */}
      {selectedOrder && (
        <CamareroOrderBottomSheet
          isOpen={showOrderSheet}
          order={selectedOrder}
          mesaNumber={selectedMesa?.numero || selectedMesa?.id || selectedOrder?.mesa_id}
          onClose={() => {
            setShowOrderSheet(false)
            setSelectedOrder(null)
            setSelectedMesa(null)
          }}
          onAddItem={handleAddItem}
          onRemoveItem={handleRemoveItem}
          onCobrar={handleCobrar}
        />
      )}
    </div>
  )
}

export default Camarero
