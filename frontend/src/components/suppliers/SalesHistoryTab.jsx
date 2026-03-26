import React, { useState, useEffect } from 'react'
import { Calendar, Download, TrendingUp, TrendingDown, DollarSign, ShoppingCart, Package } from 'lucide-react'
import suppliersApi from '../../services/api/suppliersApi'

export default function SalesHistoryTab({ supplierId }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [historyData, setHistoryData] = useState(null)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [comparePeriod, setComparePeriod] = useState(false)

  useEffect(() => {
    // Set default dates (last 30 days)
    const today = new Date()
    const thirtyDaysAgo = new Date(today)
    thirtyDaysAgo.setDate(today.getDate() - 30)
    
    setDateTo(today.toISOString().split('T')[0])
    setDateFrom(thirtyDaysAgo.toISOString().split('T')[0])
  }, [])

  useEffect(() => {
    if (dateFrom && dateTo) {
      fetchHistory()
    }
  }, [dateFrom, dateTo, comparePeriod, supplierId])

  const fetchHistory = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = {
        date_from: dateFrom,
        date_to: dateTo,
        compare_period: comparePeriod
      }
      const data = await suppliersApi.getSalesHistory(supplierId, params)
      setHistoryData(data)
    } catch (err) {
      setError(err.response?.data?.message || 'Error al cargar historial')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async () => {
    try {
      const params = {
        date_from: dateFrom,
        date_to: dateTo,
        format: 'csv'
      }
      const response = await suppliersApi.exportData(supplierId, params)
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `supplier_${supplierId}_purchases.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      alert('Error al exportar datos')
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS'
    }).format(value)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-AR')
  }

  const getChangeIcon = (percentage) => {
    if (percentage > 0) return <TrendingUp className="w-5 h-5 text-green-600" />
    if (percentage < 0) return <TrendingDown className="w-5 h-5 text-red-600" />
    return null
  }

  const getChangeColor = (percentage) => {
    if (percentage > 0) return 'text-green-600'
    if (percentage < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fecha Desde
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fecha Hasta
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex items-end">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={comparePeriod}
                onChange={(e) => setComparePeriod(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Comparar con período anterior</span>
            </label>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleExport}
              disabled={!historyData}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-300"
            >
              <Download className="w-4 h-4" />
              <span>Exportar CSV</span>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : historyData ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center gap-3 mb-2">
                <DollarSign className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">Total Gastado</h3>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(historyData.summary.total_amount)}
              </p>
              {historyData.comparison && (
                <div className={`flex items-center gap-1 mt-2 text-sm ${getChangeColor(historyData.comparison.changes.amount_change_percentage)}`}>
                  {getChangeIcon(historyData.comparison.changes.amount_change_percentage)}
                  <span>{historyData.comparison.changes.amount_change_percentage > 0 ? '+' : ''}{historyData.comparison.changes.amount_change_percentage}%</span>
                </div>
              )}
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center gap-3 mb-2">
                <ShoppingCart className="w-5 h-5 text-green-600" />
                <h3 className="font-semibold text-gray-900">Compras</h3>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {historyData.summary.total_purchases}
              </p>
              {historyData.comparison && (
                <div className={`flex items-center gap-1 mt-2 text-sm ${getChangeColor(historyData.comparison.changes.count_change_percentage)}`}>
                  {getChangeIcon(historyData.comparison.changes.count_change_percentage)}
                  <span>{historyData.comparison.changes.count_change_percentage > 0 ? '+' : ''}{historyData.comparison.changes.count_change_percentage}%</span>
                </div>
              )}
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center gap-3 mb-2">
                <Package className="w-5 h-5 text-purple-600" />
                <h3 className="font-semibold text-gray-900">Items</h3>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {historyData.summary.total_items}
              </p>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center gap-3 mb-2">
                <Calendar className="w-5 h-5 text-orange-600" />
                <h3 className="font-semibold text-gray-900">Promedio</h3>
              </div>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(historyData.summary.average_per_purchase)}
              </p>
              <p className="text-xs text-gray-500 mt-1">por compra</p>
            </div>
          </div>

          {/* Purchase List */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Historial de Compras</h3>
            </div>

            {historyData.purchases.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No hay compras en el período seleccionado
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Factura</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Moneda</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Items</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {historyData.purchases.map((purchase) => (
                      <tr key={purchase.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {formatDate(purchase.purchase_date)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {purchase.invoice_number || '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {purchase.currency}
                          {purchase.exchange_rate && (
                            <span className="text-xs text-gray-500 ml-1">
                              ({purchase.exchange_rate})
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm font-semibold text-gray-900">
                          {formatCurrency(purchase.total_amount)}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                            purchase.payment_status === 'paid' ? 'bg-green-100 text-green-800' :
                            purchase.payment_status === 'partial' ? 'bg-yellow-100 text-yellow-800' :
                            purchase.payment_status === 'cancelled' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {purchase.payment_status === 'paid' ? 'Pagado' :
                             purchase.payment_status === 'partial' ? 'Parcial' :
                             purchase.payment_status === 'cancelled' ? 'Cancelado' :
                             'Pendiente'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {purchase.items?.length || 0}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      ) : null}
    </div>
  )
}
