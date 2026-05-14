import { useState } from 'react'
import { X } from 'lucide-react'
import GALIA from '../../constants/colors'

const CobrarBottomSheet = ({ isOpen, orderId, total, onConfirm, onClose }) => {
  const [selectedMethod, setSelectedMethod] = useState(null)

  if (!isOpen) return null

  const handleConfirm = () => {
    if (selectedMethod) {
      onConfirm(selectedMethod)
      setSelectedMethod(null)
    }
  }

  const metodos = ['Efectivo', 'Tarjeta', 'Otro']

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />

      {/* Bottom Sheet */}
      <div
        className="fixed bottom-0 left-0 right-0 z-50 rounded-t-xl max-h-[60vh] flex flex-col"
        style={{ backgroundColor: GALIA.blanco }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-4 py-3"
          style={{ backgroundColor: GALIA.marron }}
        >
          <h2 className="text-white text-lg font-semibold">Método de Pago</h2>
          <button onClick={onClose} className="p-1">
            <X size={20} color="white" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {/* Total Display */}
          <div className="mb-4">
            <p className="text-sm" style={{ color: GALIA.grisClaro }}>
              Total a pagar:
            </p>
            <p className="text-3xl font-bold" style={{ color: GALIA.amarillo }}>
              ${total.toFixed(2)}
            </p>
          </div>

          {/* Method Selection */}
          <div className="grid grid-cols-3 gap-2">
            {metodos.map((metodo) => (
              <button
                key={metodo}
                onClick={() => setSelectedMethod(metodo)}
                className="py-3 rounded border-2 font-semibold transition-colors duration-200"
                style={{
                  borderColor:
                    selectedMethod === metodo ? GALIA.amarillo : GALIA.grisLigero,
                  backgroundColor:
                    selectedMethod === metodo ? GALIA.amarillo : 'transparent',
                  color:
                    selectedMethod === metodo ? GALIA.marron : GALIA.marron,
                }}
              >
                {metodo}
              </button>
            ))}
          </div>
        </div>

        {/* Confirm Button */}
        <div className="px-4 py-4 border-t" style={{ borderColor: GALIA.grisLigero }}>
          <button
            onClick={handleConfirm}
            disabled={!selectedMethod}
            className="w-full py-3 rounded font-bold text-lg transition-opacity duration-200"
            style={{
              backgroundColor: selectedMethod ? GALIA.marron : GALIA.grisLigero,
              color: 'white',
              opacity: selectedMethod ? 1 : 0.6,
              cursor: selectedMethod ? 'pointer' : 'not-allowed',
            }}
          >
            Confirmar
          </button>
        </div>
      </div>
    </>
  )
}

export default CobrarBottomSheet
