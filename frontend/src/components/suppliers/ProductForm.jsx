import React, { useState, useEffect } from 'react'
import { X } from 'lucide-react'

export default function ProductForm({ product, supplierId, onSubmit, onCancel, isLoading }) {
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    category: '',
    unit_of_measure: '',
    current_price: '',
    status: 'active'
  })

  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (product) {
      setFormData({
        name: product.name || '',
        sku: product.sku || '',
        category: product.category || '',
        unit_of_measure: product.unit_of_measure || '',
        current_price: product.current_price?.toString() || '',
        status: product.status || 'active'
      })
    }
  }, [product])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: null }))
    }
  }

  const validate = () => {
    const newErrors = {}
    
    if (!formData.name || formData.name.trim().length < 3) {
      newErrors.name = 'El nombre debe tener al menos 3 caracteres'
    }
    
    if (!formData.sku || formData.sku.trim().length < 2) {
      newErrors.sku = 'El SKU debe tener al menos 2 caracteres'
    }
    
    if (!/^[a-zA-Z0-9-]+$/.test(formData.sku)) {
      newErrors.sku = 'El SKU solo puede contener letras, números y guiones'
    }
    
    if (!formData.unit_of_measure || formData.unit_of_measure.trim().length === 0) {
      newErrors.unit_of_measure = 'La unidad de medida es requerida'
    }
    
    const price = parseFloat(formData.current_price)
    if (!formData.current_price || isNaN(price) || price <= 0) {
      newErrors.current_price = 'El precio debe ser mayor a 0'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (validate()) {
      const cleanedData = {
        supplier_id: supplierId,
        name: formData.name.trim(),
        sku: formData.sku.trim(),
        category: formData.category?.trim() || null,
        unit_of_measure: formData.unit_of_measure.trim(),
        current_price: parseFloat(formData.current_price),
        status: formData.status
      }
      onSubmit(cleanedData)
    }
  }

  const categories = [
    'Alimentos',
    'Bebidas',
    'Lácteos',
    'Carnes',
    'Verduras',
    'Frutas',
    'Panadería',
    'Limpieza',
    'Descartables',
    'Otros'
  ]

  const units = [
    'kg',
    'g',
    'L',
    'ml',
    'unidad',
    'caja',
    'paquete',
    'docena'
  ]

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">
            {product ? 'Editar Producto' : 'Nuevo Producto'}
          </h2>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nombre del Producto <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  errors.name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Ej: Aceite de Oliva 1L"
              />
              {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                SKU <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="sku"
                value={formData.sku}
                onChange={handleChange}
                required
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  errors.sku ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Ej: ACE-OLI-1L"
              />
              {errors.sku && <p className="text-red-500 text-sm mt-1">{errors.sku}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Categoría
              </label>
              <select
                name="category"
                value={formData.category}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Seleccionar categoría</option>
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Unidad de Medida <span className="text-red-500">*</span>
              </label>
              <select
                name="unit_of_measure"
                value={formData.unit_of_measure}
                onChange={handleChange}
                required
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  errors.unit_of_measure ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value="">Seleccionar unidad</option>
                {units.map(unit => (
                  <option key={unit} value={unit}>{unit}</option>
                ))}
              </select>
              {errors.unit_of_measure && <p className="text-red-500 text-sm mt-1">{errors.unit_of_measure}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Precio Actual <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <span className="absolute left-3 top-2 text-gray-500">$</span>
                <input
                  type="number"
                  name="current_price"
                  value={formData.current_price}
                  onChange={handleChange}
                  required
                  step="0.01"
                  min="0.01"
                  className={`w-full pl-8 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.current_price ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="0.00"
                />
              </div>
              {errors.current_price && <p className="text-red-500 text-sm mt-1">{errors.current_price}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Estado
              </label>
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="active">Activo</option>
                <option value="discontinued">Discontinuado</option>
                <option value="archived">Archivado</option>
              </select>
            </div>
          </div>

          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              disabled={isLoading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
              disabled={isLoading}
            >
              {isLoading ? 'Guardando...' : (product ? 'Actualizar' : 'Crear')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
