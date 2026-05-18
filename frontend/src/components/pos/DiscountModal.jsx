import { useState } from 'react'
import { X } from 'lucide-react'
import GALIA from '../../constants/colors'

const DiscountModal = ({ isOpen, total, currentDiscount, onApply, onClose }) => {
  if (!isOpen) return null

  const [discountType, setDiscountType] = useState('porcentaje')
  const [discountValue, setDiscountValue] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const calculateDiscountAmount = () => {
    if (!discountValue) return 0

    const value = parseFloat(discountValue)
    if (isNaN(value) || value < 0) return 0

    if (discountType === 'porcentaje') {
      // Percentage discount
      return (total * value) / 100
    } else {
      // Fixed amount discount
      return Math.min(value, total) // Don't allow discount greater than total
    }
  }

  const discountAmount = calculateDiscountAmount()
  const finalTotal = Math.max(0, total - discountAmount)

  const handleApply = async () => {
    if (!discountValue || parseFloat(discountValue) <= 0) {
      setError('Ingresa un valor de descuento válido')
      return
    }

    const value = parseFloat(discountValue)
    if (isNaN(value)) {
      setError('El valor debe ser un número válido')
      return
    }

    if (discountType === 'porcentaje' && value > 100) {
      setError('El descuento porcentual no puede exceder 100%')
      return
    }

    setLoading(true)
    setError('')

    try {
      await onApply({
        tipo: discountType,
        valor: value,
      })
    } catch (err) {
      setError(err.message || 'Error al aplicar descuento')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleApply()
    }
  }

  const handleClear = () => {
    onApply({
      tipo: null,
      valor: null,
    })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-lg w-full max-w-md overflow-hidden flex flex-col shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b" style={{ backgroundColor: GALIA.crema, borderColor: GALIA.grisLigero }}>
          <h2 className="text-2xl font-bold" style={{ color: GALIA.marron }}>
            Aplicar Descuento
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded transition"
            disabled={loading}
            title="Cerrar"
          >
            <X size={24} />
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border-b border-red-200 text-red-700 px-6 py-3 text-sm">
            {error}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 p-6 space-y-4">
          {/* Total Summary */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <p className="text-sm" style={{ color: GALIA.grisClaro }}>
              Total Original
            </p>
            <p className="text-2xl font-bold" style={{ color: GALIA.marron }}>
              ${total.toFixed(2)}
            </p>
          </div>

          {/* Discount Type Selection */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: GALIA.marron }}>
              Tipo de Descuento
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setDiscountType('porcentaje')}
                className={`py-2 rounded font-medium transition-colors border-2`}
                style={{
                  borderColor: discountType === 'porcentaje' ? GALIA.amarillo : GALIA.grisLigero,
                  backgroundColor: discountType === 'porcentaje' ? GALIA.crema : 'white',
                  color: GALIA.marron,
                }}
              >
                Porcentaje (%)
              </button>
              <button
                onClick={() => setDiscountType('monto_fijo')}
                className={`py-2 rounded font-medium transition-colors border-2`}
                style={{
                  borderColor: discountType === 'monto_fijo' ? GALIA.amarillo : GALIA.grisLigero,
                  backgroundColor: discountType === 'monto_fijo' ? GALIA.crema : 'white',
                  color: GALIA.marron,
                }}
              >
                Monto Fijo ($)
              </button>
            </div>
          </div>

          {/* Discount Value Input */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: GALIA.marron }}>
              Valor de Descuento
            </label>
            <input
              type="number"
              value={discountValue}
              onChange={(e) => {
                setDiscountValue(e.target.value)
                setError('')
              }}
              onKeyPress={handleKeyPress}
              placeholder={discountType === 'porcentaje' ? '0 - 100' : '0.00'}
              min="0"
              max={discountType === 'porcentaje' ? '100' : undefined}
              step="0.01"
              className="w-full px-4 py-2 border rounded text-lg font-semibold"
              style={{ borderColor: GALIA.grisLigero, color: GALIA.marron }}
              autoFocus
            />
            <p className="text-xs mt-2" style={{ color: GALIA.grisClaro }}>
              {discountType === 'porcentaje'
                ? 'Ingresa un porcentaje entre 0 y 100'
                : 'Ingresa un monto fijo en pesos'}
            </p>
          </div>

          {/* Discount Preview */}
          {discountValue && !error && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <span style={{ color: GALIA.grisClaro }}>Descuento:</span>
                <span className="font-bold" style={{ color: '#10B981' }}>
                  -${discountAmount.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-green-200">
                <span className="font-medium" style={{ color: GALIA.marron }}>
                  Total Final:
                </span>
                <span className="text-xl font-bold" style={{ color: GALIA.amarillo }}>
                  ${finalTotal.toFixed(2)}
                </span>
              </div>
            </div>
          )}

          {currentDiscount && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs text-blue-900">
                Hay un descuento aplicado actualmente. Haz clic en "Aplicar" para actualizar o "Limpiar" para eliminar.
              </p>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 p-6 border-t" style={{ borderColor: GALIA.grisLigero }}>
          <button
            onClick={onClose}
            disabled={loading}
            className="flex-1 py-2 rounded font-semibold transition-colors border"
            style={{ borderColor: GALIA.grisLigero, color: GALIA.marron }}
          >
            Cancelar
          </button>
          {currentDiscount && (
            <button
              onClick={handleClear}
              disabled={loading}
              className="flex-1 py-2 rounded font-semibold transition-colors"
              style={{ backgroundColor: '#EF4444', color: 'white' }}
              onMouseEnter={(e) => (e.target.style.opacity = '0.9')}
              onMouseLeave={(e) => (e.target.style.opacity = '1')}
            >
              Limpiar
            </button>
          )}
          <button
            onClick={handleApply}
            disabled={loading || !discountValue}
            className="flex-1 py-2 rounded font-bold text-white transition-opacity"
            style={{
              backgroundColor:
                discountValue && !error ? GALIA.marron : GALIA.grisLigero,
              cursor: discountValue && !error ? 'pointer' : 'not-allowed',
            }}
            onMouseEnter={(e) => {
              if (discountValue && !error) e.target.style.opacity = '0.9'
            }}
            onMouseLeave={(e) => {
              if (discountValue && !error) e.target.style.opacity = '1'
            }}
          >
            {loading ? 'Aplicando...' : 'Aplicar'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default DiscountModal
