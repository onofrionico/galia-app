import React, { useState, useEffect } from 'react'
import { X, Save, Loader2 } from 'lucide-react'
import suppliersApi from '../../services/api/suppliersApi'

export default function ProductForm({ product, onSave, onCancel, loading }) {
  const [suppliers, setSuppliers] = useState([])
  const [loadingSuppliers, setLoadingSuppliers] = useState(false)
  const [formData, setFormData] = useState({
    supplier_id: '',
    name: '',
    sku: '',
    category: '',
    unit_of_measure: '',
    current_price: '',
    status: 'active'
  })
  const [errors, setErrors] = useState({})

  useEffect(() => {
    fetchSuppliers()
    if (product) {
      setFormData({
        supplier_id: product.supplier_id || '',
        name: product.name || '',
        sku: product.sku || '',
        category: product.category || '',
        unit_of_measure: product.unit_of_measure || '',
        current_price: product.current_price || '',
        status: product.status || 'active'
      })
    }
  }, [product])

  const fetchSuppliers = async () => {
    setLoadingSuppliers(true)
    try {
      const data = await suppliersApi.getAll({ per_page: 1000 })
      setSuppliers(data.suppliers || [])
    } catch (err) {
      console.error('Error loading suppliers:', err)
    } finally {
      setLoadingSuppliers(false)
    }
  }

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }))
    }
  }

  const validate = () => {
    const newErrors = {}
    
    if (!formData.supplier_id) newErrors.supplier_id = 'Proveedor es requerido'
    if (!formData.name.trim()) newErrors.name = 'Nombre es requerido'
    if (!formData.sku.trim()) newErrors.sku = 'SKU es requerido'
    if (!formData.unit_of_measure.trim()) newErrors.unit_of_measure = 'Unidad de medida es requerida'
    if (!formData.current_price || parseFloat(formData.current_price) <= 0) {
      newErrors.current_price = 'Precio debe ser mayor a 0'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (validate()) {
      onSave({
        ...formData,
        supplier_id: parseInt(formData.supplier_id),
        current_price: parseFloat(formData.current_price)
      })
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">
            {product ? 'Editar Producto' : 'Nuevo Producto'}
          </h2>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Supplier */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Proveedor <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.supplier_id}
              onChange={(e) => handleChange('supplier_id', e.target.value)}
              disabled={loadingSuppliers || !!product}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.supplier_id ? 'border-red-500' : 'border-gray-300'
              } ${product ? 'bg-gray-100' : ''}`}
            >
              <option value="">Seleccionar proveedor</option>
              {suppliers.map(supplier => (
                <option key={supplier.id} value={supplier.id}>
                  {supplier.name}
                </option>
              ))}
            </select>
            {errors.supplier_id && (
              <p className="text-red-500 text-sm mt-1">{errors.supplier_id}</p>
            )}
          </div>

          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.name ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Nombre del producto"
            />
            {errors.name && (
              <p className="text-red-500 text-sm mt-1">{errors.name}</p>
            )}
          </div>

          {/* SKU */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              SKU <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.sku}
              onChange={(e) => handleChange('sku', e.target.value)}
              disabled={!!product}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.sku ? 'border-red-500' : 'border-gray-300'
              } ${product ? 'bg-gray-100' : ''}`}
              placeholder="Código SKU único"
            />
            {errors.sku && (
              <p className="text-red-500 text-sm mt-1">{errors.sku}</p>
            )}
          </div>

          {/* Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Categoría
            </label>
            <input
              type="text"
              value={formData.category}
              onChange={(e) => handleChange('category', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Categoría del producto"
            />
          </div>

          {/* Unit of Measure */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Unidad de Medida <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.unit_of_measure}
              onChange={(e) => handleChange('unit_of_measure', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.unit_of_measure ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="ej: kg, unidad, litro"
            />
            {errors.unit_of_measure && (
              <p className="text-red-500 text-sm mt-1">{errors.unit_of_measure}</p>
            )}
          </div>

          {/* Price */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Precio <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.current_price}
              onChange={(e) => handleChange('current_price', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.current_price ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="0.00"
            />
            {errors.current_price && (
              <p className="text-red-500 text-sm mt-1">{errors.current_price}</p>
            )}
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Estado
            </label>
            <select
              value={formData.status}
              onChange={(e) => handleChange('status', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="active">Activo</option>
              <option value="inactive">Inactivo</option>
              <option value="discontinued">Discontinuado</option>
            </select>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Guardando...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  Guardar
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
