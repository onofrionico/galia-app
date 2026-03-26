import React, { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, TrendingUp, Calendar } from 'lucide-react'
import { useExchangeRates } from '../../hooks/useConfiguration'

export default function ExchangeRateManager() {
  const { rates, loading, error, fetchLatestRates, createRate, updateRate, deleteRate } = useExchangeRates()
  const [showForm, setShowForm] = useState(false)
  const [editingRate, setEditingRate] = useState(null)
  const [formData, setFormData] = useState({
    from_currency: 'USD',
    to_currency: 'ARS',
    rate: '',
    effective_date: new Date().toISOString().split('T')[0],
    source: 'manual'
  })
  const [deleteConfirm, setDeleteConfirm] = useState(null)

  useEffect(() => {
    fetchLatestRates()
  }, [fetchLatestRates])

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    try {
      if (editingRate) {
        await updateRate(editingRate.id, { rate: parseFloat(formData.rate), source: formData.source })
        alert('Tipo de cambio actualizado exitosamente')
      } else {
        await createRate({
          ...formData,
          rate: parseFloat(formData.rate)
        })
        alert('Tipo de cambio creado exitosamente')
      }
      
      setShowForm(false)
      setEditingRate(null)
      setFormData({
        from_currency: 'USD',
        to_currency: 'ARS',
        rate: '',
        effective_date: new Date().toISOString().split('T')[0],
        source: 'manual'
      })
      fetchLatestRates()
    } catch (error) {
      alert(error.response?.data?.error || 'Error al guardar tipo de cambio')
    }
  }

  const handleEdit = (rate) => {
    setEditingRate(rate)
    setFormData({
      from_currency: rate.from_currency,
      to_currency: rate.to_currency,
      rate: rate.rate.toString(),
      effective_date: rate.effective_date,
      source: rate.source
    })
    setShowForm(true)
  }

  const handleDelete = async (rate) => {
    try {
      await deleteRate(rate.id)
      setDeleteConfirm(null)
      alert('Tipo de cambio eliminado exitosamente')
    } catch (error) {
      alert(error.response?.data?.error || 'Error al eliminar tipo de cambio')
    }
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingRate(null)
    setFormData({
      from_currency: 'USD',
      to_currency: 'ARS',
      rate: '',
      effective_date: new Date().toISOString().split('T')[0],
      source: 'manual'
    })
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-AR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 6
    }).format(value)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-AR')
  }

  const currencies = ['ARS', 'USD', 'EUR', 'BRL']

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-semibold text-gray-900">Tipos de Cambio</h3>
          <p className="text-sm text-gray-600 mt-1">Gestiona los tipos de cambio para conversiones de moneda</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
        >
          <Plus className="w-4 h-4" />
          <span>Agregar Tipo de Cambio</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                De <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.from_currency}
                onChange={(e) => setFormData(prev => ({ ...prev, from_currency: e.target.value }))}
                required
                disabled={!!editingRate}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              >
                {currencies.map(curr => (
                  <option key={curr} value={curr}>{curr}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                A <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.to_currency}
                onChange={(e) => setFormData(prev => ({ ...prev, to_currency: e.target.value }))}
                required
                disabled={!!editingRate}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              >
                {currencies.map(curr => (
                  <option key={curr} value={curr}>{curr}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tasa <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                value={formData.rate}
                onChange={(e) => setFormData(prev => ({ ...prev, rate: e.target.value }))}
                required
                step="0.000001"
                min="0.000001"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="0.00"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Fecha Efectiva <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                value={formData.effective_date}
                onChange={(e) => setFormData(prev => ({ ...prev, effective_date: e.target.value }))}
                required
                disabled={!!editingRate}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Fuente
              </label>
              <select
                value={formData.source}
                onChange={(e) => setFormData(prev => ({ ...prev, source: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="manual">Manual</option>
                <option value="api">API</option>
                <option value="import">Importación</option>
              </select>
            </div>
          </div>

          <div className="flex gap-2 mt-4">
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              disabled={loading}
            >
              {editingRate ? 'Actualizar' : 'Crear'}
            </button>
            <button
              type="button"
              onClick={handleCancel}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
          </div>
        </form>
      )}

      {loading && !showForm ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Par de Monedas</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tasa</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha Efectiva</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fuente</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {rates.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-4 py-8 text-center text-gray-500">
                    No hay tipos de cambio configurados
                  </td>
                </tr>
              ) : (
                rates.map((rate) => (
                  <tr key={rate.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-green-600" />
                        <span className="font-medium text-gray-900">
                          {rate.from_currency} → {rate.to_currency}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-semibold text-gray-900">{formatCurrency(rate.rate)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 text-gray-600">
                        <Calendar className="w-4 h-4" />
                        <span>{formatDate(rate.effective_date)}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                        {rate.source}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => handleEdit(rate)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          title="Editar"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setDeleteConfirm(rate)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded transition-colors"
                          title="Eliminar"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Confirmar Eliminación</h3>
            <p className="text-gray-600 mb-6">
              ¿Estás seguro de que deseas eliminar el tipo de cambio{' '}
              <strong>{deleteConfirm.from_currency}/{deleteConfirm.to_currency}</strong> del{' '}
              <strong>{formatDate(deleteConfirm.effective_date)}</strong>?
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
                Eliminar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
