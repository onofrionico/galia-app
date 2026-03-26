import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Package, TrendingUp, ShoppingCart, DollarSign, Calendar, Truck, Loader2, AlertCircle, History, Info } from 'lucide-react'
import productsApi from '../../services/api/productsApi'
import PriceHistoryChart from '../../components/products/PriceHistoryChart'
import VolatilityIndicator from '../../components/products/VolatilityIndicator'

export default function ProductDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [product, setProduct] = useState(null)
  const [priceHistory, setPriceHistory] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('info')

  useEffect(() => {
    fetchProductDetail()
  }, [id])

  useEffect(() => {
    if (activeTab === 'history' && !priceHistory) {
      fetchPriceHistory()
    }
  }, [activeTab, id])

  const fetchProductDetail = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await productsApi.getById(id)
      setProduct(data)
    } catch (err) {
      setError(err.response?.data?.message || 'Error al cargar el producto')
    } finally {
      setLoading(false)
    }
  }

  const fetchPriceHistory = async () => {
    setLoadingHistory(true)
    try {
      const data = await productsApi.getPriceHistory(id)
      setPriceHistory(data)
    } catch (err) {
      console.error('Error loading price history:', err)
    } finally {
      setLoadingHistory(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 flex items-center gap-3">
          <AlertCircle className="w-6 h-6 text-red-600" />
          <div>
            <h3 className="font-semibold text-red-900">Error</h3>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (!product) return null

  const stats = product.statistics || {}

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/products')}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Volver a Productos
        </button>
        
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{product.name}</h1>
            <p className="text-gray-600 mt-1">SKU: {product.sku}</p>
          </div>
          <div className="flex items-center gap-3">
            {priceHistory?.analysis && (
              <VolatilityIndicator volatility={priceHistory.analysis.volatility} />
            )}
            <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${
              product.status === 'active' ? 'bg-green-100 text-green-800' :
              product.status === 'inactive' ? 'bg-gray-100 text-gray-800' :
              'bg-red-100 text-red-800'
            }`}>
              {product.status === 'active' ? 'Activo' :
               product.status === 'inactive' ? 'Inactivo' : 'Discontinuado'}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex gap-6">
            <button
              onClick={() => setActiveTab('info')}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'info'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <Info className="w-4 h-4" />
                Información
              </div>
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'history'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <History className="w-4 h-4" />
                Historial de Precios
              </div>
            </button>
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'info' && (
        <>
          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Precio Actual</p>
              <p className="text-2xl font-bold text-gray-900">
                ${parseFloat(product.current_price).toFixed(2)}
              </p>
              <p className="text-xs text-gray-500">por {product.unit_of_measure}</p>
            </div>
            <DollarSign className="w-8 h-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Compras</p>
              <p className="text-2xl font-bold text-gray-900">{stats.purchase_count || 0}</p>
              <p className="text-xs text-gray-500">total</p>
            </div>
            <ShoppingCart className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Cantidad Total</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_quantity || 0}</p>
              <p className="text-xs text-gray-500">{product.unit_of_measure}</p>
            </div>
            <Package className="w-8 h-8 text-purple-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Gasto Total</p>
              <p className="text-2xl font-bold text-gray-900">
                ${parseFloat(stats.total_spent || 0).toFixed(2)}
              </p>
              <p className="text-xs text-gray-500">histórico</p>
            </div>
            <TrendingUp className="w-8 h-8 text-orange-600" />
          </div>
        </div>
      </div>

      {/* Product Information */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Información del Producto</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Proveedor</label>
            <Link
              to={`/suppliers/${product.supplier_id}`}
              className="flex items-center gap-2 text-blue-600 hover:text-blue-800 hover:underline"
            >
              <Truck className="w-4 h-4" />
              {product.supplier?.name || 'N/A'}
            </Link>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Categoría</label>
            <p className="text-gray-900">{product.category || '-'}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Unidad de Medida</label>
            <p className="text-gray-900">{product.unit_of_measure}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Producto Maestro</label>
            <p className="text-gray-900">{product.product_master?.name || 'No vinculado'}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Fecha de Creación</label>
            <div className="flex items-center gap-2 text-gray-900">
              <Calendar className="w-4 h-4 text-gray-400" />
              {new Date(product.created_at).toLocaleDateString('es-AR')}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">Última Actualización</label>
            <div className="flex items-center gap-2 text-gray-900">
              <Calendar className="w-4 h-4 text-gray-400" />
              {new Date(product.updated_at).toLocaleDateString('es-AR')}
            </div>
          </div>
        </div>
      </div>

      {/* Price Statistics */}
      {stats.purchase_count > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Estadísticas de Precio</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Precio Promedio</label>
              <p className="text-2xl font-bold text-gray-900">
                ${parseFloat(stats.avg_price || 0).toFixed(2)}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Precio Mínimo</label>
              <p className="text-2xl font-bold text-green-600">
                ${parseFloat(stats.min_price || 0).toFixed(2)}
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Precio Máximo</label>
              <p className="text-2xl font-bold text-red-600">
                ${parseFloat(stats.max_price || 0).toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      )}

        </>
      )}

      {activeTab === 'history' && (
        <>
          {loadingHistory ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
            </div>
          ) : priceHistory ? (
            <>
              <PriceHistoryChart 
                data={priceHistory.history} 
                analysis={priceHistory.analysis}
              />
              
              {/* Price History Table */}
              {priceHistory.history && priceHistory.history.length > 0 && (
                <div className="bg-white rounded-lg shadow p-6 mt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Detalle de Cambios</h3>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b">
                        <tr>
                          <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Fecha</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Precio</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Cambio</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Origen</th>
                          <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Notas</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {priceHistory.history.map((history) => (
                          <tr key={history.id} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-gray-900">
                              {new Date(history.effective_date).toLocaleDateString('es-AR')}
                            </td>
                            <td className="px-4 py-3 font-medium text-gray-900">
                              ${history.price.toFixed(2)}
                            </td>
                            <td className="px-4 py-3">
                              {history.change_percentage !== 0 && (
                                <span className={`inline-flex items-center gap-1 ${
                                  history.change_percentage > 0 ? 'text-red-600' : 'text-green-600'
                                }`}>
                                  {history.change_percentage > 0 ? '↑' : '↓'} 
                                  {Math.abs(history.change_percentage).toFixed(2)}%
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-3 text-gray-700">
                              <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                                {history.source || 'manual'}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-gray-600 text-sm">
                              {history.notes || '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-gray-500 text-center">No hay historial de precios disponible</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
