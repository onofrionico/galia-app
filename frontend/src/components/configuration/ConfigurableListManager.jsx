import React, { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Check, X, GripVertical } from 'lucide-react'
import { useConfigurableList } from '../../hooks/useConfiguration'

export default function ConfigurableListManager({ listType, title, description }) {
  const { items, loading, error, fetchItems, createItem, updateItem, deactivateItem } = useConfigurableList(listType)
  const [showForm, setShowForm] = useState(false)
  const [editingItem, setEditingItem] = useState(null)
  const [formData, setFormData] = useState({ value: '', display_order: 0 })
  const [deleteConfirm, setDeleteConfirm] = useState(null)

  useEffect(() => {
    fetchItems(false)
  }, [fetchItems])

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      if (editingItem) {
        await updateItem(editingItem.id, formData)
        alert('Item actualizado exitosamente')
      } else {
        await createItem(formData)
        alert('Item creado exitosamente')
      }
      
      setShowForm(false)
      setEditingItem(null)
      setFormData({ value: '', display_order: 0 })
    } catch (error) {
      alert(error.response?.data?.error || 'Error al guardar item')
    }
  }

  const handleEdit = (item) => {
    setEditingItem(item)
    setFormData({
      value: item.value,
      display_order: item.display_order
    })
    setShowForm(true)
  }

  const handleDelete = async (item) => {
    try {
      await deactivateItem(item.id)
      setDeleteConfirm(null)
      alert('Item desactivado exitosamente')
    } catch (error) {
      alert(error.response?.data?.error || 'Error al desactivar item')
    }
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingItem(null)
    setFormData({ value: '', display_order: 0 })
  }

  const handleAddNew = () => {
    setEditingItem(null)
    setFormData({ value: '', display_order: items.length })
    setShowForm(true)
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-semibold text-gray-900">{title}</h3>
          {description && <p className="text-sm text-gray-600 mt-1">{description}</p>}
        </div>
        <button
          onClick={handleAddNew}
          className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          <Plus className="w-4 h-4" />
          <span>Agregar</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Valor <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.value}
                onChange={(e) => setFormData(prev => ({ ...prev, value: e.target.value }))}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Ej: Alimentos"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Orden
              </label>
              <input
                type="number"
                value={formData.display_order}
                onChange={(e) => setFormData(prev => ({ ...prev, display_order: parseInt(e.target.value) }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex gap-2 mt-4">
            <button
              type="submit"
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              disabled={loading}
            >
              <Check className="w-4 h-4" />
              <span>{editingItem ? 'Actualizar' : 'Crear'}</span>
            </button>
            <button
              type="button"
              onClick={handleCancel}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <X className="w-4 h-4" />
              <span>Cancelar</span>
            </button>
          </div>
        </form>
      )}

      {loading && !showForm ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="space-y-2">
          {items.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No hay items configurados</p>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className={`flex items-center justify-between p-3 border rounded-lg ${
                  item.is_active ? 'border-gray-200 bg-white' : 'border-gray-200 bg-gray-50 opacity-60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <GripVertical className="w-4 h-4 text-gray-400" />
                  <div>
                    <span className="font-medium text-gray-900">{item.value}</span>
                    {!item.is_active && (
                      <span className="ml-2 text-xs text-gray-500">(Inactivo)</span>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">Orden: {item.display_order}</span>
                  <button
                    onClick={() => handleEdit(item)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                    title="Editar"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  {item.is_active && (
                    <button
                      onClick={() => setDeleteConfirm(item)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                      title="Desactivar"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Confirmar Desactivación</h3>
            <p className="text-gray-600 mb-6">
              ¿Estás seguro de que deseas desactivar <strong>{deleteConfirm.value}</strong>?
              Los items desactivados no aparecerán en los formularios pero se mantendrán en registros existentes.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm)}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Desactivar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
