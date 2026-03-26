import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Loader2, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { usePurchaseFrequency } from '../../hooks/useDashboard';
import FrequencyMetrics from '../../components/dashboard/FrequencyMetrics';
import FrequencyTimeline from '../../components/dashboard/FrequencyTimeline';

export default function PurchaseFrequencyDashboard() {
  const navigate = useNavigate();
  const [days, setDays] = useState(90);
  const [expandedSupplier, setExpandedSupplier] = useState(null);

  const { data, isLoading, error } = usePurchaseFrequency({ days });

  const handlePeriodChange = (newDays) => {
    setDays(newDays);
    setExpandedSupplier(null);
  };

  const toggleSupplier = (supplierId) => {
    setExpandedSupplier(expandedSupplier === supplierId ? null : supplierId);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-2" />
          <p className="text-gray-600">Cargando análisis de frecuencia...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 flex items-center gap-3">
          <AlertCircle className="w-6 h-6 text-red-600" />
          <div>
            <h3 className="font-semibold text-red-900">Error</h3>
            <p className="text-red-700">{error.message || 'Error al cargar los datos'}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Activity className="w-8 h-8 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">Análisis de Frecuencia de Compras</h1>
        </div>
        <p className="text-gray-600">
          Patrones de compra y detección de gaps por proveedor
        </p>
      </div>

      {/* Period Selector */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Período de Análisis
            </label>
            <div className="flex gap-2">
              {[30, 60, 90, 180, 365].map((period) => (
                <button
                  key={period}
                  onClick={() => handlePeriodChange(period)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    days === period
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {period} días
                </button>
              ))}
            </div>
          </div>
          {data && (
            <div className="text-right">
              <p className="text-sm text-gray-600">Total de Compras</p>
              <p className="text-2xl font-bold text-gray-900">{data.total_purchases}</p>
              <p className="text-xs text-gray-500">{data.total_suppliers} proveedores</p>
            </div>
          )}
        </div>
      </div>

      {/* Suppliers List */}
      {data && data.suppliers && data.suppliers.length > 0 ? (
        <div className="space-y-4">
          {data.suppliers.map((supplier) => (
            <div key={supplier.supplier_id} className="bg-white rounded-lg shadow overflow-hidden">
              {/* Supplier Header */}
              <div
                onClick={() => toggleSupplier(supplier.supplier_id)}
                className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {supplier.supplier_name}
                      </h3>
                      {supplier.current_gap && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                          Gap detectado
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-6 mt-2 text-sm text-gray-600">
                      <span>
                        <strong>{supplier.metrics.total_purchases}</strong> compras
                      </span>
                      <span>
                        Promedio: <strong>{supplier.metrics.avg_days_between}</strong> días
                      </span>
                      <span>
                        Regularidad: <strong>{supplier.metrics.regularity_score}%</strong>
                      </span>
                      {supplier.gaps.length > 0 && (
                        <span className="text-orange-600">
                          <strong>{supplier.gaps.length}</strong> gap(s)
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/suppliers/${supplier.supplier_id}`);
                      }}
                      className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Ver Proveedor
                    </button>
                    {expandedSupplier === supplier.supplier_id ? (
                      <ChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded Content */}
              {expandedSupplier === supplier.supplier_id && (
                <div className="border-t p-6 bg-gray-50">
                  <div className="space-y-6">
                    {/* Metrics Cards */}
                    <FrequencyMetrics 
                      metrics={supplier.metrics}
                      currentGap={supplier.current_gap}
                    />

                    {/* Timeline Chart */}
                    <FrequencyTimeline
                      timeline={supplier.timeline}
                      gaps={supplier.gaps}
                      avgDaysBetween={supplier.metrics.avg_days_between}
                    />

                    {/* Current Gap Alert */}
                    {supplier.current_gap && (
                      <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                        <div className="flex items-start gap-3">
                          <AlertCircle className="w-5 h-5 text-orange-600 mt-0.5" />
                          <div className="flex-1">
                            <h4 className="font-semibold text-orange-900 mb-1">
                              Gap Actual Detectado
                            </h4>
                            <p className="text-sm text-orange-800">
                              Han pasado <strong>{supplier.current_gap.days_since} días</strong> desde la última compra
                              ({new Date(supplier.current_gap.last_purchase_date).toLocaleDateString('es-AR')}).
                              El promedio esperado es de <strong>{supplier.current_gap.expected_days} días</strong>,
                              con un retraso de <strong>{supplier.current_gap.overdue_by} días</strong>.
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Period Summary */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
                      <div className="text-center">
                        <p className="text-xs text-gray-600">Primera Compra</p>
                        <p className="text-sm font-semibold text-gray-900">
                          {new Date(supplier.first_purchase_date).toLocaleDateString('es-AR')}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-gray-600">Última Compra</p>
                        <p className="text-sm font-semibold text-gray-900">
                          {new Date(supplier.last_purchase_date).toLocaleDateString('es-AR')}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-gray-600">Rango de Días</p>
                        <p className="text-sm font-semibold text-gray-900">
                          {supplier.metrics.min_days_between} - {supplier.metrics.max_days_between}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-gray-600">Compras/Mes</p>
                        <p className="text-sm font-semibold text-gray-900">
                          {supplier.metrics.purchases_per_month.toFixed(1)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Activity className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600">
            No hay datos de compras en el período seleccionado
          </p>
        </div>
      )}
    </div>
  );
}
