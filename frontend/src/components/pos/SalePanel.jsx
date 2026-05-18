import { useState, useEffect } from 'react'
import { X, Plus, Minus, ShoppingCart } from 'lucide-react'
import GALIA from '../../constants/colors'
import salesService from '../../services/salesService'
import productsService from '../../services/productsService'
import productCategoriesService from '../../services/productCategoriesService'
import OpenSaleModal from './OpenSaleModal'
import ProductCatalog from './ProductCatalog'
import AddItemModalSale from './AddItemModalSale'
import DiscountModal from './DiscountModal'
import PaymentModal from './PaymentModal'

const SalePanel = ({ sale, isOpen, onClose, onSaleUpdated, onSaleClosed, onItemAdded }) => {
  if (!isOpen || !sale) return null

  const [saleState, setSaleState] = useState(sale)
  const [items, setItems] = useState(sale.items || [])
  const [categories, setCategories] = useState([])
  const [products, setProducts] = useState([])
  const [activeCategory, setActiveCategory] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [showAddItemModal, setShowAddItemModal] = useState(false)
  const [showDiscountModal, setShowDiscountModal] = useState(false)
  const [showPaymentModal, setShowPaymentModal] = useState(false)

  useEffect(() => {
    fetchProductData()
    // Refresh sale data
    setSaleState(sale)
    setItems(sale.items || [])
  }, [sale])

  const fetchProductData = async () => {
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
      setLoading(false)
    } catch (err) {
      setError('Error al cargar productos')
      setLoading(false)
    }
  }

  const calculateTotal = () => {
    let total = items.reduce((sum, item) => {
      const itemTotal = parseFloat(item.unit_price || 0) * item.quantity
      return sum + itemTotal
    }, 0)

    // Apply discount if exists
    if (saleState.descuento_monto) {
      total -= parseFloat(saleState.descuento_monto)
    }

    return Math.max(0, total)
  }

  const calculateRemaining = () => {
    return Math.max(0, calculateTotal() - parseFloat(saleState.total_paid || 0))
  }

  const handleRemoveItem = async (itemId) => {
    try {
      const updatedItems = items.filter(item => item.id !== itemId)
      setItems(updatedItems)
      setError('')
      // In a real app, you'd call an API to remove the item from the backend
      // For now, we just update local state
    } catch (err) {
      setError('Error al eliminar item')
    }
  }

  const handleAddProduct = async (product, variant) => {
    try {
      // In a real app, add item to sale in backend
      // This would be called from AddItemModal
      setError('')
    } catch (err) {
      setError('Error al agregar item')
    }
  }

  const handleDiscountApplied = async (discountData) => {
    try {
      const updated = await salesService.updateSale(sale.id, {
        descuento_tipo: discountData.tipo,
        descuento_valor: discountData.valor,
      })
      setSaleState(updated)
      setShowDiscountModal(false)
      setError('')
      onSaleUpdated?.(updated)
    } catch (err) {
      setError(err.response?.data?.error || 'Error al aplicar descuento')
    }
  }

  const handlePaymentRegistered = async (paymentData) => {
    try {
      const updated = await salesService.registerPayment(sale.id, paymentData)
      setSaleState(updated.sale)
      setShowPaymentModal(false)
      setError('')
      onSaleUpdated?.(updated.sale)
    } catch (err) {
      setError(err.response?.data?.error || 'Error al registrar pago')
    }
  }

  const handleCloseSale = async () => {
    try {
      const updated = await salesService.closeSale(sale.id)
      setSaleState(updated)
      setShowPaymentModal(false)
      onSaleUpdated?.(updated)
      onSaleClosed?.(updated)
      onClose()
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cerrar venta')
    }
  }

  const filteredProducts = activeCategory
    ? products.filter((p) => p.category_id === activeCategory && p.is_active)
    : products.filter((p) => p.is_active)

  const total = calculateTotal()
  const remaining = calculateRemaining()
  const isPaid = remaining <= 0
  const itemCount = items.length

  return (
    <div
      className="w-full flex flex-col lg:w-96 lg:border-l lg:flex-shrink-0 overflow-hidden"
      style={{ backgroundColor: GALIA.blanco, borderColor: GALIA.grisLigero }}
    >
      {/* Header */}
      <div className="px-3 md:px-6 py-3 md:py-4 flex items-center justify-between border-b" style={{ backgroundColor: GALIA.crema, borderColor: GALIA.grisLigero }}>
        <div className="min-w-0 flex-1">
          <h2 className="text-lg md:text-xl font-bold break-words" style={{ color: GALIA.marron }}>
            Venta #{saleState.id}
          </h2>
          <p className="text-xs" style={{ color: GALIA.grisClaro }}>
            Mesa: {saleState.mesa_id || 'N/A'} • {saleState.numero_personas || 1} persona(s)
          </p>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-gray-200 rounded flex-shrink-0 ml-2" title="Cerrar">
          <X size={20} md-size={24} style={{ color: GALIA.marron }} />
        </button>
      </div>

      {/* Error message */}
      {error && (
        <div className="px-3 md:px-4 py-2 bg-red-50 border-b border-red-200 text-red-700 text-xs md:text-sm">
          {error}
        </div>
      )}

      {/* Items List */}
      <div className="flex-1 overflow-y-auto px-3 md:px-4 py-2 md:py-3">
        {items && items.length > 0 ? (
          <div className="space-y-2">
            {items.map((item) => (
              <div
                key={item.id}
                className="rounded-lg p-3 border flex items-start justify-between hover:shadow-md transition-shadow"
                style={{ backgroundColor: GALIA.crema, borderColor: GALIA.grisLigero }}
              >
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-sm" style={{ color: GALIA.marron }}>
                    {item.product_name || 'Producto'}
                  </div>
                  <div className="text-xs mt-1" style={{ color: GALIA.grisClaro }}>
                    {item.variant_name && <div>{item.variant_name}</div>}
                    <div className="font-medium mt-1">
                      {item.quantity}x ${parseFloat(item.unit_price).toFixed(2)} = ${(item.unit_price * item.quantity).toFixed(2)}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleRemoveItem(item.id)}
                  className="ml-2 p-1 hover:bg-red-100 rounded transition-colors flex-shrink-0"
                  style={{ color: GALIA.grisClaro }}
                  title="Eliminar item"
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8" style={{ color: GALIA.grisClaro }}>
            <ShoppingCart size={32} className="mx-auto mb-2 opacity-50" />
            <p className="text-sm font-medium">Sin items</p>
            <p className="text-xs">Agrega productos</p>
          </div>
        )}
      </div>

      {/* Discount Section */}
      {saleState.descuento_monto && (
        <div className="px-3 md:px-4 py-2 border-t" style={{ borderColor: GALIA.grisLigero, backgroundColor: '#f9f5f0' }}>
          <div className="flex justify-between items-center text-xs md:text-sm">
            <span style={{ color: GALIA.grisClaro }}>
              Descuento {saleState.descuento_tipo === 'porcentaje' ? `(${saleState.descuento_valor}%)` : '(fijo)'}:
            </span>
            <span className="font-medium" style={{ color: GALIA.marron }}>
              -${parseFloat(saleState.descuento_monto).toFixed(2)}
            </span>
          </div>
        </div>
      )}

      {/* Payment Status */}
      {saleState.total_paid > 0 && (
        <div className="px-3 md:px-4 py-2 border-t" style={{ borderColor: GALIA.grisLigero, backgroundColor: '#f0fdf4' }}>
          <div className="flex justify-between items-center text-xs">
            <span style={{ color: GALIA.grisClaro }}>Pagado:</span>
            <span className="font-medium" style={{ color: GALIA.verde }}>
              ${parseFloat(saleState.total_paid).toFixed(2)}
            </span>
          </div>
          {remaining > 0 && (
            <div className="flex justify-between items-center text-xs mt-1">
              <span style={{ color: GALIA.grisClaro }}>Pendiente:</span>
              <span className="font-medium" style={{ color: '#DC2626' }}>
                ${remaining.toFixed(2)}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Total Section */}
      <div
        className="border-t px-3 md:px-4 py-3 md:py-4"
        style={{ borderColor: GALIA.grisLigero, backgroundColor: GALIA.crema }}
      >
        <div className="mb-2 md:mb-3">
          <p className="text-xs" style={{ color: GALIA.grisClaro }}>
            Total ({itemCount} items)
          </p>
          <div className="text-2xl md:text-3xl font-bold" style={{ color: GALIA.amarillo }}>
            ${total.toFixed(2)}
          </div>
        </div>

        {/* Buttons */}
        <div className="space-y-2">
          <button
            onClick={() => setShowAddItemModal(true)}
            className="w-full py-2 rounded font-semibold transition-opacity duration-200 flex items-center justify-center gap-2 text-sm md:text-base"
            style={{ backgroundColor: GALIA.amarillo, color: GALIA.marron }}
            onMouseEnter={(e) => (e.target.style.opacity = '0.9')}
            onMouseLeave={(e) => (e.target.style.opacity = '1')}
          >
            <Plus size={16} className="md:w-5 md:h-5" />
            Agregar Item
          </button>

          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => setShowDiscountModal(true)}
              className="py-2 rounded font-semibold transition-opacity duration-200 text-xs md:text-sm"
              style={{ backgroundColor: '#E3F2FD', color: '#1976D2' }}
              onMouseEnter={(e) => (e.target.style.opacity = '0.9')}
              onMouseLeave={(e) => (e.target.style.opacity = '1')}
            >
              Descuento
            </button>

            <button
              onClick={() => setShowPaymentModal(true)}
              disabled={itemCount === 0}
              className="py-2 rounded font-semibold transition-opacity duration-200 text-xs md:text-sm disabled:opacity-50"
              style={{ backgroundColor: GALIA.marron, color: 'white' }}
              onMouseEnter={(e) => !itemCount ? null : (e.target.style.opacity = '0.9')}
              onMouseLeave={(e) => !itemCount ? null : (e.target.style.opacity = '1')}
            >
              {isPaid ? 'Cerrar' : 'Cobrar'}
            </button>
          </div>
        </div>
      </div>

      {/* Modals */}
      <AddItemModalSale
        isOpen={showAddItemModal}
        saleId={saleState.id}
        onClose={() => setShowAddItemModal(false)}
        onItemAdded={(updatedSale) => {
          setSaleState(updatedSale)
          setItems(updatedSale.items || [])
          setShowAddItemModal(false)
          onSaleUpdated?.(updatedSale)
          onItemAdded?.(saleState.mesa_id)
        }}
      />

      <DiscountModal
        isOpen={showDiscountModal}
        total={total}
        currentDiscount={saleState.descuento_monto}
        onApply={handleDiscountApplied}
        onClose={() => setShowDiscountModal(false)}
      />

      <PaymentModal
        isOpen={showPaymentModal}
        saleId={saleState.id}
        total={total}
        paid={parseFloat(saleState.total_paid || 0)}
        onPaymentRegistered={handlePaymentRegistered}
        onCloseSale={handleCloseSale}
        onClose={() => setShowPaymentModal(false)}
      />
    </div>
  )
}

export default SalePanel
