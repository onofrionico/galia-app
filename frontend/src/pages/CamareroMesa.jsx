import { useState, useEffect } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { ChevronDown, Trash2 } from 'lucide-react'
import productCategoriesService from '../services/productCategoriesService'
import productsService from '../services/productsService'
import ordersService from '../services/ordersService'

const CamareroMesa = () => {
  const { mesaId } = useParams()
  const { state } = useLocation()
  const navigate = useNavigate()

  // State
  const [order, setOrder] = useState(null)
  const [categories, setCategories] = useState([])
  const [products, setProducts] = useState([])
  const [activeCategory, setActiveCategory] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showPayment, setShowPayment] = useState(false)
  const [medioPago, setMedioPago] = useState('Efectivo')
  const [error, setError] = useState('')

  // 10-second polling for order updates (in case admin adds from POS)
  useEffect(() => {
    fetchOrderAndProducts()
    const interval = setInterval(fetchOrderAndProducts, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchOrderAndProducts = async () => {
    try {
      const orderId = state?.orderId
      if (!orderId) {
        setError('No order ID provided')
        return
      }

      const [orderRes, catRes, prodRes] = await Promise.all([
        ordersService.getOrder(orderId),
        productCategoriesService.getCategories(),
        productsService.getProducts({ per_page: 100 })
      ])

      setOrder(orderRes)
      setCategories(catRes.product_categories || [])
      setProducts(prodRes.products || [])

      if (catRes.product_categories && catRes.product_categories.length > 0) {
        setActiveCategory(catRes.product_categories[0].id)
      }
    } catch (err) {
      setError('Error loading data')
    } finally {
      setLoading(false)
    }
  }

  const handleAddProduct = async (variant) => {
    try {
      const updated = await ordersService.addItem(order.id, {
        product_variant_id: variant.id,
        quantity: 1
      })
      setOrder(updated)
    } catch (err) {
      setError('Error adding item')
    }
  }

  const handleRemoveItem = async (itemId) => {
    try {
      const updated = await ordersService.removeItem(order.id, itemId)
      setOrder(updated)
    } catch (err) {
      setError('Error removing item')
    }
  }

  const handleCobrar = async () => {
    setSaving(true)
    try {
      await ordersService.cobrar(order.id, medioPago)
      navigate('/camarero', {
        state: { success: true, message: `Mesa ${mesaId} cobrada` }
      })
    } catch (err) {
      setError('Error al cobrar')
    } finally {
      setSaving(false)
      setShowPayment(false)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-full">Cargando...</div>
  }

  if (!order) {
    return <div className="flex items-center justify-center h-full">Orden no encontrada</div>
  }

  const categoryProducts = products.filter(p => p.category_id === activeCategory)

  return (
    <div className="h-full w-full flex flex-col bg-gray-50">
      {/* Sticky header */}
      <div className="sticky top-0 z-10 px-4 py-3 bg-white border-b shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">Mesa {mesaId}</h2>
          <div className="text-right">
            <div className="text-xs text-gray-500">Total</div>
            <div className="text-xl font-bold text-blue-600">
              ${order.total?.toFixed(2) || '0.00'}
            </div>
          </div>
        </div>
      </div>

      {/* Categories scroll tabs */}
      <div className="flex gap-2 px-4 py-2 overflow-x-auto bg-white border-b">
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className={`px-3 py-1 whitespace-nowrap text-sm rounded transition ${
              activeCategory === cat.id
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700'
            }`}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {/* Products grid - scrollable */}
      <div className="flex-1 overflow-y-auto px-4 py-3">
        <div className="grid grid-cols-2 gap-3 pb-32">
          {categoryProducts.map(product => (
            <div
              key={product.id}
              className="bg-white rounded-lg shadow-sm p-3 cursor-pointer hover:shadow-md transition"
            >
              {product.variants && product.variants.length > 0 ? (
                <div className="space-y-2">
                  {product.variants.map(variant => (
                    <button
                      key={variant.id}
                      onClick={() => handleAddProduct(variant)}
                      className="w-full text-left p-2 bg-gray-50 hover:bg-blue-50 rounded text-sm"
                    >
                      <div className="font-medium text-gray-800">{product.name}</div>
                      <div className="text-xs text-gray-600">{variant.name}</div>
                      <div className="text-sm font-bold text-blue-600">
                        ${parseFloat(variant.price).toFixed(2)}
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <button
                  onClick={() => {
                    // Handle product without variants (shouldn't happen)
                  }}
                  className="text-center py-2"
                >
                  <div className="font-medium text-gray-800">{product.name}</div>
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Bottom sheet - fixed order items + COBRAR */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t rounded-t-lg shadow-lg max-h-1/3 overflow-y-auto">
        <div className="sticky top-0 px-4 py-2 bg-gray-50 border-b flex items-center justify-between">
          <span className="font-semibold text-gray-800">Orden ({order.items?.length || 0} ítems)</span>
          <button
            onClick={() => setShowPayment(!showPayment)}
            className="p-1 hover:bg-gray-200 rounded"
          >
            <ChevronDown className="h-5 w-5" />
          </button>
        </div>

        {showPayment ? (
          <>
            {/* Order items list */}
            <div className="px-4 py-2 space-y-2 max-h-32 overflow-y-auto">
              {order.items?.map(item => (
                <div key={item.id} className="flex justify-between items-center py-1 border-b">
                  <div className="flex-1">
                    <div className="text-sm font-medium">{item.product_name}</div>
                    <div className="text-xs text-gray-600">{item.variant_name}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-sm">
                      {item.quantity}x ${parseFloat(item.unit_price).toFixed(2)}
                    </div>
                    <button
                      onClick={() => handleRemoveItem(item.id)}
                      className="p-1 text-red-500 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Payment method selector */}
            <div className="px-4 py-3 space-y-2 border-t">
              <div className="text-sm font-semibold text-gray-800">Medio de pago</div>
              {['Efectivo', 'Débito', 'QR'].map(metodo => (
                <button
                  key={metodo}
                  onClick={() => setMedioPago(metodo)}
                  className={`w-full p-2 rounded text-sm font-medium transition ${
                    medioPago === metodo
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                  }`}
                >
                  {metodo}
                </button>
              ))}

              {/* COBRAR button */}
              <button
                onClick={handleCobrar}
                disabled={saving || !order.items?.length}
                className="w-full mt-2 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold rounded-lg transition"
              >
                {saving ? 'Cobrando...' : 'COBRAR'}
              </button>
            </div>
          </>
        ) : (
          // Collapsed view - just show total
          <div className="px-4 py-3 text-center">
            <div className="text-2xl font-bold text-green-600">
              ${order.total?.toFixed(2) || '0.00'}
            </div>
            <div className="text-xs text-gray-600 mt-1">
              {order.items?.length || 0} ítems
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default CamareroMesa
