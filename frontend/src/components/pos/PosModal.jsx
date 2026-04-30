import { useState, useEffect } from 'react'
import { X, Plus, Minus } from 'lucide-react'
import productsService from '../../services/productsService'
import productCategoriesService from '../../services/productCategoriesService'

const PosModal = ({ mesaId, onClose, onSale }) => {
  const [categories, setCategories] = useState([])
  const [products, setProducts] = useState([])
  const [activeCategory, setActiveCategory] = useState(null)
  const [selectedVariant, setSelectedVariant] = useState(null)
  const [order, setOrder] = useState([])
  const [medioPago, setMedioPago] = useState('Efectivo')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [catsRes, prodsRes] = await Promise.all([
        productCategoriesService.getCategories({ include_inactive: false }),
        productsService.getProducts({ per_page: 100, include_inactive: false }),
      ])

      setCategories(catsRes.categories || [])
      setProducts(prodsRes.products || [])

      if (catsRes.categories && catsRes.categories.length > 0) {
        setActiveCategory(catsRes.categories[0].id)
      }
    } catch (err) {
      setError('Error al cargar productos')
    } finally {
      setLoading(false)
    }
  }

  const filteredProducts = activeCategory
    ? products.filter((p) => p.category_id === activeCategory && p.is_active)
    : products.filter((p) => p.is_active)

  const handleAddProduct = (product) => {
    if (product.variants && product.variants.length > 1) {
      setSelectedVariant({ product, selectingVariant: true })
      return
    }

    const variant = product.variants?.[0]
    if (!variant) {
      setError('No hay variantes disponibles')
      return
    }

    addToOrder(variant, product)
  }

  const addToOrder = (variant, product) => {
    const existingItem = order.find(
      (item) => item.product_variant_id === variant.id
    )

    if (existingItem) {
      setOrder(
        order.map((item) =>
          item.product_variant_id === variant.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        )
      )
    } else {
      setOrder([
        ...order,
        {
          product_variant_id: variant.id,
          product_name: product.name,
          variant_name: variant.name,
          quantity: 1,
          unit_price: variant.price,
          subtotal: variant.price,
        },
      ])
    }
    setSelectedVariant(null)
    setError('')
  }

  const handleQuantityChange = (variantId, delta) => {
    setOrder(
      order
        .map((item) => {
          if (item.product_variant_id === variantId) {
            const newQty = Math.max(1, item.quantity + delta)
            return {
              ...item,
              quantity: newQty,
              subtotal: item.unit_price * newQty,
            }
          }
          return item
        })
        .filter((item) => item.quantity > 0)
    )
  }

  const handleRemoveItem = (variantId) => {
    setOrder(order.filter((item) => item.product_variant_id !== variantId))
  }

  const totalAmount = order.reduce((sum, item) => sum + item.subtotal, 0)

  const handleCobrar = async () => {
    if (order.length === 0) {
      setError('Agrega al menos un item')
      return
    }

    setSaving(true)
    try {
      await onSale({
        items: order.map((item) => ({
          product_variant_id: item.product_variant_id,
          quantity: item.quantity,
        })),
        mesa_id: mesaId,
        medio_pago: medioPago,
      })
      onClose()
    } catch (err) {
      setError(err.response?.data?.error || 'Error al guardar venta')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">Cargando...</div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold">
            {mesaId ? `Mesa ${mesaId}` : 'Nueva Venta'} - POS
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded"
            disabled={saving}
          >
            <X size={24} />
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border-b border-red-200 text-red-700 px-6 py-3">
            {error}
          </div>
        )}

        <div className="flex-1 overflow-hidden flex gap-4 p-6">
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex gap-2 mb-4 pb-4 border-b overflow-x-auto">
              <button
                onClick={() => setActiveCategory(null)}
                className={`px-4 py-2 rounded whitespace-nowrap ${
                  activeCategory === null
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                Todos
              </button>
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  className={`px-4 py-2 rounded whitespace-nowrap ${
                    activeCategory === cat.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700'
                  }`}
                >
                  {cat.icon} {cat.name}
                </button>
              ))}
            </div>

            <div className="overflow-y-auto flex-1">
              <div className="grid grid-cols-3 gap-3">
                {filteredProducts.map((product) => (
                  <button
                    key={product.id}
                    onClick={() => handleAddProduct(product)}
                    className="border-2 border-gray-300 rounded-lg p-3 hover:border-blue-500 hover:bg-blue-50 transition text-center"
                  >
                    <div className="text-3xl mb-2">📦</div>
                    <div className="font-medium text-sm">{product.name}</div>
                    {product.variants && product.variants.length > 0 && (
                      <div className="text-xs text-gray-600 mt-1">
                        ${product.variants[0].price}
                        {product.variants.length > 1 && ` +${product.variants.length - 1}`}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="w-64 border-l pl-4 flex flex-col">
            <h3 className="font-bold text-lg mb-3">Comanda</h3>

            <div className="flex-1 overflow-y-auto mb-4 border rounded p-3 bg-gray-50">
              {order.length === 0 ? (
                <div className="text-center text-gray-500 py-4">Sin items</div>
              ) : (
                <div className="space-y-2">
                  {order.map((item) => (
                    <div key={item.product_variant_id} className="bg-white p-2 rounded">
                      <div className="text-sm font-medium">{item.product_name}</div>
                      <div className="text-xs text-gray-600">{item.variant_name}</div>
                      <div className="flex items-center justify-between mt-1">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() =>
                              handleQuantityChange(item.product_variant_id, -1)
                            }
                            className="p-0.5 hover:bg-red-100 rounded"
                          >
                            <Minus size={14} />
                          </button>
                          <span className="w-6 text-center text-sm">
                            {item.quantity}
                          </span>
                          <button
                            onClick={() =>
                              handleQuantityChange(item.product_variant_id, 1)
                            }
                            className="p-0.5 hover:bg-green-100 rounded"
                          >
                            <Plus size={14} />
                          </button>
                        </div>
                        <div className="text-sm font-medium">
                          ${item.subtotal.toFixed(2)}
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveItem(item.product_variant_id)}
                        className="text-xs text-red-600 hover:underline mt-1"
                      >
                        Eliminar
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="border-t pt-3 mb-3">
              <div className="flex justify-between items-center font-bold text-lg mb-3">
                <span>Total:</span>
                <span className="text-green-600">${totalAmount.toFixed(2)}</span>
              </div>

              <div className="mb-3">
                <label className="block text-sm font-medium mb-2">
                  Medio de Pago
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {['Efectivo', 'Débito', 'QR'].map((option) => (
                    <button
                      key={option}
                      onClick={() => setMedioPago(option)}
                      className={`py-2 rounded text-sm font-medium transition ${
                        medioPago === option
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={handleCobrar}
                disabled={saving || order.length === 0}
                className="w-full bg-green-600 text-white font-bold py-3 rounded hover:bg-green-700 disabled:bg-gray-400 transition"
              >
                {saving ? 'Guardando...' : 'COBRAR'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {selectedVariant && selectedVariant.selectingVariant && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-51">
          <div className="bg-white rounded-lg p-6 max-w-sm">
            <h3 className="text-lg font-bold mb-4">
              Selecciona tamaño: {selectedVariant.product.name}
            </h3>
            <div className="space-y-2 mb-4">
              {selectedVariant.product.variants.map((variant) => (
                <button
                  key={variant.id}
                  onClick={() =>
                    addToOrder(variant, selectedVariant.product)
                  }
                  className="w-full border-2 border-blue-500 bg-blue-50 text-blue-700 font-medium py-2 rounded hover:bg-blue-100 transition"
                >
                  {variant.name} - ${variant.price}
                </button>
              ))}
            </div>
            <button
              onClick={() => setSelectedVariant(null)}
              className="w-full border-2 border-gray-300 py-2 rounded hover:bg-gray-50"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default PosModal
