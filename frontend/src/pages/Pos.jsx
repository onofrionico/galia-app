import { useState, useEffect } from 'react'
import salonsService from '../services/salonsService'
import ordersService from '../services/ordersService'
import salesService from '../services/salesService'
import { useNotification } from '../context/NotificationContext'
import PosHeader from '../components/pos/PosHeader'
import PosMain from '../components/pos/PosMain'
import OrderDrawer from '../components/pos/OrderDrawer'
import CobrarBottomSheet from '../components/pos/CobrarBottomSheet'
import AddItemModal from '../components/pos/AddItemModal'
import SalePanel from '../components/pos/SalePanel'
import OpenSaleModal from '../components/pos/OpenSaleModal'
import SalonFloorPlan from '../components/pos/SalonFloorPlan'

const Pos = () => {
  const { addNotification } = useNotification()
  const [salons, setSalons] = useState([])
  const [activeSalon, setActiveSalon] = useState(null)
  const [allMesas, setAllMesas] = useState({})
  const [openOrders, setOpenOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [selectedOrder, setSelectedOrder] = useState(null)
  const [selectedSale, setSelectedSale] = useState(null)
  const [showOrderDrawer, setShowOrderDrawer] = useState(false)
  const [showSalePanel, setShowSalePanel] = useState(false)
  const [showOpenSaleModal, setShowOpenSaleModal] = useState(false)
  const [showAddItemModal, setShowAddItemModal] = useState(false)
  const [showCobrarSheet, setShowCobrarSheet] = useState(false)
  const [posMode, setPosMode] = useState('Mesas')
  const [isEditMode, setIsEditMode] = useState(false)
  const [selectedMesa, setSelectedMesa] = useState(null)

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
    setSelectedMesa(mesa)
    if (mesa.status === 'libre') {
      // Show modal to create new sale
      setShowOpenSaleModal(true)
    } else if (mesa.status === 'ocupada' && mesa.openOrder) {
      // Open existing order/sale
      try {
        const sale = await salesService.getSale(mesa.openOrder.id)
        setSelectedSale(sale)
        setShowSalePanel(true)
      } catch (err) {
        // Fallback to order drawer if sale endpoint fails
        setSelectedOrder(mesa.openOrder)
        setShowOrderDrawer(true)
      }
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
      // Show notification for comanda printed
      const mesaNumber = selectedMesa?.numero || selectedMesa?.id
      addNotification(`Nueva comanda en Mesa ${mesaNumber}`, 'success')
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
      // Get mesa info for notification
      const mesa = activeSalonMesas.find((m) => m.id === selectedOrder.mesa_id)
      const mesaNumber = mesa?.numero || selectedOrder.mesa_id
      const total = selectedOrder.total || 0
      addNotification(
        `Venta cerrada - Mesa ${mesaNumber} - $${parseFloat(total).toFixed(2)}`,
        'info'
      )
      setSelectedOrder(null)
      await fetchAll()
    } catch (err) {
      setError('Error al cobrar')
    }
  }

  const handleMesaDrag = async (mesaId, x, y) => {
    try {
      console.log(`Moviendo mesa ${mesaId} a (${x.toFixed(1)}%, ${y.toFixed(1)}%)`)
      await salonsService.updateMesa(activeSalon, mesaId, { pos_x: x, pos_y: y })
      console.log(`Mesa movida exitosamente`)
      await fetchAll()
    } catch (err) {
      console.error('Error al mover mesa:', err)
      setError('Error al mover mesa: ' + (err.response?.data?.error || err.message))
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
        isEditMode={isEditMode}
        onEditModeToggle={() => setIsEditMode(!isEditMode)}
      />

      {/* Main layout - responsive: stack on mobile/tablet, side-by-side on large desktop */}
      <div className="flex flex-1 overflow-hidden flex-col lg:flex-row">
        {/* Floor plan - full width on mobile/tablet, flex-1 on large desktop */}
        <div className="flex-1 flex flex-col min-h-0 w-full">
          {isEditMode && (
            <div className="bg-blue-50 border-b p-3 text-sm text-blue-900">
              Arrastra las mesas para reorganizar. Las posiciones se guardan automáticamente.
            </div>
          )}
          <div className="flex-1 overflow-auto p-2 md:p-4 w-full" style={{ backgroundColor: isEditMode ? '#f3f4f6' : '#fafafa' }}>
            <div style={{ height: '100%', width: '100%' }}>
              <SalonFloorPlan
                mesas={activeSalonMesas}
                onMesaClick={handleMesaClick}
                isEditMode={isEditMode}
                onMesaDrag={handleMesaDrag}
              />
            </div>
          </div>
        </div>

        {/* Sale panel - hidden on mobile/tablet, visible on large desktop (lg+) */}
        {showSalePanel && !isEditMode && (
          <div className="hidden lg:flex flex-shrink-0">
            <SalePanel
              sale={selectedSale}
              isOpen={showSalePanel}
              onClose={() => {
                setShowSalePanel(false)
                setSelectedSale(null)
                fetchAll()
              }}
              onSaleUpdated={(updatedSale) => {
                setSelectedSale(updatedSale)
                fetchAll()
              }}
              onSaleClosed={(sale) => {
                const mesaNumber = sale.mesa_id || 'desconocida'
                const total = sale.total || 0
                addNotification(
                  `Venta cerrada - Mesa ${mesaNumber} - $${parseFloat(total).toFixed(2)}`,
                  'info'
                )
              }}
              onItemAdded={(mesaNumber) => {
                addNotification(`Nueva comanda en Mesa ${mesaNumber}`, 'success')
              }}
            />
          </div>
        )}

        {/* Sale panel modal for mobile/tablet */}
        {showSalePanel && !isEditMode && (
          <div className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40 flex items-end">
            <div className="w-screen bg-white rounded-t-lg max-h-[90vh] overflow-y-auto flex flex-col">
              <SalePanel
                sale={selectedSale}
                isOpen={showSalePanel}
                onClose={() => {
                  setShowSalePanel(false)
                  setSelectedSale(null)
                  fetchAll()
                }}
                onSaleUpdated={(updatedSale) => {
                  setSelectedSale(updatedSale)
                  fetchAll()
                }}
                onSaleClosed={(sale) => {
                  const mesaNumber = sale.mesa_id || 'desconocida'
                  const total = sale.total || 0
                  addNotification(
                    `Venta cerrada - Mesa ${mesaNumber} - $${parseFloat(total).toFixed(2)}`,
                    'info'
                  )
                }}
                onItemAdded={(mesaNumber) => {
                  addNotification(`Nueva comanda en Mesa ${mesaNumber}`, 'success')
                }}
              />
            </div>
          </div>
        )}

        {showOrderDrawer && !isEditMode && (
          <OrderDrawer
            order={selectedOrder}
            isOpen={showOrderDrawer}
            onClose={() => setShowOrderDrawer(false)}
            onAddItem={() => setShowAddItemModal(true)}
            onRemoveItem={handleRemoveItem}
            onCobrar={() => setShowCobrarSheet(true)}
          />
        )}
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
        orderId={selectedOrder?.id}
        onClose={() => setShowAddItemModal(false)}
        onItemAdded={(updatedOrder) => {
          setSelectedOrder(updatedOrder)
          setShowAddItemModal(false)
          fetchAll()
        }}
      />

      <OpenSaleModal
        isOpen={showOpenSaleModal}
        mesaId={selectedMesa?.id}
        mesaNumber={selectedMesa?.numero || `Mesa ${selectedMesa?.id}`}
        onClose={() => {
          setShowOpenSaleModal(false)
          setSelectedMesa(null)
        }}
        onSaleCreated={(newSale) => {
          setSelectedSale(newSale)
          setShowOpenSaleModal(false)
          setShowSalePanel(true)
          fetchAll()
        }}
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
