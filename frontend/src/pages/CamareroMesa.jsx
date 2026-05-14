import { useState, useEffect } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { ChevronDown, Trash2, ChevronLeft } from 'lucide-react'
import productCategoriesService from '../services/productCategoriesService'
import productsService from '../services/productsService'
import ordersService from '../services/ordersService'
import GALIA from '../constants/colors'

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
    <div className="h-full w-full flex flex-col" style={{ backgroundColor: GALIA.crema }}>
      {/* Sticky header */}
      <div className="sticky top-0 z-10 px-4 py-3 shadow-sm" style={{ backgroundColor: GALIA.marron }}>
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/camarero')}
            className="flex items-center gap-2 text-white hover:opacity-80"
          >
            <ChevronLeft className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Mesa {mesaId}</h2>
          </button>
          <div className="text-right">
            <div className="text-xs text-white opacity-80">Total</div>
            <div className="text-xl font-bold" style={{ color: GALIA.amarillo }}>
              ${order.total?.toFixed(2) || '0.00'}
            </div>
          </div>
        </div>
      </div>

      {/* Categories scroll tabs */}
      <div className="flex gap-2 px-3 py-2 overflow-x-auto" style={{ backgroundColor: GALIA.blanco, borderBottom: `1px solid ${GALIA.grisLigero}` }}>
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => setActiveCategory(cat.id)}
            className="px-4 py-2 whitespace-nowrap text-sm rounded-full border transition"
            style={{
              backgroundColor: activeCategory === cat.id ? GALIA.amarillo : 'transparent',
              color: activeCategory === cat.id ? GALIA.marron : GALIA.marron,
              borderColor: activeCategory === cat.id ? GALIA.amarillo : GALIA.grisLigero
            }}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {/* Products grid - scrollable */}
      <div className="flex-1 overflow-y-auto px-3 py-3 pb-32">
        <div className="grid grid-cols-2 gap-2">
          {categoryProducts.map(product => (
            <div
              key={product.id}
              className="rounded-lg overflow-hidden cursor-pointer transition-shadow"
              style={{ backgroundColor: GALIA.blanco }}
            >
              {product.variants && product.variants.length > 0 ? (
                <div className="space-y-1">
                  {product.variants.map(variant => (
                    <button
                      key={variant.id}
                      onClick={() => handleAddProduct(variant)}
                      className="w-full text-left p-2 transition"
                      style={{ backgroundColor: GALIA.blanco, borderBottom: `1px solid ${GALIA.grisLigero}` }}
                    >
                      <div className="font-semibold text-sm" style={{ color: GALIA.marron }}>{product.name}</div>
                      <div className="text-xs" style={{ color: GALIA.grisClaro }}>{variant.name}</div>
                      <div className="text-sm font-bold" style={{ color: GALIA.amarillo }}>
                        ${parseFloat(variant.price).toFixed(2)}
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <button
                  onClick={() => {}}
                  className="text-center py-2"
                >
                  <div className="font-medium" style={{ color: GALIA.marron }}>{product.name}</div>
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Bottom bar - fixed order items + COBRAR */}
      <div className="fixed bottom-0 left-0 right-0 rounded-t-lg shadow-lg max-h-1/3 overflow-y-auto" style={{ backgroundColor: GALIA.blanco }}>
        <div className="sticky top-0 px-4 py-2 flex items-center justify-between" style={{ backgroundColor: GALIA.crema, borderBottom: `1px solid ${GALIA.grisLigero}` }}>
          <span className="font-semibold" style={{ color: GALIA.marron }}>Orden ({order.items?.length || 0} ítems)</span>
          <button
            onClick={() => setShowPayment(!showPayment)}
            className="p-1 rounded transition"
            style={{ color: GALIA.marron }}
          >
            <ChevronDown className="h-5 w-5" />
          </button>
        </div>

        {showPayment ? (
          <>
            {/* Order items list */}
            <div className="px-4 py-2 space-y-2 max-h-32 overflow-y-auto">
              {order.items?.map(item => (
                <div key={item.id} className="flex justify-between items-center py-1" style={{ borderBottom: `1px solid ${GALIA.grisLigero}` }}>
                  <div className="flex-1">
                    <div className="text-sm font-medium" style={{ color: GALIA.marron }}>{item.product_name}</div>
                    <div className="text-xs" style={{ color: GALIA.grisClaro }}>{item.variant_name}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-sm" style={{ color: GALIA.marron }}>
                      {item.quantity}x ${parseFloat(item.unit_price).toFixed(2)}
                    </div>
                    <button
                      onClick={() => handleRemoveItem(item.id)}
                      className="p-1 rounded transition"
                      style={{ color: '#dc2626' }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Payment method selector */}
            <div className="px-4 py-3 space-y-2" style={{ borderTop: `1px solid ${GALIA.grisLigero}` }}>
              <div className="text-sm font-semibold" style={{ color: GALIA.marron }}>Medio de pago</div>
              {['Efectivo', 'Tarjeta', 'Otro'].map(metodo => (
                <button
                  key={metodo}
                  onClick={() => setMedioPago(metodo)}
                  className="w-full p-2 rounded text-sm font-medium transition border-2"
                  style={{
                    backgroundColor: medioPago === metodo ? GALIA.amarillo : 'transparent',
                    color: medioPago === metodo ? GALIA.marron : GALIA.marron,
                    borderColor: medioPago === metodo ? GALIA.amarillo : GALIA.grisLigero
                  }}
                >
                  {metodo}
                </button>
              ))}

              {/* COBRAR button */}
              <button
                onClick={handleCobrar}
                disabled={saving || !order.items?.length}
                className="w-full mt-2 py-3 font-bold rounded-lg transition"
                style={{
                  backgroundColor: saving || !order.items?.length ? GALIA.grisLigero : GALIA.marron,
                  color: 'white'
                }}
              >
                {saving ? 'Cobrando...' : 'COBRAR'}
              </button>
            </div>
          </>
        ) : (
          // Collapsed view - just show total
          <div className="px-4 py-3 text-center">
            <div className="text-2xl font-bold" style={{ color: GALIA.amarillo }}>
              ${order.total?.toFixed(2) || '0.00'}
            </div>
            <div className="text-xs mt-1" style={{ color: GALIA.grisClaro }}>
              {order.items?.length || 0} ítems
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default CamareroMesa
