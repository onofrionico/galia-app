import { useState, useEffect } from 'react'
import { X, Plus, Minus } from 'lucide-react'
import GALIA from '../../constants/colors'
import productCategoriesService from '../../services/productCategoriesService'
import productsService from '../../services/productsService'
import salesService from '../../services/salesService'

const AddItemModalSale = ({ isOpen, saleId, onClose, onItemAdded }) => {
  if (!isOpen) return null

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

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    document.addEventListener('keydown', handleEsc)
    return () => document.removeEventListener('keydown', handleEsc)
  }, [onClose])

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
      // For the SalePanel, we add items directly to the sale
      // The backend should have an endpoint to add items to a sale
      const updatedSale = await salesService.addItemToSale(saleId, {
        product_variant_id: selectedVariant.variant.id,
        quantity,
      })
      onItemAdded?.(updatedSale)
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center p-6 border-b" style={{ backgroundColor: GALIA.crema, borderColor: GALIA.grisLigero }}>
          <h2 className="text-2xl font-bold" style={{ color: GALIA.marron }}>
            Agregar Ítem a Venta
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
          <div className="bg-red-50 border-b border-red-200 text-red-700 px-6 py-3">
            {error}
          </div>
        )}

        <div className="flex-1 overflow-hidden flex flex-col gap-4 p-6">
          <div className="flex-1 flex flex-col min-w-0">
            <div className="flex gap-2 mb-4 pb-4 border-b overflow-x-auto" style={{ borderColor: GALIA.grisLigero }}>
              <button
                onClick={() => setActiveCategory(null)}
                className={`px-4 py-2 rounded whitespace-nowrap font-medium transition-colors text-sm`}
                style={{
                  backgroundColor: activeCategory === null ? GALIA.amarillo : GALIA.grisLigero,
                  color: activeCategory === null ? GALIA.marron : GALIA.grisClaro,
                }}
              >
                Todos
              </button>
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  className={`px-4 py-2 rounded whitespace-nowrap font-medium transition-colors text-sm`}
                  style={{
                    backgroundColor: activeCategory === cat.id ? GALIA.amarillo : GALIA.grisLigero,
                    color: activeCategory === cat.id ? GALIA.marron : GALIA.grisClaro,
                  }}
                >
                  {cat.icon || '📦'} {cat.name}
                </button>
              ))}
            </div>

            <div className="overflow-y-auto flex-1 min-h-0">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {filteredProducts.map((product) => (
                  <button
                    key={product.id}
                    onClick={() => handleAddProduct(product)}
                    className="border-2 rounded-lg p-4 hover:shadow-md transition-all text-center min-h-32 flex flex-col items-center justify-center"
                    style={{
                      borderColor: GALIA.grisLigero,
                      backgroundColor: GALIA.crema,
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = GALIA.amarillo
                      e.currentTarget.style.backgroundColor = GALIA.blanco
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = GALIA.grisLigero
                      e.currentTarget.style.backgroundColor = GALIA.crema
                    }}
                  >
                    <div className="text-3xl mb-2">📦</div>
                    <div className="font-bold text-sm leading-snug mb-2 line-clamp-2" style={{ color: GALIA.marron }}>
                      {product.name}
                    </div>
                    {product.variants && product.variants.length > 0 && (
                      <div className="text-xs font-semibold mt-1" style={{ color: GALIA.amarillo }}>
                        ${product.variants[0].price}
                        {product.variants.length > 1 && ` +${product.variants.length - 1}`}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="w-full flex flex-col pt-4 border-t" style={{ borderColor: GALIA.grisLigero }}>
            <h3 className="font-bold text-lg mb-3" style={{ color: GALIA.marron }}>
              Item a Agregar
            </h3>

            {selectedVariant && !selectedVariant.selectingVariant ? (
              <div className="flex-1 flex flex-col">
                <div className="rounded p-3 mb-4" style={{ backgroundColor: GALIA.crema, borderColor: GALIA.grisLigero }}>
                  <div className="font-medium text-sm mb-1" style={{ color: GALIA.marron }}>
                    {selectedVariant.product.name}
                  </div>
                  <div className="text-xs" style={{ color: GALIA.grisClaro }}>
                    {selectedVariant.variant.name} - ${selectedVariant.variant.price}
                  </div>

                  <div className="flex items-center gap-2 mt-3">
                    <button
                      onClick={() => handleQuantityChange(-1)}
                      className="p-1 hover:opacity-70 rounded transition-opacity"
                      style={{ color: GALIA.marron }}
                    >
                      <Minus size={16} />
                    </button>
                    <span className="w-8 text-center font-medium" style={{ color: GALIA.marron }}>
                      {quantity}
                    </span>
                    <button
                      onClick={() => handleQuantityChange(1)}
                      className="p-1 hover:opacity-70 rounded transition-opacity"
                      style={{ color: GALIA.marron }}
                    >
                      <Plus size={16} />
                    </button>
                  </div>

                  <div className="mt-3 pt-3 border-t" style={{ borderColor: GALIA.grisLigero }}>
                    <div className="font-bold text-sm" style={{ color: GALIA.amarillo }}>
                      Subtotal: ${(selectedVariant.variant.price * quantity).toFixed(2)}
                    </div>
                  </div>
                </div>

                <div className="space-y-2 mt-auto">
                  <button
                    onClick={handleAddItem}
                    disabled={saving}
                    className="w-full font-bold py-2 rounded transition-opacity"
                    style={{ backgroundColor: GALIA.verde, color: 'white' }}
                    onMouseEnter={(e) => (e.target.style.opacity = '0.9')}
                    onMouseLeave={(e) => (e.target.style.opacity = '1')}
                  >
                    {saving ? 'Agregando...' : 'Agregar'}
                  </button>
                  <button
                    onClick={() => {
                      setSelectedVariant(null)
                      setQuantity(1)
                      setError('')
                    }}
                    className="w-full border-2 py-2 rounded hover:opacity-70 transition-opacity"
                    style={{ borderColor: GALIA.grisLigero, color: GALIA.marron }}
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center flex-1 flex items-center justify-center" style={{ color: GALIA.grisClaro }}>
                <p className="text-sm font-medium">Selecciona un producto</p>
              </div>
            )}
          </div>
        </div>

        {selectedVariant && selectedVariant.selectingVariant && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-51">
            <div className="bg-white rounded-lg p-6 max-w-sm shadow-lg">
              <h3 className="text-lg font-bold mb-4" style={{ color: GALIA.marron }}>
                Selecciona tamaño: {selectedVariant.product.name}
              </h3>
              <div className="space-y-2 mb-4">
                {selectedVariant.product.variants.map((variant) => (
                  <button
                    key={variant.id}
                    onClick={() => handleSelectVariant(variant)}
                    className="w-full border-2 py-2 rounded font-medium transition-colors"
                    style={{
                      borderColor: GALIA.amarillo,
                      backgroundColor: GALIA.crema,
                      color: GALIA.marron,
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = GALIA.amarillo
                      e.currentTarget.style.color = GALIA.marron
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = GALIA.crema
                      e.currentTarget.style.color = GALIA.marron
                    }}
                  >
                    {variant.name} - ${variant.price}
                  </button>
                ))}
              </div>
              <button
                onClick={() => setSelectedVariant(null)}
                className="w-full border-2 py-2 rounded hover:opacity-70 transition-opacity"
                style={{ borderColor: GALIA.grisLigero, color: GALIA.marron }}
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

export default AddItemModalSale
