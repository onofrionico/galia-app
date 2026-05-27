import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import { X, ChevronDown, Trash2, Printer } from 'lucide-react'
import GALIA from '../../constants/colors'
import productCategoriesService from '../../services/productCategoriesService'
import productsService from '../../services/productsService'
import salePrinting from '../../services/salePrinting'

const CamareroOrderBottomSheet = ({
  isOpen,
  order,
  mesaNumber,
  onClose,
  onAddItem,
  onRemoveItem,
  onCobrar
}) => {
  const [categories, setCategories] = useState([])
  const [products, setProducts] = useState([])
  const [activeCategory, setActiveCategory] = useState(null)
  const [showOrderItems, setShowOrderItems] = useState(true)
  const [loading, setLoading] = useState(false)
  const [printing, setPrinting] = useState(false)
  const [error, setError] = useState('')
  const [showPaymentMethod, setShowPaymentMethod] = useState(false)
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState(null)

  useEffect(() => {
    if (isOpen && order) {
      fetchCategoriesAndProducts()
    }
  }, [isOpen, order])

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    if (isOpen) {
      window.addEventListener('keydown', handleEscape)
      return () => window.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, onClose])

  const fetchCategoriesAndProducts = async () => {
    try {
      setLoading(true)
      setError('')
      const [catRes, prodRes] = await Promise.all([
        productCategoriesService.getCategories(),
        productsService.getProducts({ per_page: 100 })
      ])
      setCategories(catRes.product_categories || [])
      setProducts(prodRes.products || [])
      if (catRes.product_categories && catRes.product_categories.length > 0) {
        setActiveCategory(catRes.product_categories[0].id)
      }
    } catch (err) {
      console.error('Error fetching categories/products:', err)
      setError('Error al cargar productos')
    } finally {
      setLoading(false)
    }
  }

  const handlePrintControl = async () => {
    if (!order) return
    setPrinting(true)
    try {
      await salePrinting.printControl(order, order.items || [], order.total || 0, 0)
    } catch (err) {
      console.error('Error al imprimir control:', err)
    } finally {
      setPrinting(false)
    }
  }

  const handleProductVariantClick = async (variant) => {
    try {
      await onAddItem(variant.id, 1)
    } catch (err) {
      console.error('Error adding item:', err)
    }
  }

  const handleAgregarItem = () => {
    // Collapse order items to show products
    setShowOrderItems(false)
  }

  if (!isOpen || !order) return null

  const categoryProducts = products.filter(p => p.category_id === activeCategory)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-40 flex items-end" onClick={onClose}>
      {/* BottomSheet - Dynamic height based on content */}
      <div className="w-screen bg-white rounded-t-lg flex flex-col" style={{ maxHeight: 'min(90vh, 100vh - 60px)' }} onClick={(e) => e.stopPropagation()}>

        {/* Header - Sticky */}
        <div className="sticky top-0 z-10 px-4 py-3 shadow-sm border-b flex items-center justify-between" style={{ backgroundColor: GALIA.marron, borderColor: GALIA.grisLigero }}>
          <button
            onClick={onClose}
            className="flex items-center gap-2 text-white hover:opacity-80"
          >
            <X className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Mesa {mesaNumber}</h2>
          </button>
          <div className="text-right">
            <div className="text-xs text-white opacity-80">Total</div>
            <div className="text-xl font-bold" style={{ color: GALIA.amarillo }}>
              ${parseFloat(order.total || 0).toFixed(2)}
            </div>
          </div>
        </div>

        {/* Categories tabs - Sticky */}
        <div className="sticky top-0 z-9 flex gap-2 px-3 py-2 overflow-x-auto" style={{ backgroundColor: GALIA.blanco, borderBottom: `1px solid ${GALIA.grisLigero}` }}>
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className="px-4 py-2 whitespace-nowrap text-sm rounded-full border transition"
              style={{
                backgroundColor: activeCategory === cat.id ? GALIA.amarillo : 'transparent',
                color: GALIA.marron,
                borderColor: activeCategory === cat.id ? GALIA.amarillo : GALIA.grisLigero
              }}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Products grid - Scrollable, flex-1 to fill available space */}
        <div className="flex-1 overflow-y-auto px-3 py-3">
          {error && (
            <div className="p-3 text-sm text-center" style={{ backgroundColor: '#fee', color: '#c33' }}>
              {error}
            </div>
          )}
          {loading ? (
            <div className="text-center py-8" style={{ color: GALIA.grisClaro }}>
              Cargando productos...
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              {categoryProducts.map(product => (
                <div key={product.id} className="rounded-lg overflow-hidden" style={{ backgroundColor: GALIA.blanco }}>
                  {product.variants && product.variants.length > 0 ? (
                    <div className="space-y-1">
                      {product.variants.map(variant => (
                        <button
                          key={variant.id}
                          onClick={() => handleProductVariantClick(variant)}
                          className="w-full text-left p-2 transition hover:bg-gray-50"
                          style={{ backgroundColor: GALIA.blanco, borderBottom: `1px solid ${GALIA.grisLigero}` }}
                        >
                          <div className="font-semibold text-sm" style={{ color: GALIA.marron }}>
                            {product.name}
                          </div>
                          <div className="text-xs" style={{ color: GALIA.grisClaro }}>
                            {variant.name}
                          </div>
                          <div className="text-sm font-bold" style={{ color: GALIA.amarillo }}>
                            ${parseFloat(variant.price).toFixed(2)}
                          </div>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <button className="w-full p-2 text-center">
                      <div className="font-medium" style={{ color: GALIA.marron }}>
                        {product.name}
                      </div>
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Order items section - Always visible at bottom */}
        <div className="border-t" style={{ borderColor: GALIA.grisLigero, backgroundColor: GALIA.blanco }}>

          {/* Order header */}
          <div className="sticky top-0 px-4 py-2 flex items-center justify-between border-b" style={{ backgroundColor: GALIA.crema, borderColor: GALIA.grisLigero }}>
            <span className="font-semibold" style={{ color: GALIA.marron }}>
              Orden ({order.items?.length || 0} ítems)
            </span>
          </div>

          {/* Order items - Always visible, scrollable if needed */}
          <div className="px-4 py-2 space-y-2 max-h-40 overflow-y-auto">
            {order.items && order.items.length > 0 ? (
              order.items.map(item => (
                <div
                  key={item.id}
                  className="flex justify-between items-center py-1"
                  style={{ borderBottom: `1px solid ${GALIA.grisLigero}` }}
                >
                  <div className="flex-1">
                    <div className="text-sm font-medium" style={{ color: GALIA.marron }}>
                      {item.product_name}
                    </div>
                    <div className="text-xs" style={{ color: GALIA.grisClaro }}>
                      {item.variant_name}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-sm" style={{ color: GALIA.marron }}>
                      {item.quantity}x ${parseFloat(item.unit_price).toFixed(2)}
                    </div>
                    <button
                      onClick={() => onRemoveItem(item.id)}
                      className="p-1 rounded transition hover:bg-red-50"
                      style={{ color: '#dc2626' }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-4" style={{ color: GALIA.grisClaro }}>
                Sin items
              </div>
            )}
          </div>

          {/* Action buttons - Always visible */}
          <div className="px-4 py-3 space-y-2" style={{ borderTop: `1px solid ${GALIA.grisLigero}` }}>
            <button
              onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
              className="w-full py-2 rounded font-semibold transition-opacity text-sm hover:opacity-90"
              style={{ backgroundColor: GALIA.amarillo, color: GALIA.marron }}
            >
              Agregar Item
            </button>
            <button
              onClick={handlePrintControl}
              disabled={!order.items || order.items.length === 0 || printing}
              className="w-full py-2 rounded font-semibold transition-opacity text-sm flex items-center justify-center gap-2 disabled:opacity-50 hover:opacity-90 disabled:hover:opacity-50"
              style={{ backgroundColor: '#3B82F6', color: 'white' }}
            >
              <Printer size={16} />
              {printing ? 'Imprimiendo...' : 'Control Mesa'}
            </button>
            <button
              onClick={() => setShowPaymentMethod(true)}
              disabled={!order.items || order.items.length === 0}
              className="w-full py-3 font-bold rounded-lg transition text-base disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 disabled:hover:opacity-50"
              style={{ backgroundColor: GALIA.marron, color: 'white' }}
            >
              COBRAR
            </button>
          </div>
        </div>
      </div>

      {/* Payment Method Selection Modal */}
      {showPaymentMethod && (
        <>
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-50"
            onClick={() => setShowPaymentMethod(false)}
          />
          <div
            className="fixed bottom-0 left-0 right-0 z-50 rounded-t-xl flex flex-col"
            style={{ backgroundColor: GALIA.blanco, maxHeight: '60vh' }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div
              className="flex items-center justify-between px-4 py-3"
              style={{ backgroundColor: GALIA.marron }}
            >
              <h2 className="text-white text-lg font-semibold">Método de Pago</h2>
              <button
                onClick={() => setShowPaymentMethod(false)}
                className="p-1 text-white hover:opacity-80"
              >
                <X size={20} />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
              {/* Total Display */}
              <div className="mb-4">
                <p className="text-sm" style={{ color: GALIA.grisClaro }}>
                  Total a pagar:
                </p>
                <p className="text-3xl font-bold" style={{ color: GALIA.amarillo }}>
                  ${parseFloat(order.total || 0).toFixed(2)}
                </p>
              </div>

              {/* Method Selection */}
              <div className="grid grid-cols-3 gap-2">
                {['Efectivo', 'Tarjeta', 'Otro'].map((metodo) => (
                  <button
                    key={metodo}
                    onClick={() => setSelectedPaymentMethod(metodo)}
                    className="py-3 rounded border-2 font-semibold transition-colors duration-200"
                    style={{
                      borderColor:
                        selectedPaymentMethod === metodo ? GALIA.amarillo : GALIA.grisLigero,
                      backgroundColor:
                        selectedPaymentMethod === metodo ? GALIA.amarillo : 'transparent',
                      color: GALIA.marron,
                    }}
                  >
                    {metodo.charAt(0).toUpperCase() + metodo.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Confirm Button */}
            <div className="px-4 py-4 border-t" style={{ borderColor: GALIA.grisLigero }}>
              <button
                onClick={() => {
                  if (selectedPaymentMethod && onCobrar) {
                    onCobrar(selectedPaymentMethod)
                    setShowPaymentMethod(false)
                    setSelectedPaymentMethod(null)
                  }
                }}
                disabled={!selectedPaymentMethod}
                className="w-full py-3 rounded font-bold text-lg transition-opacity duration-200"
                style={{
                  backgroundColor: selectedPaymentMethod ? GALIA.marron : GALIA.grisLigero,
                  color: 'white',
                  opacity: selectedPaymentMethod ? 1 : 0.6,
                  cursor: selectedPaymentMethod ? 'pointer' : 'not-allowed',
                }}
              >
                Confirmar
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

CamareroOrderBottomSheet.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  order: PropTypes.shape({
    id: PropTypes.number.isRequired,
    items: PropTypes.arrayOf(PropTypes.shape({
      id: PropTypes.number.isRequired,
      product_name: PropTypes.string.isRequired,
      variant_name: PropTypes.string,
      quantity: PropTypes.number.isRequired,
      unit_price: PropTypes.number.isRequired
    })),
    total: PropTypes.number
  }),
  mesaNumber: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  onClose: PropTypes.func.isRequired,
  onAddItem: PropTypes.func.isRequired,
  onRemoveItem: PropTypes.func.isRequired,
  onCobrar: PropTypes.func.isRequired
}

export default CamareroOrderBottomSheet
