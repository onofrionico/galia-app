import { useEffect } from 'react'
import { X, Trash2, Printer } from 'lucide-react'
import { useState } from 'react'
import GALIA from '../../constants/colors'
import salePrinting from '../../services/salePrinting'

const CamareroOrderBottomSheet = ({
  isOpen,
  order,
  mesaNumber,
  onClose,
  onAddItem,
  onRemoveItem,
  onCobrar,
  onCancel
}) => {
  const [printing, setPrinting] = useState(false)

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) onClose()
    }
    if (isOpen) {
      window.addEventListener('keydown', handleEscape)
      return () => window.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, onClose])

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
      className="fixed inset-0 bg-black bg-opacity-50 z-40 flex items-end"
      onClick={onClose}
    >
      <div
        className="w-screen bg-white rounded-t-2xl flex flex-col shadow-xl"
        style={{ maxHeight: '80vh' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-4 py-3 rounded-t-2xl"
          style={{ backgroundColor: GALIA.marron }}
        >
          <div className="flex items-center gap-2">
            <button onClick={onClose} className="text-white hover:opacity-80">
              <X size={20} />
            </button>
            <h2 className="text-white text-lg font-semibold">
              Mesa {mesaNumber}
            </h2>
          </div>
          <div className="text-right">
            <div className="text-xs text-white opacity-70">Total</div>
            <div className="text-xl font-bold" style={{ color: GALIA.amarillo }}>
              ${parseFloat(order.total || 0).toFixed(2)}
            </div>
          </div>
        </div>

        {/* Items list - scrollable */}
        <div className="flex-1 overflow-y-auto px-4 py-3">
          {order.items && order.items.length > 0 ? (
            <div className="space-y-2">
              {order.items.map(item => (
                <div
                  key={item.id}
                  className="flex justify-between items-center py-2 border-b"
                  style={{ borderColor: GALIA.grisLigero }}
                >
                  <div className="flex-1">
                    <div className="text-sm font-semibold" style={{ color: GALIA.marron }}>
                      {item.product_name}
                    </div>
                    {item.variant_name && (
                      <div className="text-xs" style={{ color: GALIA.grisClaro }}>
                        {item.variant_name}
                      </div>
                    )}
                    <div className="text-xs font-medium mt-0.5" style={{ color: GALIA.grisClaro }}>
                      {item.quantity}x ${parseFloat(item.unit_price).toFixed(2)} = ${(item.quantity * item.unit_price).toFixed(2)}
                    </div>
                  </div>
                  <button
                    onClick={() => onRemoveItem(item.id)}
                    className="ml-3 p-1 rounded hover:bg-red-50 transition-colors"
                    style={{ color: '#dc2626' }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-10" style={{ color: GALIA.grisClaro }}>
              <p className="font-medium">Sin items</p>
              <p className="text-sm">Agrega productos a la orden</p>
            </div>
          )}
        </div>

        {/* Action buttons - always visible */}
        <div className="px-4 py-4 space-y-2 border-t" style={{ borderColor: GALIA.grisLigero }}>
          <button
            onClick={onAddItem}
            className="w-full py-3 rounded-lg font-semibold text-sm transition hover:opacity-90"
            style={{ backgroundColor: GALIA.amarillo, color: GALIA.marron }}
          >
            Agregar Item
          </button>
          <div className="flex gap-2">
            <button
              onClick={handlePrintControl}
              disabled={!order.items?.length || printing}
              className="flex-1 py-2.5 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 transition hover:opacity-90 disabled:opacity-40"
              style={{ backgroundColor: '#3B82F6', color: 'white' }}
            >
              <Printer size={16} />
              {printing ? 'Imprimiendo...' : 'Control Mesa'}
            </button>
            <button
              onClick={onCobrar}
              disabled={!order.items?.length}
              className="flex-1 py-2.5 rounded-lg font-bold text-sm transition hover:opacity-90 disabled:opacity-40"
              style={{ backgroundColor: GALIA.marron, color: 'white' }}
            >
              COBRAR
            </button>
          </div>
          {!order.items?.length && onCancel && (
            <button
              onClick={onCancel}
              className="w-full py-2.5 rounded-lg font-semibold text-sm border-2 transition hover:bg-gray-50"
              style={{ borderColor: GALIA.grisLigero, color: GALIA.grisClaro }}
            >
              Cancelar Orden
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default CamareroOrderBottomSheet
