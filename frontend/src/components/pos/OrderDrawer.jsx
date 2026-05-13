import { useState, useEffect } from 'react'
import { X, Plus } from 'lucide-react'

const OrderDrawer = ({ order, onAddItem, onClose, onCobrar }) => {
  const [showPaymentOptions, setShowPaymentOptions] = useState(false)
  const total = order?.total || 0
  const mesa = order?.mesa_id

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    document.addEventListener('keydown', handleEsc)
    return () => document.removeEventListener('keydown', handleEsc)
  }, [onClose])

  const handlePayment = (medioPago) => {
    onCobrar(medioPago)
    setShowPaymentOptions(false)
  }

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-30 z-30" onClick={onClose} />
      <div className="fixed right-0 top-0 bottom-0 w-96 bg-white shadow-xl z-40 flex flex-col">
        <div className="border-b p-4 flex justify-between items-center bg-gray-50">
          <h3 className="text-lg font-bold">Mesa {mesa}</h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-200 rounded transition" title="Cerrar (ESC)">
            <X size={20} />
          </button>
        </div>

      <div className="text-xs text-gray-600 px-4 pt-3">
        Orden #{order?.id || 'N/A'}
      </div>

      <div className="flex-1 overflow-y-auto p-4 border-b">
        {!order?.items || order.items.length === 0 ? (
          <div className="text-center text-gray-500 py-8">Sin items</div>
        ) : (
          <div className="space-y-2">
            {order.items.map((item) => (
              <div
                key={item.id}
                className="bg-gray-50 rounded p-2 border border-gray-200"
              >
                <div className="flex justify-between">
                  <div>
                    <div className="text-sm font-medium">
                      {item.product_variant?.product?.name || 'Producto'}
                    </div>
                    <div className="text-xs text-gray-600">
                      {item.product_variant?.name || 'Variante'}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">
                      ${(item.unit_price * item.quantity).toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-600">x{item.quantity}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="p-4 border-b">
        <div className="flex justify-between items-center font-bold text-lg mb-3">
          <span>Total:</span>
          <span className="text-green-600">${total.toFixed(2)}</span>
        </div>
        <button
          onClick={onAddItem}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 text-sm font-medium mb-2"
        >
          <Plus size={16} className="inline mr-1" /> Agregar Ítem
        </button>
      </div>

      <div className="p-4 space-y-2">
        {showPaymentOptions ? (
          <div className="space-y-2 mb-2">
            <p className="text-sm font-medium text-gray-700">Selecciona medio de pago:</p>
            {['Efectivo', 'Débito', 'QR'].map((option) => (
              <button
                key={option}
                onClick={() => handlePayment(option)}
                className="w-full bg-gray-100 text-gray-800 py-2 rounded hover:bg-gray-200 text-sm font-medium"
              >
                {option}
              </button>
            ))}
            <button
              onClick={() => setShowPaymentOptions(false)}
              className="w-full border border-gray-300 py-2 rounded hover:bg-gray-50 text-sm font-medium"
            >
              Cancelar
            </button>
          </div>
        ) : (
          <>
            <button
              onClick={() => setShowPaymentOptions(true)}
              className="w-full bg-green-600 text-white font-bold py-3 rounded hover:bg-green-700 text-lg"
            >
              COBRAR
            </button>
            <button
              onClick={onClose}
              className="w-full border-2 border-gray-300 py-2 rounded hover:bg-gray-50 text-sm font-medium"
            >
              Cerrar Drawer
            </button>
          </>
        )}
      </div>
      </div>
    </>
  )
}

export default OrderDrawer
