import { useState, useEffect, useRef } from 'react'
import { X, Plus, Minus } from 'lucide-react'
import productCategoriesService from '../../services/productCategoriesService'
import productsService from '../../services/productsService'
import ordersService from '../../services/ordersService'

const AddItemModal = ({ isOpen, orderId, onClose, onItemAdded }) => {
  const [categories, setCategories] = useState([])
  const [products, setProducts] = useState([])
  const [activeCategory, setActiveCategory] = useState(null)
  const [selectedVariant, setSelectedVariant] = useState(null)
  const [quantity, setQuantity] = useState(1)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const rightPanelRef = useRef(null)

  useEffect(() => {
    fetchData()
  }, [])

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    document.addEventListener('keydown', handleEsc)
    return () => document.removeEventListener('keydown', handleEsc)
  }, [onClose])

  useEffect(() => {
    // Auto-scroll right panel when a product is selected
    if (selectedVariant && !selectedVariant.selectingVariant && rightPanelRef.current) {
      rightPanelRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [selectedVariant])

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

  if (!isOpen) return null

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6">Cargando...</div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center p-6 border-b bg-gray-50">
          <h2 className="text-2xl font-bold">Agregar Ítem a Orden</h2>
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
          <div className="bg-red-50 border-b border-red-200 text-red-700 px-6 py-3">
            {error}
          </div>
        )}

        <div className="flex-1 overflow-hidden flex flex-col lg:flex-row gap-4 p-4 lg:p-6">
          {/* Products grid - takes more space on desktop */}
          <div className={`flex flex-col min-w-0 order-2 lg:order-1 min-h-0 ${
            selectedVariant ? 'flex-0' : 'flex-1'
          }`}>
            <div className="flex gap-2 mb-4 pb-4 border-b overflow-x-auto flex-nowrap flex-shrink-0">
              <button
                onClick={() => setActiveCategory(null)}
                className={`px-3 py-2 rounded whitespace-nowrap text-sm lg:text-base ${
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
                  className={`px-3 py-2 rounded whitespace-nowrap text-sm lg:text-base ${
                    activeCategory === cat.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700'
                  }`}
                >
                  {cat.icon} {cat.name}
                </button>
              ))}
            </div>

            <div className={`overflow-y-auto ${selectedVariant ? 'max-h-32' : 'flex-1'}`}>
              <div className="grid grid-cols-2 lg:grid-cols-2 gap-2 lg:gap-3 pr-2">
                {filteredProducts.map((product) => (
                  <button
                    key={product.id}
                    onClick={() => handleAddProduct(product)}
                    className="border-2 border-gray-300 rounded-lg p-2 lg:p-4 hover:border-blue-500 hover:bg-blue-50 transition text-center min-h-20 lg:min-h-32 flex flex-col items-center justify-center"
                  >
                    <div className="text-2xl lg:text-4xl mb-1 lg:mb-3">📦</div>
                    <div className="font-bold text-xs lg:text-base leading-snug mb-1 lg:mb-2 line-clamp-2">{product.name}</div>
                    {product.variants && product.variants.length > 0 && (
                      <div className="text-xs lg:text-sm text-gray-700 font-semibold mt-0 lg:mt-1">
                        ${product.variants[0].price}
                        {product.variants.length > 1 && ` +${product.variants.length - 1}`}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Right panel - smaller on mobile, fixed width on desktop */}
          <div
            ref={rightPanelRef}
            className={`w-full lg:w-64 lg:border-l lg:pl-4 flex flex-col order-1 lg:order-2 border-t lg:border-t-0 pt-4 lg:pt-0 lg:flex-shrink-0 ${
              selectedVariant ? 'flex-1 lg:flex-shrink-0 lg:max-h-none' : 'flex-shrink max-h-48'
            }`}
          >
            {/* Header - always visible */}
            <h3 className="font-bold text-lg mb-3 flex-shrink-0">Item a Agregar</h3>

            {selectedVariant && !selectedVariant.selectingVariant ? (
              <>
                {/* Content - scrolleable */}
                <div className="flex-1 overflow-y-auto min-h-0">
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
                </div>

                {/* Buttons - always visible at bottom */}
                <div className="space-y-2 flex-shrink-0 mt-3">
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
              </>
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
