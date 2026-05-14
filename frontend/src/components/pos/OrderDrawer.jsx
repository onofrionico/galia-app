import { X } from 'lucide-react'
import GALIA from '../../constants/colors'

const OrderDrawer = ({ order, isOpen, onClose, onAddItem, onRemoveItem, onCobrar }) => {
  if (!isOpen || !order) return null

  return (
    <div
      className="fixed right-0 top-0 h-full w-80 flex flex-col shadow-lg z-50"
      style={{ backgroundColor: GALIA.blanco, borderLeft: `4px solid ${GALIA.amarillo}` }}
    >
      {/* Header */}
      <div className="px-4 py-3 flex items-center justify-between" style={{ backgroundColor: GALIA.crema }}>
        <h2 className="text-lg font-semibold" style={{ color: GALIA.marron }}>
          Orden #{order.id}
        </h2>
        <button onClick={onClose} className="p-1">
          <X size={20} style={{ color: GALIA.marron }} />
        </button>
      </div>

      {/* Items List */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {order.items && order.items.length > 0 ? (
          order.items.map((item) => (
            <div
              key={item.id}
              className="rounded px-3 py-2 flex items-center justify-between"
              style={{ backgroundColor: GALIA.crema }}
            >
              <div className="flex-1">
                <div className="text-sm font-medium" style={{ color: GALIA.marron }}>
                  {item.product_name}
                </div>
                <div className="text-xs" style={{ color: GALIA.grisClaro }}>
                  x{item.quantity}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold" style={{ color: GALIA.marron }}>
                  ${(item.unit_price * item.quantity).toFixed(2)}
                </span>
                <button
                  onClick={() => onRemoveItem(item.id)}
                  className="p-1"
                  style={{ color: GALIA.grisClaro }}
                  onMouseEnter={(e) => (e.target.style.color = '#ef4444')}
                  onMouseLeave={(e) => (e.target.style.color = GALIA.grisClaro)}
                >
                  ×
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8" style={{ color: GALIA.grisClaro }}>
            Sin items
          </div>
        )}
      </div>

      {/* Total Section */}
      <div
        className="border-t px-4 py-4"
        style={{ borderColor: GALIA.grisLigero }}
      >
        <div className="text-2xl font-bold mb-4" style={{ color: GALIA.amarillo }}>
          ${parseFloat(order.total || 0).toFixed(2)}
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
