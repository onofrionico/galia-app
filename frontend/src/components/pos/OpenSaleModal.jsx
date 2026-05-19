import { useState } from 'react'
import { X } from 'lucide-react'
import GALIA from '../../constants/colors'
import ordersService from '../../services/ordersService'

const OpenSaleModal = ({ isOpen, mesaId, mesaNumber, onClose, onSaleCreated }) => {
  if (!isOpen) return null

  const [numeroPersonas, setNumeroPersonas] = useState(1)
  const [comentarios, setComentarios] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleCreate = async () => {
    if (numeroPersonas < 1) {
      setError('El número de personas debe ser mayor a 0')
      return
    }

    setSaving(true)
    setError('')

    try {
      const order = await ordersService.createOrder({
        mesa_id: mesaId,
      })

      onSaleCreated?.(order)
      onClose()
    } catch (err) {
      setError(err.response?.data?.error || 'Error al crear la orden')
    } finally {
      setSaving(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && numeroPersonas >= 1) {
      handleCreate()
    }
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
            Nueva Venta
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded transition"
            disabled={saving}
            title="Cerrar (ESC)"
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
          {/* Mesa Info */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <p className="text-sm" style={{ color: GALIA.grisClaro }}>
              Mesa
            </p>
            <p className="text-2xl font-bold" style={{ color: GALIA.marron }}>
              {mesaNumber || `Mesa ${mesaId}`}
            </p>
          </div>

          {/* Number of People */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: GALIA.marron }}>
              Número de Personas
            </label>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setNumeroPersonas(Math.max(1, numeroPersonas - 1))}
                className="px-4 py-2 rounded border transition-colors"
                style={{ borderColor: GALIA.grisLigero, color: GALIA.marron }}
              >
                -
              </button>
              <input
                type="number"
                value={numeroPersonas}
                onChange={(e) => {
                  const val = parseInt(e.target.value, 10)
                  if (!isNaN(val) && val >= 1) {
                    setNumeroPersonas(val)
                  }
                }}
                onKeyPress={handleKeyPress}
                className="flex-1 px-4 py-2 border rounded text-center font-bold text-lg"
                style={{ borderColor: GALIA.grisLigero, color: GALIA.marron }}
                min="1"
              />
              <button
                onClick={() => setNumeroPersonas(numeroPersonas + 1)}
                className="px-4 py-2 rounded border transition-colors"
                style={{ borderColor: GALIA.grisLigero, color: GALIA.marron }}
              >
                +
              </button>
            </div>
          </div>

          {/* Comments */}
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: GALIA.marron }}>
              Comentarios (opcional)
            </label>
            <textarea
              value={comentarios}
              onChange={(e) => setComentarios(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ej: preferencias, solicitudes especiales..."
              className="w-full px-4 py-2 border rounded resize-none"
              style={{ borderColor: GALIA.grisLigero, color: GALIA.marron }}
              rows="3"
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 p-6 border-t" style={{ borderColor: GALIA.grisLigero }}>
          <button
            onClick={onClose}
            disabled={saving}
            className="flex-1 py-2 rounded font-semibold transition-colors border"
            style={{ borderColor: GALIA.grisLigero, color: GALIA.marron }}
          >
            Cancelar
          </button>
          <button
            onClick={handleCreate}
            disabled={saving || numeroPersonas < 1}
            className="flex-1 py-2 rounded font-bold text-lg transition-opacity text-white"
            style={{
              backgroundColor: numeroPersonas >= 1 ? GALIA.marron : GALIA.grisLigero,
              cursor: numeroPersonas >= 1 ? 'pointer' : 'not-allowed',
            }}
            onMouseEnter={(e) => {
              if (numeroPersonas >= 1) e.target.style.opacity = '0.9'
            }}
            onMouseLeave={(e) => {
              if (numeroPersonas >= 1) e.target.style.opacity = '1'
            }}
          >
            {saving ? 'Creando...' : 'Crear Venta'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default OpenSaleModal
