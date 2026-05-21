import { useState } from 'react'
import { X, Printer } from 'lucide-react'
import GALIA from '../../constants/colors'
import salePrinting from '../../services/salePrinting'

const OrderDrawer = ({ order, isOpen, onClose, onAddItem, onRemoveItem, onCobrar, onCancel }) => {
  const [printing, setPrinting] = useState(false)
  if (!isOpen || !order) return null

  const handlePrintControl = async () => {
    setPrinting(true)
    try {
      await salePrinting.printControl(order, order.items || [], order.total || 0, 0)
    } catch (err) {
      console.error('Error al imprimir control:', err)
    } finally {
      setPrinting(false)
    }
  }

  return (
    <div
      className="w-full flex flex-col lg:w-96 lg:border-l lg:flex-shrink-0 overflow-hidden"
      style={{ backgroundColor: GALIA.blanco, borderColor: GALIA.grisLigero }}
    >
      {/* Header */}
      <div className="px-3 md:px-6 py-3 md:py-4 flex items-center justify-between border-b" style={{ backgroundColor: GALIA.crema, borderColor: GALIA.grisLigero }}>
        <div className="min-w-0 flex-1">
          <h2 className="text-lg md:text-xl font-bold break-words" style={{ color: GALIA.marron }}>
            Orden #{order.id}
          </h2>
          <p className="text-xs" style={{ color: GALIA.grisClaro }}>
            {order.items?.length || 0} items
          </p>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-gray-200 rounded flex-shrink-0 ml-2" title="Cerrar">
          <X size={20} className="md:w-6 md:h-6" style={{ color: GALIA.marron }} />
        </button>
      </div>

      {/* Items List */}
      <div className="flex-1 overflow-y-auto px-3 md:px-4 py-2 md:py-3">
        {order.items && order.items.length > 0 ? (
          <div className="space-y-2 md:space-y-3">
            {order.items.map((item) => (
              <div
                key={item.id}
                className="rounded-lg p-3 md:p-4 border flex items-start justify-between hover:shadow-md transition-shadow"
                style={{ backgroundColor: GALIA.crema, borderColor: GALIA.grisLigero }}
              >
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-sm md:text-base" style={{ color: GALIA.marron }}>
                    {item.product_name}
                  </div>
                  <div className="text-xs md:text-sm mt-1" style={{ color: GALIA.grisClaro }}>
                    {item.variant_name && <div>{item.variant_name}</div>}
                    <div className="font-medium mt-1">
                      {item.quantity}x ${parseFloat(item.unit_price).toFixed(2)} = ${(item.unit_price * item.quantity).toFixed(2)}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => onRemoveItem(item.id)}
                  className="ml-2 md:ml-3 p-1 md:p-2 hover:bg-red-100 rounded transition-colors flex-shrink-0"
                  style={{ color: GALIA.grisClaro }}
                  title="Eliminar item"
                >
                  <X size={16} className="md:w-[18px] md:h-[18px]" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 md:py-12" style={{ color: GALIA.grisClaro }}>
            <p className="text-base md:text-lg font-medium">Sin items</p>
            <p className="text-xs md:text-sm">Haz click en "Agregar Item"</p>
          </div>
        )}
      </div>

      {/* Total Section */}
      <div
        className="border-t px-3 md:px-6 py-4 md:py-6"
        style={{ borderColor: GALIA.grisLigero, backgroundColor: GALIA.crema }}
      >
        <div className="text-center mb-3 md:mb-4">
          <p className="text-xs md:text-sm" style={{ color: GALIA.grisClaro }}>Total</p>
          <div className="text-2xl md:text-4xl font-bold" style={{ color: GALIA.amarillo }}>
            ${parseFloat(order.total || 0).toFixed(2)}
          </div>
        </div>

        {/* Buttons */}
        <div className="space-y-2">
          <button
            onClick={onAddItem}
            className="w-full py-2 rounded font-semibold transition-opacity duration-200 text-sm md:text-base"
            style={{ backgroundColor: GALIA.amarillo, color: GALIA.marron }}
            onMouseEnter={(e) => (e.target.style.opacity = '0.9')}
            onMouseLeave={(e) => (e.target.style.opacity = '1')}
          >
            Agregar Item
          </button>
          <button
            onClick={handlePrintControl}
            disabled={!order.items || order.items.length === 0 || printing}
            className="w-full py-2 rounded font-semibold transition-opacity duration-200 text-sm md:text-base flex items-center justify-center gap-2 disabled:opacity-50"
            style={{ backgroundColor: '#3B82F6', color: 'white' }}
            onMouseEnter={(e) => {
              if (!e.target.disabled) e.target.style.opacity = '0.9'
            }}
            onMouseLeave={(e) => {
              if (!e.target.disabled) e.target.style.opacity = '1'
            }}
            title="Imprimir control de mesa"
          >
            <Printer size={16} />
            {printing ? 'Imprimiendo...' : 'Control Mesa'}
          </button>
          <button
            onClick={onCobrar}
            disabled={!order.items || order.items.length === 0}
            className="w-full py-2 md:py-3 rounded font-bold text-base md:text-lg transition-opacity duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ backgroundColor: GALIA.marron, color: 'white' }}
            onMouseEnter={(e) => {
              if (!e.target.disabled) e.target.style.opacity = '0.9'
            }}
            onMouseLeave={(e) => {
              if (!e.target.disabled) e.target.style.opacity = '1'
            }}
          >
            COBRAR
          </button>
          {(!order.items || order.items.length === 0) && (
            <button
              onClick={onCancel}
              className="w-full py-2 rounded font-semibold text-sm md:text-base border-2 transition-opacity duration-200"
              style={{ borderColor: GALIA.grisLigero, color: GALIA.grisClaro }}
              onMouseEnter={(e) => (e.target.style.opacity = '0.7')}
              onMouseLeave={(e) => (e.target.style.opacity = '1')}
            >
              Cancelar Orden
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default OrderDrawer
