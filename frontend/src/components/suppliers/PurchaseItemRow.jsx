import React, { useState, useEffect } from 'react'
import { Trash2, AlertTriangle } from 'lucide-react'

export default function PurchaseItemRow({ 
  item, 
  products, 
  onUpdate, 
  onRemove, 
  index 
}) {
  const [formData, setFormData] = useState({
    product_id: item.product_id || '',
    quantity: item.quantity || '',
    unit_price: item.unit_price || '',
    notes: item.notes || ''
  })

  const [selectedProduct, setSelectedProduct] = useState(null)
  const [priceVariance, setPriceVariance] = useState(null)

  useEffect(() => {
    if (formData.product_id) {
      const product = products.find(p => p.id === parseInt(formData.product_id))
      setSelectedProduct(product)
      
      if (product && formData.unit_price) {
        const variance = ((parseFloat(formData.unit_price) - parseFloat(product.current_price)) / parseFloat(product.current_price)) * 100
        setPriceVariance(variance)
      } else {
        setPriceVariance(null)
      }
    } else {
      setSelectedProduct(null)
      setPriceVariance(null)
    }
  }, [formData.product_id, formData.unit_price, products])

  const handleChange = (field, value) => {
    const newData = { ...formData, [field]: value }
    setFormData(newData)
    onUpdate(index, newData)
  }

  const handleProductChange = (productId) => {
    const product = products.find(p => p.id === parseInt(productId))
    const newData = {
      ...formData,
      product_id: productId,
      unit_price: product ? product.current_price : ''
    }
    setFormData(newData)
    onUpdate(index, newData)
  }

  const calculateTotal = () => {
    const qty = parseFloat(formData.quantity) || 0
    const price = parseFloat(formData.unit_price) || 0
    return (qty * price).toFixed(2)
  }

  const hasSignificantVariance = priceVariance && Math.abs(priceVariance) > 5

  return (
    <tr className={hasSignificantVariance ? 'bg-yellow-50' : ''}>
      <td className="px-4 py-3">
        <select
          value={formData.product_id}
          onChange={(e) => handleProductChange(e.target.value)}
          required
          className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
        >
          <option value="">Seleccionar producto</option>
          {products.map(product => (
            <option key={product.id} value={product.id}>
              {product.name} ({product.sku})
            </option>
          ))}
        </select>
      </td>
      
      <td className="px-4 py-3">
        <input
          type="number"
          value={formData.quantity}
          onChange={(e) => handleChange('quantity', e.target.value)}
          required
          step="0.01"
          min="0.01"
          className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          placeholder="0.00"
        />
      </td>
      
      <td className="px-4 py-3">
        <div className="relative">
          <span className="absolute left-2 top-1 text-gray-500 text-sm">$</span>
          <input
            type="number"
            value={formData.unit_price}
            onChange={(e) => handleChange('unit_price', e.target.value)}
            required
            step="0.01"
            min="0.01"
            className={`w-full pl-6 pr-2 py-1 border rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm ${
              hasSignificantVariance ? 'border-yellow-500' : 'border-gray-300'
            }`}
            placeholder="0.00"
          />
          {hasSignificantVariance && (
            <div className="absolute right-2 top-1">
              <AlertTriangle className="w-4 h-4 text-yellow-600" title={`Variación: ${priceVariance.toFixed(1)}%`} />
            </div>
          )}
        </div>
        {selectedProduct && (
          <div className="text-xs text-gray-500 mt-1">
            Catálogo: ${parseFloat(selectedProduct.current_price).toFixed(2)}
          </div>
        )}
      </td>
      
      <td className="px-4 py-3">
        <div className="font-semibold text-gray-900 text-sm">
          ${calculateTotal()}
        </div>
      </td>
      
      <td className="px-4 py-3">
        <input
          type="text"
          value={formData.notes}
          onChange={(e) => handleChange('notes', e.target.value)}
          className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          placeholder="Notas opcionales"
        />
      </td>
      
      <td className="px-4 py-3 text-center">
        <button
          type="button"
          onClick={() => onRemove(index)}
          className="text-red-600 hover:text-red-900 transition-colors"
          title="Eliminar item"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </td>
    </tr>
  )
}
