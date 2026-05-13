import { useState, useEffect } from 'react'
import { X, Plus, Minus } from 'lucide-react'
import productCategoriesService from '../../services/productCategoriesService'
import productsService from '../../services/productsService'
import ordersService from '../../services/ordersService'

const AddItemModal = ({ orderId, onClose, onItemAdded }) => {
  const [categories, setCategories] = useState([])
  const [products, setProducts] = useState([])
  const [activeCategory, setActiveCategory] = useState(null)
  const [selectedVariant, setSelectedVariant] = useState(null)
  const [quantity, setQuantity] = useState(1)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

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

    setSelectedVariant({ product, variant, selectingVariant: false })
  }

  const handleQuantityChange = (delta) => {
    setQuantity(Math.max(1, quantity + delta))
  }

  const handleAddItem = async () => {
    if (!selectedVariant?.variant || quantity <= 0) {
      setError('Selecciona un producto y cantidad válida')
      return
    }

    setSaving(true)
    try {
      const updatedOrder = await ordersService.addItem(orderId, {
        product_variant_id: selectedVariant.variant.id,
        quantity,
      })
      onItemAdded?.(updatedOrder)
    } catch (err) {
      setError(err.response?.data?.error || 'Error al agregar item')
    } finally {
      setSaving(false)
    }
  }

  const handleSelectVariant = (variant) => {
    setSelectedVariant({ product: selectedVariant.product, variant, selectingVariant: false })
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
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold">Agregar Ítem a Orden</h2>
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
              <div className="grid grid-cols-2 gap-3">
                {filteredProducts.map((product) => (
                  <button
                    key={product.id}
                    onClick={() => handleAddProduct(product)}
                    className="border-2 border-gray-300 rounded-lg p-4 hover:border-blue-500 hover:bg-blue-50 transition text-center min-h-32 flex flex-col items-center justify-center"
                  >
                    <div className="text-4xl mb-3">📦</div>
                    <div className="font-bold text-base leading-snug mb-2 line-clamp-2">{product.name}</div>
                    {product.variants && product.variants.length > 0 && (
                      <div className="text-sm text-gray-700 font-semibold mt-1">
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
            <h3 className="font-bold text-lg mb-3">Item a Agregar</h3>

            {selectedVariant && !selectedVariant.selectingVariant ? (
              <div className="flex-1 flex flex-col">
                <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-4">
                  <div className="font-medium text-sm mb-1">
                    {selectedVariant.product.name}
                  </div>
                  <div className="text-xs text-gray-600 mb-2">
                    {selectedVariant.variant.name} - ${selectedVariant.variant.price}
                  </div>

                  <div className="flex items-center gap-2 mt-3">
                    <button
                      onClick={() => handleQuantityChange(-1)}
                      className="p-1 hover:bg-blue-100 rounded"
                    >
                      <Minus size={16} />
                    </button>
                    <span className="w-8 text-center font-medium">{quantity}</span>
                    <button
                      onClick={() => handleQuantityChange(1)}
                      className="p-1 hover:bg-blue-100 rounded"
                    >
                      <Plus size={16} />
                    </button>
                  </div>

                  <div className="mt-3 pt-3 border-t border-blue-200">
                    <div className="font-bold text-sm">
                      Subtotal: ${(selectedVariant.variant.price * quantity).toFixed(2)}
                    </div>
                  </div>
                </div>

                <div className="space-y-2 mt-auto">
                  <button
                    onClick={handleAddItem}
                    disabled={saving}
                    className="w-full bg-green-600 text-white font-bold py-2 rounded hover:bg-green-700 disabled:bg-gray-400 transition"
                  >
                    {saving ? 'Agregando...' : 'Agregar'}
                  </button>
                  <button
                    onClick={() => {
                      setSelectedVariant(null)
                      setQuantity(1)
                      setError('')
                    }}
                    className="w-full border-2 border-gray-300 py-2 rounded hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 flex-1 flex items-center justify-center">
                Selecciona un producto
              </div>
            )}
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
                    onClick={() => handleSelectVariant(variant)}
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
    </div>
  )
}

export default AddItemModal
