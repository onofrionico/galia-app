import { useState } from 'react'
import { X, Plus, Minus } from 'lucide-react'
import GALIA from '../../constants/colors'

const PaymentModal = ({
  isOpen,
  saleId,
  total,
  paid,
  onPaymentRegistered,
  onCloseSale,
  onClose,
}) => {
  if (!isOpen) return null

  const [paymentMethod, setPaymentMethod] = useState('Efectivo')
  const [paymentAmount, setPaymentAmount] = useState(total - paid)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [paymentHistory, setPaymentHistory] = useState([])

  const remaining = Math.max(0, total - paid)
  const isPaid = remaining <= 0

  const paymentMethods = ['Efectivo', 'Tarjeta Débito', 'Tarjeta Crédito', 'Transferencia', 'Otro']

  const handlePaymentAmountChange = (delta) => {
    const newAmount = paymentAmount + delta
    const maxPayment = remaining
    if (newAmount > 0 && newAmount <= maxPayment) {
      setPaymentAmount(newAmount)
    }
  }

  const handleCustomAmount = (e) => {
    const value = parseFloat(e.target.value)
    if (!isNaN(value) && value >= 0 && value <= remaining) {
      setPaymentAmount(value)
    }
  }

  const handleRegisterPayment = async () => {
    if (!paymentMethod) {
      setError('Selecciona un método de pago')
      return
    }

    if (paymentAmount <= 0) {
      setError('El monto debe ser mayor a 0')
      return
    }

    if (paymentAmount > remaining) {
      setError('El monto no puede exceder el total pendiente')
      return
    }

    setLoading(true)
    setError('')

    try {
      await onPaymentRegistered({
        amount: paymentAmount,
        method: paymentMethod,
      })

      // Add to history
      setPaymentHistory([
        ...paymentHistory,
        {
          method: paymentMethod,
          amount: paymentAmount,
          timestamp: new Date().toLocaleTimeString(),
        },
      ])

      // Reset payment form
      const newRemaining = remaining - paymentAmount
      if (newRemaining <= 0) {
        // Venta fully paid, prepare to close
        if (onCloseSale) {
          await onCloseSale()
        }
      } else {
        // Reset for next payment
        setPaymentAmount(newRemaining)
        setPaymentMethod('Efectivo')
      }
    } catch (err) {
      setError(err.message || 'Error al registrar el pago')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    if (remaining > 0) {
      if (confirm('Aún hay pendiente. ¿Cerrar de todas formas?')) {
        onClose()
      }
    } else {
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-lg w-full max-w-md max-h-[90vh] overflow-hidden flex flex-col shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b" style={{ backgroundColor: GALIA.crema, borderColor: GALIA.grisLigero }}>
          <h2 className="text-2xl font-bold" style={{ color: GALIA.marron }}>
            Registrar Pago
          </h2>
          <button
            onClick={handleClose}
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
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {/* Summary */}
          <div className="space-y-2 pb-4 border-b" style={{ borderColor: GALIA.grisLigero }}>
            <div className="flex justify-between items-center">
              <span style={{ color: GALIA.grisClaro }}>Total:</span>
              <span className="font-bold" style={{ color: GALIA.marron }}>
                ${total.toFixed(2)}
              </span>
            </div>
            {paid > 0 && (
              <div className="flex justify-between items-center">
                <span style={{ color: GALIA.grisClaro }}>Pagado:</span>
                <span className="font-bold" style={{ color: GALIA.verde }}>
                  ${paid.toFixed(2)}
                </span>
              </div>
            )}
            <div className="flex justify-between items-center pt-2 border-t" style={{ borderColor: GALIA.grisLigero }}>
              <span className="font-medium" style={{ color: GALIA.marron }}>
                Pendiente:
              </span>
              <span className="text-lg font-bold" style={{ color: remaining > 0 ? '#DC2626' : GALIA.verde }}>
                ${remaining.toFixed(2)}
              </span>
            </div>
          </div>

          {!isPaid && (
            <>
              {/* Payment Method */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: GALIA.marron }}>
                  Método de Pago
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {paymentMethods.map((method) => (
                    <button
                      key={method}
                      onClick={() => setPaymentMethod(method)}
                      className="py-2 rounded font-medium transition-colors border-2 text-sm"
                      style={{
                        borderColor: paymentMethod === method ? GALIA.amarillo : GALIA.grisLigero,
                        backgroundColor: paymentMethod === method ? GALIA.crema : 'white',
                        color: GALIA.marron,
                      }}
                    >
                      {method}
                    </button>
                  ))}
                </div>
              </div>

              {/* Payment Amount */}
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: GALIA.marron }}>
                  Monto a Pagar
                </label>
                <div className="flex items-center gap-2 mb-3">
                  <button
                    onClick={() => handlePaymentAmountChange(-10)}
                    className="px-3 py-2 rounded border"
                    style={{ borderColor: GALIA.grisLigero, color: GALIA.marron }}
                  >
                    <Minus size={16} />
                  </button>
                  <input
                    type="number"
                    value={paymentAmount.toFixed(2)}
                    onChange={handleCustomAmount}
                    min="0"
                    max={remaining}
                    step="1"
                    className="flex-1 px-4 py-2 border rounded text-center font-bold text-lg"
                    style={{ borderColor: GALIA.grisLigero, color: GALIA.marron }}
                  />
                  <button
                    onClick={() => handlePaymentAmountChange(10)}
                    className="px-3 py-2 rounded border"
                    style={{ borderColor: GALIA.grisLigero, color: GALIA.marron }}
                  >
                    <Plus size={16} />
                  </button>
                </div>

                {/* Quick amount buttons */}
                <div className="grid grid-cols-3 gap-2">
                  {[10, 20, 50].map((amount) => (
                    <button
                      key={amount}
                      onClick={() => setPaymentAmount(Math.min(amount, remaining))}
                      disabled={amount > remaining}
                      className="py-2 rounded text-sm font-semibold transition-colors border"
                      style={{
                        borderColor: GALIA.grisLigero,
                        backgroundColor: GALIA.crema,
                        color: GALIA.marron,
                        opacity: amount > remaining ? 0.5 : 1,
                        cursor: amount > remaining ? 'not-allowed' : 'pointer',
                      }}
                    >
                      ${amount}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Payment History */}
          {paymentHistory.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm font-medium mb-2" style={{ color: GALIA.marron }}>
                Pagos Registrados
              </p>
              <div className="space-y-1">
                {paymentHistory.map((payment, idx) => (
                  <div key={idx} className="flex justify-between items-center text-xs">
                    <span>{payment.method}</span>
                    <span className="font-medium">${payment.amount.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {isPaid && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm font-medium" style={{ color: '#10B981' }}>
                ✓ Venta completamente pagada
              </p>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 p-6 border-t" style={{ borderColor: GALIA.grisLigero }}>
          <button
            onClick={handleClose}
            disabled={loading}
            className="flex-1 py-2 rounded font-semibold transition-colors border"
            style={{ borderColor: GALIA.grisLigero, color: GALIA.marron }}
          >
            Cancelar
          </button>
          {!isPaid ? (
            <button
              onClick={handleRegisterPayment}
              disabled={loading || !paymentMethod || paymentAmount <= 0}
              className="flex-1 py-2 rounded font-bold text-white transition-opacity"
              style={{
                backgroundColor:
                  paymentMethod && paymentAmount > 0 ? GALIA.marron : GALIA.grisLigero,
                cursor: paymentMethod && paymentAmount > 0 ? 'pointer' : 'not-allowed',
              }}
              onMouseEnter={(e) => {
                if (paymentMethod && paymentAmount > 0) e.target.style.opacity = '0.9'
              }}
              onMouseLeave={(e) => {
                if (paymentMethod && paymentAmount > 0) e.target.style.opacity = '1'
              }}
            >
              {loading ? 'Procesando...' : 'Registrar Pago'}
            </button>
          ) : (
            <button
              onClick={() => {
                if (onCloseSale) onCloseSale()
              }}
              disabled={loading}
              className="flex-1 py-2 rounded font-bold text-white transition-opacity"
              style={{ backgroundColor: GALIA.verde }}
              onMouseEnter={(e) => (e.target.style.opacity = '0.9')}
              onMouseLeave={(e) => (e.target.style.opacity = '1')}
            >
              {loading ? 'Cerrando...' : 'Cerrar Venta'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default PaymentModal
