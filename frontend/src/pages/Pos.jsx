import { useState, useEffect } from 'react'
import salonsService from '../services/salonsService'
import ordersService from '../services/ordersService'
import salesService from '../services/salesService'
import PosHeader from '../components/pos/PosHeader'
import PosMain from '../components/pos/PosMain'
import OrderDrawer from '../components/pos/OrderDrawer'
import CobrarBottomSheet from '../components/pos/CobrarBottomSheet'
import AddItemModal from '../components/pos/AddItemModal'

const Pos = () => {
  const [salons, setSalons] = useState([])
  const [activeSalon, setActiveSalon] = useState(null)
  const [allMesas, setAllMesas] = useState({})
  const [openOrders, setOpenOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [selectedOrder, setSelectedOrder] = useState(null)
  const [showOrderDrawer, setShowOrderDrawer] = useState(false)
  const [showAddItemModal, setShowAddItemModal] = useState(false)
  const [showCobrarSheet, setShowCobrarSheet] = useState(false)
  const [posMode, setPosMode] = useState('Mesas')

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
        const mesasWithOrders = (mesasRes.mesas || []).map((mesa) => ({
          ...mesa,
          openOrder: (ordersRes.orders || []).find((o) => o.mesa_id === mesa.id),
        }))
        mesasMap[salon.id] = mesasWithOrders
      }
      setAllMesas(mesasMap)

      if (salonRes.salons && salonRes.salons.length > 0 && !activeSalon) {
        setActiveSalon(salonRes.salons[0].id)
      }

      setLoading(false)
    } catch (err) {
      setError('Error al cargar datos')
      setLoading(false)
    }
  }

  const handleMesaClick = async (mesa) => {
    if (mesa.status === 'libre') {
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
    } else if (mesa.status === 'ocupada' && mesa.openOrder) {
      setSelectedOrder(mesa.openOrder)
      setShowOrderDrawer(true)
    }
  }

  const handleAddItem = async (productVariantId, quantity) => {
    try {
      await ordersService.addItem(selectedOrder.id, {
        product_variant_id: productVariantId,
        quantity,
      })
      const updated = await ordersService.getOrder(selectedOrder.id)
      setSelectedOrder(updated)
      await fetchAll()
    } catch (err) {
      setError('Error al agregar item')
    }
  }

  const handleRemoveItem = async (itemId) => {
    try {
      await ordersService.removeItem(selectedOrder.id, itemId)
      const updated = await ordersService.getOrder(selectedOrder.id)
      setSelectedOrder(updated)
      await fetchAll()
    } catch (err) {
      setError('Error al eliminar item')
    }
  }

  const handleCobrar = async (metodo_pago) => {
    try {
      await ordersService.cobrar(selectedOrder.id, { metodo_pago })
      setShowCobrarSheet(false)
      setShowOrderDrawer(false)
      setSelectedOrder(null)
      await fetchAll()
    } catch (err) {
      setError('Error al cobrar')
    }
  }

  if (loading) {
    return <div className="p-6">Cargando...</div>
  }

  const activeSalonMesas = allMesas[activeSalon] || []

  return (
    <div className="h-full flex flex-col">
      <PosHeader
        activeMode={posMode}
        onModeChange={setPosMode}
      />

      <div className="flex flex-1 overflow-hidden">
        <PosMain
          salons={salons}
          mesas={allMesas}
          onMesaClick={handleMesaClick}
          activeSalonMesas={activeSalonMesas}
          activeSalon={activeSalon}
          onSalonChange={setActiveSalon}
        />

        <OrderDrawer
          order={selectedOrder}
          isOpen={showOrderDrawer}
          onClose={() => setShowOrderDrawer(false)}
          onAddItem={() => setShowAddItemModal(true)}
          onRemoveItem={handleRemoveItem}
          onCobrar={() => setShowCobrarSheet(true)}
        />
      </div>

      <CobrarBottomSheet
        isOpen={showCobrarSheet}
        orderId={selectedOrder?.id}
        total={selectedOrder?.total || 0}
        onConfirm={handleCobrar}
        onClose={() => setShowCobrarSheet(false)}
      />

      <AddItemModal
        isOpen={showAddItemModal}
        onClose={() => setShowAddItemModal(false)}
        onAddItem={handleAddItem}
      />

      {error && (
        <div className="fixed bottom-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded">
          {error}
        </div>
      )}
    </div>
  )
}

export default Pos
