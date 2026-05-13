import { useState, useEffect } from 'react'
import { Settings2 } from 'lucide-react'
import salonsService from '../services/salonsService'
import salesService from '../services/salesService'
import ordersService from '../services/ordersService'
import PosModal from '../components/pos/PosModal'
import OrderDrawer from '../components/pos/OrderDrawer'
import AddItemModal from '../components/pos/AddItemModal'
import SalonFloorPlan from '../components/pos/SalonFloorPlan'

const Pos = () => {
  const [salons, setSalons] = useState([])
  const [activeSalon, setActiveSalon] = useState(null)
  const [allMesas, setAllMesas] = useState({})
  const [openOrders, setOpenOrders] = useState([])
  const [dailySummary, setDailySummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editMode, setEditMode] = useState(false)

  const [showPosModal, setShowPosModal] = useState(false)
  const [showAddItemModal, setShowAddItemModal] = useState(false)
  const [showDirectSale, setShowDirectSale] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [showOrderDrawer, setShowOrderDrawer] = useState(false)

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchAll = async () => {
    try {
      const [salonRes, ordersRes] = await Promise.all([
        salonsService.getSalons({ include_inactive: false }),
        ordersService.getOrders({ status: 'abierta' }),
      ])

      setSalons(salonRes.salons || [])
      setOpenOrders(ordersRes.orders || [])

      // Fetch mesas for all salons
      const mesasMap = {}
      for (const salon of salonRes.salons || []) {
        const mesasRes = await salonsService.getMesas(salon.id)
        mesasMap[salon.id] = mesasRes.mesas || []
      }
      setAllMesas(mesasMap)

      if (salonRes.salons && salonRes.salons.length > 0 && !activeSalon) {
        setActiveSalon(salonRes.salons[0].id)
      }

      await fetchDailySummary()
      setLoading(false)
    } catch (err) {
      setError('Error al cargar datos')
      setLoading(false)
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

  const handleMesaClick = async (mesa) => {
    if (mesa.status === 'libre') {
      // Create new order
      try {
        const order = await ordersService.createOrder({
          mesa_id: mesa.id,
          salon_id: activeSalon,
        })
        setSelectedOrder(order)
        setShowOrderDrawer(true)
        await fetchAll()
      } catch (err) {
        setError('Error al crear orden')
      }
    } else if (mesa.status === 'ocupada') {
      // Open existing order
      const order = openOrders.find((o) => o.mesa_id === mesa.id)
      if (order) {
        setSelectedOrder(order)
        setShowOrderDrawer(true)
      }
    }
  }

  const handleSale = async (saleData) => {
    try {
      await salesService.createSale(
        saleData.items,
        saleData.mesa_id,
        saleData.medio_pago
      )

      await fetchAll()

      setShowPosModal(false)
      setShowDirectSale(false)
      setError('')
    } catch (err) {
      setError(err.response?.data?.error || 'Error al registrar venta')
    }
  }

  const handleItemAdded = async () => {
    setShowAddItemModal(false)
    await fetchAll()
    // Re-fetch the current order to show updated items
    if (selectedOrder) {
      try {
        const updatedOrder = await ordersService.getOrder(selectedOrder.id)
        setSelectedOrder(updatedOrder)
      } catch (err) {
        console.error('Error fetching updated order:', err)
      }
    }
  }

  const handleMesaDrag = async (mesaId, x, y) => {
    if (!activeSalon) return
    try {
      const newMesas = [...(allMesas[activeSalon] || [])]
      const mesaIndex = newMesas.findIndex((m) => m.id === mesaId)
      if (mesaIndex >= 0) {
        const mesa = newMesas[mesaIndex]
        const newX = Math.max(0, Math.min(100 - mesa.width, x))
        const newY = Math.max(0, Math.min(100 - mesa.height, y))

        // Check for collisions with other mesas
        const hasCollision = newMesas.some((m, idx) => {
          if (idx === mesaIndex) return false
          const minDistance = 3 // % of floor plan
          return (
            Math.abs((newX + mesa.width / 2) - (m.pos_x + m.width / 2)) < minDistance &&
            Math.abs((newY + mesa.height / 2) - (m.pos_y + m.height / 2)) < minDistance
          )
        })

        if (hasCollision) {
          setError('Las mesas no pueden superponerse. Sepáralas más.')
          return
        }

        newMesas[mesaIndex] = {
          ...mesa,
          pos_x: newX,
          pos_y: newY,
        }
        await salonsService.updateMesa(activeSalon, mesaId, {
          pos_x: newX,
          pos_y: newY,
        })
        setAllMesas({
          ...allMesas,
          [activeSalon]: newMesas,
        })
        setError('')
      }
    } catch (err) {
      console.error('Error updating mesa position:', err)
    }
  }

  if (loading) {
    return <div className="p-6">Cargando POS...</div>
  }

  const currentSalon = salons.find((s) => s.id === activeSalon)
  const activeMesas = allMesas[activeSalon] || []
  const mesasWithOrders = activeMesas.map((m) => ({
    ...m,
    openOrder: openOrders.find((o) => o.mesa_id === m.id) || null,
    total: openOrders.find((o) => o.mesa_id === m.id)?.total || undefined,
  }))

  return (
    <div className="h-screen flex flex-col bg-slate-900 text-white">
      <div className="p-4 border-b border-slate-700">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold">🛒 Caja — {currentSalon?.name}</h1>
          <div className="flex gap-2 text-xs">
            <span className="text-green-400">● {activeMesas.filter((m) => m.status === 'libre').length} libres</span>
            <span className="text-red-400">● {activeMesas.filter((m) => m.status === 'ocupada').length} ocupadas</span>
            {activeMesas.filter((m) => m.status === 'reservada').length > 0 && (
              <span className="text-yellow-400">
                ● {activeMesas.filter((m) => m.status === 'reservada').length} reservadas
              </span>
            )}
          </div>
        </div>

        <div className="flex gap-2 overflow-x-auto mb-3">
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

        <button
          onClick={() => setShowDirectSale(true)}
          className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition text-sm font-medium"
        >
          💳 Venta Directa
        </button>
      </div>

      {error && (
        <div className="bg-red-900 border-b border-red-700 text-red-200 px-4 py-2">
          {error}
        </div>
      )}

      <div className="flex-1 relative overflow-hidden p-4">
        {activeSalon && (
          <SalonFloorPlan
            mesas={mesasWithOrders}
            onMesaClick={handleMesaClick}
            onMesaDrag={handleMesaDrag}
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
          mesaId={null}
          onClose={() => {
            setShowPosModal(false)
          }}
          onSale={handleSale}
        />
      )}

      {showDirectSale && (
        <PosModal
          mesaId={null}
          onClose={() => {
            setShowDirectSale(false)
          }}
          onSale={handleSale}
        />
      )}

      {showOrderDrawer && selectedOrder && (
        <OrderDrawer
          order={selectedOrder}
          onAddItem={() => setShowAddItemModal(true)}
          onClose={() => {
            setShowOrderDrawer(false)
            setSelectedOrder(null)
          }}
          onCobrar={async (medioPago) => {
            try {
              await ordersService.cobrar(selectedOrder.id, medioPago)
              await fetchAll()
              setShowOrderDrawer(false)
              setSelectedOrder(null)
              setError('')
            } catch (err) {
              setError(err.response?.data?.error || 'Error al cobrar orden')
            }
          }}
        />
      )}

      {showAddItemModal && selectedOrder && (
        <AddItemModal
          orderId={selectedOrder.id}
          onClose={() => setShowAddItemModal(false)}
          onItemAdded={handleItemAdded}
        />
      )}
    </div>
  )
}

export default Pos
