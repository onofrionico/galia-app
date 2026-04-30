import { useState, useEffect } from 'react'
import { AlertCircle } from 'lucide-react'
import productsService from '../services/productsService'

const Stock = () => {
  const [variants, setVariants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updatingId, setUpdatingId] = useState(null)

  useEffect(() => {
    fetchLowStock()
  }, [])

  const fetchLowStock = async () => {
    setLoading(true)
    try {
      const response = await productsService.getLowStock()
      setVariants(response.variants || [])
      setError('')
    } catch (err) {
      setError('Error al cargar el inventario')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleStockChange = async (variantId, productId, newQuantity) => {
    setUpdatingId(variantId)
    try {
      await productsService.adjustStock(productId, variantId, newQuantity)
      setVariants(
        variants.map((v) =>
          v.id === variantId
            ? { ...v, stock_quantity: newQuantity }
            : v
        )
      )
      setError('')
    } catch (err) {
      setError('Error al actualizar stock')
    } finally {
      setUpdatingId(null)
    }
  }

  if (loading) {
    return <div className="p-6">Cargando inventario...</div>
  }

  const lowStockVariants = variants.filter(
    (v) => v.stock_quantity <= v.min_stock
  )
  const normalStockVariants = variants.filter(
    (v) => v.stock_quantity > v.min_stock
  )

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">📦 Inventario</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {lowStockVariants.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6 flex gap-3">
          <AlertCircle className="text-yellow-600 flex-shrink-0" size={20} />
          <div>
            <h3 className="font-bold text-yellow-900 mb-1">Alerta: Stock Bajo</h3>
            <p className="text-sm text-yellow-800">
              {lowStockVariants.length} productos tienen stock por debajo del mínimo
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Stock Directo */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b p-4 bg-blue-50">
            <h2 className="text-lg font-bold text-blue-900">
              Stock Directo (Variantes)
            </h2>
            <p className="text-sm text-blue-700 mt-1">
              {variants.length} items
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-sm text-gray-700">
                    Producto
                  </th>
                  <th className="text-right px-4 py-3 font-medium text-sm text-gray-700">
                    Stock
                  </th>
                  <th className="text-right px-4 py-3 font-medium text-sm text-gray-700">
                    Mín
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {variants.length === 0 ? (
                  <tr>
                    <td colSpan="3" className="px-4 py-4 text-center text-gray-500">
                      No hay variantes
                    </td>
                  </tr>
                ) : (
                  variants.map((variant) => {
                    const isLow = variant.stock_quantity <= variant.min_stock
                    return (
                      <tr
                        key={variant.id}
                        className={isLow ? 'bg-red-50 hover:bg-red-100' : 'hover:bg-gray-50'}
                      >
                        <td className="px-4 py-3">
                          <div className="font-medium text-sm">
                            {variant.product_name}
                          </div>
                          <div className="text-xs text-gray-600">
                            {variant.name}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <input
                            type="number"
                            value={variant.stock_quantity}
                            onChange={(e) =>
                              handleStockChange(
                                variant.id,
                                variant.product_id,
                                parseFloat(e.target.value)
                              )
                            }
                            disabled={updatingId === variant.id}
                            className={`w-20 border rounded px-2 py-1 text-right text-sm ${
                              isLow
                                ? 'border-red-300 bg-red-100 text-red-900'
                                : 'border-gray-300'
                            }`}
                            step="0.1"
                          />
                        </td>
                        <td className="px-4 py-3 text-right text-sm">
                          {variant.min_stock}
                          {isLow && (
                            <div className="text-red-600 font-bold text-xs mt-1">
                              ⚠️ BAJO
                            </div>
                          )}
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Insumos */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b p-4 bg-purple-50">
            <h2 className="text-lg font-bold text-purple-900">
              Insumos (Supplies)
            </h2>
            <p className="text-sm text-purple-700 mt-1">
              Stock disponible para recetas
            </p>
          </div>

          <div className="p-4 text-center text-gray-500">
            <p>Los insumos se gestionan en la sección de Productos</p>
            <p className="text-sm mt-2 text-gray-600">
              Al crear recetas, el stock de insumos se descuenta automáticamente
              al vender productos con receta.
            </p>
          </div>
        </div>
      </div>

      {/* Resumen */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-600">{variants.length}</div>
          <div className="text-sm text-blue-900">Variantes en Stock</div>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-600">
            {normalStockVariants.length}
          </div>
          <div className="text-sm text-green-900">Stock Normal</div>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-red-600">
            {lowStockVariants.length}
          </div>
          <div className="text-sm text-red-900">Stock Bajo</div>
        </div>
      </div>

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-bold text-blue-900 mb-2">ℹ️ Información</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>
            • <strong>Stock Directo:</strong> Para productos simples (sin receta)
          </li>
          <li>
            • <strong>Insumos:</strong> Ingredientes para productos con receta
          </li>
          <li>
            • <strong>Min Stock:</strong> Nivel mínimo. Se resalta en rojo si está
            por debajo
          </li>
          <li>
            • Edita los números directamente. Los cambios se guardan automáticamente
          </li>
        </ul>
      </div>
    </div>
  )
}

export default Stock
