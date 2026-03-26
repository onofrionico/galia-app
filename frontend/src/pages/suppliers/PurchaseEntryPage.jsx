import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft, Plus, Save, AlertCircle } from 'lucide-react'
import { useSuppliers } from '../../hooks/useSuppliers'
import { useProducts } from '../../hooks/useProducts'
import { usePurchases } from '../../hooks/usePurchases'
import PurchaseItemRow from '../../components/suppliers/PurchaseItemRow'
import PriceUpdateModal from '../../components/suppliers/PriceUpdateModal'

export default function PurchaseEntryPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const supplierId = searchParams.get('supplier_id')

  const [formData, setFormData] = useState({
    supplier_id: supplierId || '',
    purchase_date: new Date().toISOString().split('T')[0],
    currency: 'ARS',
    exchange_rate: '',
    invoice_number: '',
    cae_number: '',
    payment_status: 'pending',
    notes: ''
  })

  const { data: suppliersData } = useSuppliers()
  const suppliers = suppliersData?.suppliers || []
  const { products, fetchProductsBySupplier } = useProducts()
  const { createPurchase, updateProductPrices, loading } = usePurchases()

  const [items, setItems] = useState([
    { product_id: '', quantity: '', unit_price: '', notes: '' }
  ])

  const [errors, setErrors] = useState({})
  const [showPriceModal, setShowPriceModal] = useState(false)
  const [priceVariances, setPriceVariances] = useState([])
  const [pendingPurchase, setPendingPurchase] = useState(null)

  useEffect(() => {
    if (formData.supplier_id) {
      fetchProductsBySupplier(formData.supplier_id)
    }
  }, [formData.supplier_id, fetchProductsBySupplier])

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }))
    }
  }

  const handleItemUpdate = (index, itemData) => {
    const newItems = [...items]
    newItems[index] = itemData
    setItems(newItems)
  }

  const handleAddItem = () => {
    setItems([...items, { product_id: '', quantity: '', unit_price: '', notes: '' }])
  }

  const handleRemoveItem = (index) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index))
    }
  }

  const calculateTotal = () => {
    return items.reduce((sum, item) => {
      const qty = parseFloat(item.quantity) || 0
      const price = parseFloat(item.unit_price) || 0
      return sum + (qty * price)
    }, 0).toFixed(2)
  }

  const detectPriceVariances = () => {
    const variances = []
    
    items.forEach(item => {
      if (item.product_id && item.unit_price) {
        const product = products.find(p => p.id === parseInt(item.product_id))
        if (product) {
          const purchasePrice = parseFloat(item.unit_price)
          const catalogPrice = parseFloat(product.current_price)
          const variance = ((purchasePrice - catalogPrice) / catalogPrice) * 100
          
          if (Math.abs(variance) > 0.1) {
            variances.push({
              product_id: product.id,
              product_name: product.name,
              sku: product.sku,
              catalog_price: catalogPrice,
              purchase_price: purchasePrice,
              variance_percentage: variance
            })
          }
        }
      }
    })
    
    return variances
  }

  const validate = () => {
    const newErrors = {}
    
    if (!formData.supplier_id) {
      newErrors.supplier_id = 'Debe seleccionar un proveedor'
    }
    
    if (!formData.purchase_date) {
      newErrors.purchase_date = 'La fecha de compra es requerida'
    }
    
    const validItems = items.filter(item => 
      item.product_id && item.quantity && item.unit_price
    )
    
    if (validItems.length === 0) {
      newErrors.items = 'Debe agregar al menos un producto'
    }
    
    items.forEach((item, index) => {
      if (item.product_id || item.quantity || item.unit_price) {
        if (!item.product_id) {
          newErrors[`item_${index}_product`] = 'Producto requerido'
        }
        if (!item.quantity || parseFloat(item.quantity) <= 0) {
          newErrors[`item_${index}_quantity`] = 'Cantidad inválida'
        }
        if (!item.unit_price || parseFloat(item.unit_price) <= 0) {
          newErrors[`item_${index}_price`] = 'Precio inválido'
        }
      }
    })
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!validate()) {
      return
    }
    
    const variances = detectPriceVariances()
    
    const purchaseData = {
      ...formData,
      supplier_id: parseInt(formData.supplier_id),
      exchange_rate: formData.exchange_rate ? parseFloat(formData.exchange_rate) : null,
      items: items
        .filter(item => item.product_id && item.quantity && item.unit_price)
        .map(item => ({
          product_id: parseInt(item.product_id),
          quantity: parseFloat(item.quantity),
          unit_price: parseFloat(item.unit_price),
          notes: item.notes || null
        }))
    }
    
    if (variances.length > 0) {
      setPriceVariances(variances)
      setPendingPurchase(purchaseData)
      setShowPriceModal(true)
    } else {
      await savePurchase(purchaseData, [])
    }
  }

  const savePurchase = async (purchaseData, priceUpdates) => {
    try {
      const purchase = await createPurchase(purchaseData)
      
      if (priceUpdates.length > 0) {
        await updateProductPrices(purchase.id, priceUpdates)
      }
      
      alert('Compra registrada exitosamente')
      navigate('/suppliers')
    } catch (error) {
      alert(error.response?.data?.error || 'Error al guardar la compra')
    }
  }

  const handlePriceModalConfirm = async (priceUpdates) => {
    setShowPriceModal(false)
    await savePurchase(pendingPurchase, priceUpdates)
  }

  const handlePriceModalCancel = () => {
    setShowPriceModal(false)
    setPriceVariances([])
    setPendingPurchase(null)
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <button
          onClick={() => navigate('/suppliers')}
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Volver a Proveedores</span>
        </button>

        <h1 className="text-3xl font-bold text-gray-900">Nueva Compra</h1>
        <p className="text-gray-600 mt-1">Registrar una nueva compra de productos</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Información General</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Proveedor <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.supplier_id}
                onChange={(e) => handleChange('supplier_id', e.target.value)}
                required
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  errors.supplier_id ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="">Seleccionar proveedor</option>
                {suppliers.map(supplier => (
                  <option key={supplier.id} value={supplier.id}>
                    {supplier.name}
                  </option>
                ))}
              </select>
              {errors.supplier_id && <p className="text-red-500 text-sm mt-1">{errors.supplier_id}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Fecha de Compra <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                value={formData.purchase_date}
                onChange={(e) => handleChange('purchase_date', e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Número de Factura
              </label>
              <input
                type="text"
                value={formData.invoice_number}
                onChange={(e) => handleChange('invoice_number', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Ej: 0001-00001234"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Número CAE
              </label>
              <input
                type="text"
                value={formData.cae_number}
                onChange={(e) => handleChange('cae_number', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Código de Autorización Electrónico"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Moneda
              </label>
              <select
                value={formData.currency}
                onChange={(e) => handleChange('currency', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="ARS">ARS - Peso Argentino</option>
                <option value="USD">USD - Dólar</option>
                <option value="EUR">EUR - Euro</option>
                <option value="BRL">BRL - Real</option>
              </select>
            </div>

            {formData.currency !== 'ARS' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Cambio
                </label>
                <input
                  type="number"
                  value={formData.exchange_rate}
                  onChange={(e) => handleChange('exchange_rate', e.target.value)}
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Ej: 1000.00"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Estado de Pago
              </label>
              <select
                value={formData.payment_status}
                onChange={(e) => handleChange('payment_status', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="pending">Pendiente</option>
                <option value="partial">Parcial</option>
                <option value="paid">Pagado</option>
                <option value="cancelled">Cancelado</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notas
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => handleChange('notes', e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Notas adicionales sobre la compra"
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Productos</h2>
            <button
              type="button"
              onClick={handleAddItem}
              className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
              disabled={!formData.supplier_id}
            >
              <Plus className="w-4 h-4" />
              <span>Agregar Producto</span>
            </button>
          </div>

          {!formData.supplier_id && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <p className="text-yellow-800 text-sm">
                Selecciona un proveedor para agregar productos
              </p>
            </div>
          )}

          {errors.items && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-red-800 text-sm">{errors.items}</p>
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Producto</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cantidad</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Precio Unit.</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Notas</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Acciones</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {items.map((item, index) => (
                  <PurchaseItemRow
                    key={index}
                    item={item}
                    products={products}
                    onUpdate={handleItemUpdate}
                    onRemove={handleRemoveItem}
                    index={index}
                  />
                ))}
              </tbody>
              <tfoot className="bg-gray-50">
                <tr>
                  <td colSpan="3" className="px-4 py-3 text-right font-semibold text-gray-900">
                    Total:
                  </td>
                  <td className="px-4 py-3 font-bold text-lg text-gray-900">
                    ${calculateTotal()}
                  </td>
                  <td colSpan="2"></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => navigate('/suppliers')}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300 flex items-center justify-center gap-2"
            disabled={loading}
          >
            <Save className="w-4 h-4" />
            <span>{loading ? 'Guardando...' : 'Guardar Compra'}</span>
          </button>
        </div>
      </form>

      {showPriceModal && (
        <PriceUpdateModal
          priceVariances={priceVariances}
          onConfirm={handlePriceModalConfirm}
          onCancel={handlePriceModalCancel}
        />
      )}
    </div>
  )
}
