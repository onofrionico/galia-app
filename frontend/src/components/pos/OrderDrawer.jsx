import { X, Plus } from 'lucide-react'

const OrderDrawer = ({ mesa, saleData, onAddItem, onClose, onCobrar }) => {
  const total = saleData?.items?.reduce((sum, item) => sum + item.subtotal, 0) || 0
  const duration = saleData?.duration || '0 min'

  return (
    <div className="fixed right-0 top-0 bottom-0 w-96 bg-white shadow-xl z-40 flex flex-col">
      <div className="border-b p-4 flex justify-between items-center">
        <h3 className="text-lg font-bold">Mesa {mesa.number}</h3>
        <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
          <X size={20} />
        </button>
      </div>

      <div className="text-xs text-gray-600 px-4 pt-3">
        Abierta hace {duration}
      </div>

      <div className="flex-1 overflow-y-auto p-4 border-b">
        {!saleData?.items || saleData.items.length === 0 ? (
          <div className="text-center text-gray-500 py-8">Sin items</div>
        ) : (
          <div className="space-y-2">
            {saleData.items.map((item, idx) => (
              <div
                key={idx}
                className="bg-gray-50 rounded p-2 border border-gray-200"
              >
                <div className="flex justify-between">
                  <div>
                    <div className="text-sm font-medium">{item.product_name}</div>
                    <div className="text-xs text-gray-600">
                      {item.variant_name}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">
                      ${item.subtotal.toFixed(2)}
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
        <button
          onClick={onCobrar}
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
      </div>
    </div>
  )
}

export default OrderDrawer
