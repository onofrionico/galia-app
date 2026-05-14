import { X } from 'lucide-react'
import GALIA from '../../constants/colors'

const OrderDrawer = ({ order, isOpen, onClose, onAddItem, onRemoveItem, onCobrar }) => {
  if (!isOpen || !order) return null

  return (
    <div
      className="w-96 flex flex-col border-l lg:w-[450px]"
      style={{ backgroundColor: GALIA.blanco, borderColor: GALIA.grisLigero }}
    >
      {/* Header */}
      <div className="px-6 py-4 flex items-center justify-between border-b" style={{ backgroundColor: GALIA.crema, borderColor: GALIA.grisLigero }}>
        <div>
          <h2 className="text-xl font-bold" style={{ color: GALIA.marron }}>
            Orden #{order.id}
          </h2>
          <p className="text-xs" style={{ color: GALIA.grisClaro }}>
            {order.items?.length || 0} items
          </p>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-gray-200 rounded" title="Cerrar">
          <X size={24} style={{ color: GALIA.marron }} />
        </button>
      </div>

      {/* Items List */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        {order.items && order.items.length > 0 ? (
          <div className="space-y-3">
            {order.items.map((item) => (
              <div
                key={item.id}
                className="rounded-lg p-4 border flex items-start justify-between hover:shadow-md transition-shadow"
                style={{ backgroundColor: GALIA.crema, borderColor: GALIA.grisLigero }}
              >
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-base" style={{ color: GALIA.marron }}>
                    {item.product_name}
                  </div>
                  <div className="text-sm mt-1" style={{ color: GALIA.grisClaro }}>
                    {item.variant_name && <div>{item.variant_name}</div>}
                    <div className="font-medium mt-1">
                      {item.quantity}x ${parseFloat(item.unit_price).toFixed(2)} = ${(item.unit_price * item.quantity).toFixed(2)}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => onRemoveItem(item.id)}
                  className="ml-3 p-2 hover:bg-red-100 rounded transition-colors flex-shrink-0"
                  style={{ color: GALIA.grisClaro }}
                  title="Eliminar item"
                >
                  <X size={18} />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12" style={{ color: GALIA.grisClaro }}>
            <p className="text-lg font-medium">Sin items</p>
            <p className="text-sm">Haz click en "Agregar Item"</p>
          </div>
        )}
      </div>

      {/* Total Section */}
      <div
        className="border-t px-6 py-6"
        style={{ borderColor: GALIA.grisLigero, backgroundColor: GALIA.crema }}
      >
        <div className="text-center mb-4">
          <p className="text-sm" style={{ color: GALIA.grisClaro }}>Total</p>
          <div className="text-4xl font-bold" style={{ color: GALIA.amarillo }}>
            ${parseFloat(order.total || 0).toFixed(2)}
          </div>
        </div>

        {/* Buttons */}
        <div className="space-y-2">
          <button
            onClick={onAddItem}
            className="w-full py-2 rounded font-semibold transition-opacity duration-200"
            style={{ backgroundColor: GALIA.amarillo, color: GALIA.marron }}
            onMouseEnter={(e) => (e.target.style.opacity = '0.9')}
            onMouseLeave={(e) => (e.target.style.opacity = '1')}
          >
            Agregar Item
          </button>
          <button
            onClick={onCobrar}
            className="w-full py-3 rounded font-bold text-lg transition-opacity duration-200"
            style={{ backgroundColor: GALIA.marron, color: 'white' }}
            onMouseEnter={(e) => (e.target.style.opacity = '0.9')}
            onMouseLeave={(e) => (e.target.style.opacity = '1')}
          >
            COBRAR
          </button>
        </div>
      </div>
    </div>
  )
}

export default OrderDrawer
