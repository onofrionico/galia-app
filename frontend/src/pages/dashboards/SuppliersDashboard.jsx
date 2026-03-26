import React, { useState } from 'react';
import { Calendar, Download, RefreshCw } from 'lucide-react';
import useDashboard from '../../hooks/useDashboard';
import MetricsCards from '../../components/dashboard/MetricsCards';
import TopSuppliersChart from '../../components/dashboard/TopSuppliersChart';
import SpendingDistributionChart from '../../components/dashboard/SpendingDistributionChart';
import SpendingTrendChart from '../../components/dashboard/SpendingTrendChart';

export default function SuppliersDashboard() {
  const [period, setPeriod] = useState('month');
  const [customDates, setCustomDates] = useState({
    start_date: '',
    end_date: '',
  });

  const params = period === 'custom' ? { period, ...customDates } : { period };
  const { data, isLoading, error, refetch } = useDashboard(params);

  const periods = [
    { value: 'today', label: 'Hoy' },
    { value: 'week', label: 'Esta Semana' },
    { value: 'month', label: 'Este Mes' },
    { value: 'quarter', label: 'Este Trimestre' },
    { value: 'year', label: 'Este Año' },
    { value: 'custom', label: 'Personalizado' },
  ];

  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Export dashboard data');
  };

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error al cargar el dashboard: {error.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard de Proveedores</h1>
          <p className="text-gray-600 mt-1">Análisis de compras y gastos por proveedor</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            <Download className="w-4 h-4" />
            Exportar
          </button>
        </div>
      </div>

      {/* Period Selector */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Período:</span>
          </div>
          <div className="flex gap-2 flex-wrap">
            {periods.map((p) => (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  period === p.value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
          {period === 'custom' && (
            <div className="flex items-center gap-2 ml-4">
              <input
                type="date"
                value={customDates.start_date}
                onChange={(e) => setCustomDates({ ...customDates, start_date: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
              <span className="text-gray-500">-</span>
              <input
                type="date"
                value={customDates.end_date}
                onChange={(e) => setCustomDates({ ...customDates, end_date: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
          )}
        </div>
        {data?.period && (
          <p className="text-sm text-gray-600 mt-2">
            Mostrando datos desde {new Date(data.period.start_date).toLocaleDateString('es-AR')} hasta{' '}
            {new Date(data.period.end_date).toLocaleDateString('es-AR')} ({data.period.days} días)
          </p>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-2" />
            <p className="text-gray-600">Cargando datos del dashboard...</p>
          </div>
        </div>
      )}

      {/* Dashboard Content */}
      {!isLoading && data && (
        <>
          {/* Metrics Cards */}
          <MetricsCards metrics={data.metrics} />

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Suppliers Chart */}
            <div className="lg:col-span-2">
              <TopSuppliersChart data={data.top_suppliers} />
            </div>

            {/* Spending Distribution */}
            <SpendingDistributionChart data={data.category_distribution} type="category" />

            {/* Payment Status Distribution */}
            <SpendingDistributionChart data={data.payment_status} type="status" />

            {/* Spending Trend */}
            <div className="lg:col-span-2">
              <SpendingTrendChart data={data.spending_trend} />
            </div>
          </div>

          {/* Summary Table */}
          {data.top_suppliers && data.top_suppliers.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Detalle de Proveedores</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Proveedor
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        CUIT
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Compras
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Total Gastado
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Promedio
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        % del Total
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {data.top_suppliers.map((supplier) => (
                      <tr key={supplier.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{supplier.name}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-500">{supplier.tax_id}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          <div className="text-sm text-gray-900">{supplier.purchase_count}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          <div className="text-sm font-medium text-gray-900">
                            ${supplier.total_spent.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          <div className="text-sm text-gray-900">
                            ${supplier.avg_order_value.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          <div className="text-sm font-medium text-blue-600">{supplier.percentage}%</div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
