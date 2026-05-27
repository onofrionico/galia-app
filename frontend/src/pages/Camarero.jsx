import { useState, useEffect, useCallback } from 'react'
import { Map, List } from 'lucide-react'
import salonsService from '../services/salonsService'
import ordersService from '../services/ordersService'
import GALIA from '../constants/colors'
import SalonFloorPlan from '../components/pos/SalonFloorPlan'
import CamareroTableListView from '../components/camarero/CamareroTableListView'
import CamareroOrderBottomSheet from '../components/camarero/CamareroOrderBottomSheet'
import OpenSaleModal from '../components/pos/OpenSaleModal'
import AddItemModal from '../components/pos/AddItemModal'
import CobrarBottomSheet from '../components/pos/CobrarBottomSheet'

const Camarero = () => {
  const [viewMode, setViewMode] = useState('map')
  const [salons, setSalons] = useState([])
  const [activeSalon, setActiveSalon] = useState(null)
  const [allMesas, setAllMesas] = useState({})
  const [openOrders, setOpenOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [selectedMesa, setSelectedMesa] = useState(null)
  const [selectedOrder, setSelectedOrder] = useState(null)

  // Modal/sheet visibility
  const [showOpenSaleModal, setShowOpenSaleModal] = useState(false)
  const [showOrderSheet, setShowOrderSheet] = useState(false)
  const [showAddItemModal, setShowAddItemModal] = useState(false)
  const [showCobrarSheet, setShowCobrarSheet] = useState(false)

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

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, 10000)
    return () => clearInterval(interval)
  }, [fetchAll])

  const handleMesaClick = async (mesa) => {
    setSelectedMesa(mesa)
    setError('')
    if (mesa.status === 'libre') {
      setShowOpenSaleModal(true)
    } else if (mesa.status === 'ocupada') {
      const order = openOrders.find(o => o.mesa_id === mesa.id)
      if (order) {
        try {
          const fullOrder = await ordersService.getOrder(order.id)
          setSelectedOrder(fullOrder)
          setShowOrderSheet(true)
        } catch (err) {
          setError('Error al cargar la orden')
        }
      }
    }
  }

  const handleOrderCreated = (order) => {
    setSelectedOrder(order)
    setShowOpenSaleModal(false)
    setShowOrderSheet(true)
  }

  const handleRemoveItem = async (itemId) => {
    try {
      const updated = await ordersService.removeItem(selectedOrder.id, itemId)
      setSelectedOrder(updated)
      await fetchAll()
    } catch (err) {
      setError('Error al eliminar item')
    }
  }

  const handleCobrar = async (metodoPago) => {
    try {
      await ordersService.cobrar(selectedOrder.id, metodoPago)
      setShowCobrarSheet(false)
      setShowOrderSheet(false)
      setSelectedOrder(null)
      setSelectedMesa(null)
      await fetchAll()
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cobrar')
    }
  }

  const handleCancelOrder = async () => {
    try {
      await ordersService.cancelOrder(selectedOrder.id)
      setShowOrderSheet(false)
      setSelectedOrder(null)
      setSelectedMesa(null)
      await fetchAll()
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cancelar la orden')
    }
  }

  const handleCloseOrderSheet = () => {
    setShowOrderSheet(false)
    setSelectedOrder(null)
    setSelectedMesa(null)
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
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('map')}
            title="Vista Mapa"
            className="p-2 rounded transition"
            style={{ backgroundColor: viewMode === 'map' ? GALIA.amarillo : 'transparent', color: viewMode === 'map' ? GALIA.marron : 'white' }}
          >
            <Map size={20} />
          </button>
          <button
            onClick={() => setViewMode('list')}
            title="Vista Lista"
            className="p-2 rounded transition"
            style={{ backgroundColor: viewMode === 'list' ? GALIA.amarillo : 'transparent', color: viewMode === 'list' ? GALIA.marron : 'white' }}
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

      {/* Main content */}
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

      {error && (
        <div className="p-3 text-sm" style={{ backgroundColor: '#fee', color: '#c33' }}>
          {error}
        </div>
      )}

      {/* Modal: Nueva venta (mesa libre) */}
      <OpenSaleModal
        isOpen={showOpenSaleModal}
        mesaId={selectedMesa?.id}
        mesaNumber={selectedMesa?.numero || `Mesa ${selectedMesa?.id}`}
        onClose={() => { setShowOpenSaleModal(false); setSelectedMesa(null) }}
        onSaleCreated={handleOrderCreated}
      />

      {/* BottomSheet: Orden de la mesa */}
      {selectedOrder && (
        <CamareroOrderBottomSheet
          isOpen={showOrderSheet}
          order={selectedOrder}
          mesaNumber={selectedMesa?.numero || selectedOrder?.mesa_id}
          onClose={handleCloseOrderSheet}
          onAddItem={() => setShowAddItemModal(true)}
          onRemoveItem={handleRemoveItem}
          onCobrar={() => setShowCobrarSheet(true)}
          onCancel={handleCancelOrder}
        />
      )}

      {/* Modal: Agregar item */}
      <AddItemModal
        isOpen={showAddItemModal}
        orderId={selectedOrder?.id}
        onClose={() => setShowAddItemModal(false)}
        onItemAdded={(updatedOrder) => {
          setSelectedOrder(updatedOrder)
          setShowAddItemModal(false)
          fetchAll()
        }}
      />

      {/* BottomSheet: Cobrar */}
      <CobrarBottomSheet
        isOpen={showCobrarSheet}
        orderId={selectedOrder?.id}
        order={selectedOrder}
        total={selectedOrder?.total || 0}
        onConfirm={handleCobrar}
        onClose={() => setShowCobrarSheet(false)}
      />
    </div>
  )
}

export default Camarero
