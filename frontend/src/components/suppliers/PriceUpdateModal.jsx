import React, { useState } from 'react'
import { X, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react'

export default function PriceUpdateModal({ 
  priceVariances, 
  onConfirm, 
  onCancel,
  onUpdateCatalog 
}) {
  const [selectedUpdates, setSelectedUpdates] = useState(
    priceVariances.map(v => v.product_id)
  )

  const toggleUpdate = (productId) => {
    setSelectedUpdates(prev => 
      prev.includes(productId)
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    )
  }

  const handleConfirm = () => {
    const updates = priceVariances
      .filter(v => selectedUpdates.includes(v.product_id))
      .map(v => ({
        product_id: v.product_id,
        new_price: v.purchase_price
      }))
    
    onConfirm(updates)
  }

  const formatPrice = (price) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS'
    }).format(price)
  }

  const getVarianceIcon = (variance) => {
    if (variance > 0) return <TrendingUp className="w-5 h-5 text-red-600" />
    if (variance < 0) return <TrendingDown className="w-5 h-5 text-green-600" />
    return null
  }

  const getVarianceColor = (variance) => {
    if (Math.abs(variance) > 10) return 'text-red-600'
    if (Math.abs(variance) > 5) return 'text-yellow-600'
    return 'text-gray-600'
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-yellow-600" />
            <h2 className="text-2xl font-bold text-gray-900">
              Diferencias de Precio Detectadas
            </h2>
          </div>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          <p className="text-gray-600 mb-4">
            Los siguientes productos tienen precios diferentes al catálogo. 
            Selecciona cuáles deseas actualizar en el catálogo:
          </p>

          <div className="space-y-3">
            {priceVariances.map((variance) => (
              <div
                key={variance.product_id}
                className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    checked={selectedUpdates.includes(variance.product_id)}
                    onChange={() => toggleUpdate(variance.product_id)}
                    className="mt-1 w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-gray-900">
                        {variance.product_name}
                      </h3>
                      <div className="flex items-center gap-2">
                        {getVarianceIcon(variance.variance_percentage)}
                        <span className={`font-bold ${getVarianceColor(variance.variance_percentage)}`}>
                          {variance.variance_percentage > 0 ? '+' : ''}
                          {variance.variance_percentage.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    
                    <div className="text-sm text-gray-600">
                      SKU: {variance.sku}
                    </div>
                    
                    <div className="flex items-center gap-4 mt-2">
                      <div>
                        <span className="text-xs text-gray-500">Precio Catálogo:</span>
                        <div className="font-semibold text-gray-700">
                          {formatPrice(variance.catalog_price)}
                        </div>
                      </div>
                      
                      <div className="text-gray-400">→</div>
                      
                      <div>
                        <span className="text-xs text-gray-500">Precio Compra:</span>
                        <div className="font-semibold text-blue-600">
                          {formatPrice(variance.purchase_price)}
                        </div>
                      </div>
                      
                      <div className="flex-1"></div>
                      
                      <div>
                        <span className="text-xs text-gray-500">Diferencia:</span>
                        <div className={`font-semibold ${getVarianceColor(variance.variance_percentage)}`}>
                          {formatPrice(variance.purchase_price - variance.catalog_price)}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">
              ¿Qué sucederá?
            </h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• La compra se guardará con los precios ingresados</li>
              <li>• Los productos seleccionados actualizarán su precio de catálogo</li>
              <li>• Se creará un registro en el historial de precios</li>
              <li>• Los productos no seleccionados mantendrán su precio actual</li>
            </ul>
          </div>
        </div>

        <div className="flex gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => onConfirm([])}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
          >
            Guardar sin Actualizar
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            disabled={selectedUpdates.length === 0}
          >
            Guardar y Actualizar ({selectedUpdates.length})
          </button>
        </div>
      </div>
    </div>
  )
}
