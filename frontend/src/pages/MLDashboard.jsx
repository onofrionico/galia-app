import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { 
  Brain, TrendingUp, AlertTriangle, Calendar, 
  CheckCircle, XCircle, Activity, BarChart3,
  RefreshCw, Zap, Clock, Target
} from 'lucide-react'
import api from '@/services/api'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

const MLDashboard = () => {
  const [selectedPeriod, setSelectedPeriod] = useState(30)

  // Fetch dashboard stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['ml-dashboard-stats'],
    queryFn: async () => {
      const response = await api.get('/ml/dashboard/stats')
      return response.data
    }
  })

  // Fetch accuracy metrics
  const { data: accuracy, isLoading: accuracyLoading } = useQuery({
    queryKey: ['ml-accuracy', selectedPeriod],
    queryFn: async () => {
      const response = await api.get('/ml/dashboard/accuracy', {
        params: { days: selectedPeriod }
      })
      return response.data
    }
  })

  // Fetch accuracy by hour
  const { data: byHour } = useQuery({
    queryKey: ['ml-accuracy-by-hour'],
    queryFn: async () => {
      const response = await api.get('/ml/dashboard/accuracy/by-hour')
      return response.data
    }
  })

  // Fetch accuracy by day
  const { data: byDay } = useQuery({
    queryKey: ['ml-accuracy-by-day'],
    queryFn: async () => {
      const response = await api.get('/ml/dashboard/accuracy/by-day')
      return response.data
    }
  })

  // Fetch alerts
  const { data: alerts } = useQuery({
    queryKey: ['ml-alerts'],
    queryFn: async () => {
      const response = await api.get('/ml/dashboard/alerts')
      return response.data
    }
  })

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-300'
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-300'
      default: return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getAccuracyColor = (mape) => {
    if (mape < 10) return 'text-green-600'
    if (mape < 20) return 'text-yellow-600'
    return 'text-red-600'
  }

  if (statsLoading || accuracyLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-purple-600 mx-auto mb-2" />
          <p className="text-gray-600">Cargando dashboard ML...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-3">
            <Brain className="h-8 w-8 text-purple-600" />
            <span>Dashboard ML</span>
          </h1>
          <p className="text-gray-600 mt-1">
            Monitoreo y precisión del modelo de predicción
          </p>
        </div>
        
        <select
          value={selectedPeriod}
          onChange={(e) => setSelectedPeriod(Number(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option value={7}>Últimos 7 días</option>
          <option value={30}>Últimos 30 días</option>
          <option value={90}>Últimos 90 días</option>
        </select>
      </div>

      {/* Model Info Card */}
      {stats?.model && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-4">
              <div className="bg-purple-600 rounded-lg p-3">
                <Zap className="h-6 w-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Modelo Activo</h3>
                <p className="text-sm text-gray-600">Versión {stats.model.version}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Entrenado: {format(new Date(stats.model.trained_at), 'dd/MM/yyyy HH:mm', { locale: es })}
                </p>
              </div>
            </div>
            
            <div className="text-right">
              <div className="flex items-center space-x-4">
                <div>
                  <p className="text-xs text-gray-600">Train Score</p>
                  <p className="text-lg font-bold text-green-600">{(stats.model.train_score * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Test Score</p>
                  <p className="text-lg font-bold text-green-600">{(stats.model.test_score * 100).toFixed(1)}%</p>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {stats.model.training_records} registros de entrenamiento
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Retrain Recommendation */}
      {stats?.retrain_recommendation && (
        <div className={`border rounded-lg p-6 ${
          stats.retrain_recommendation.should_retrain 
            ? 'bg-orange-50 border-orange-300' 
            : 'bg-green-50 border-green-300'
        }`}>
          <div className="flex items-start space-x-3">
            {stats.retrain_recommendation.should_retrain ? (
              <AlertTriangle className="h-6 w-6 text-orange-600 flex-shrink-0" />
            ) : (
              <CheckCircle className="h-6 w-6 text-green-600 flex-shrink-0" />
            )}
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 mb-2">
                {stats.retrain_recommendation.should_retrain 
                  ? '⚠️ Reentrenamiento Recomendado' 
                  : '✅ Modelo Estable'}
              </h3>
              <p className="text-sm text-gray-700 mb-3">
                {stats.retrain_recommendation.recommendation || stats.retrain_recommendation.reason || 'Sin información disponible'}
              </p>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">MAPE Reciente</p>
                  <p className="font-semibold">{stats.retrain_recommendation.recent_mape != null ? `${stats.retrain_recommendation.recent_mape}%` : '-'}</p>
                </div>
                <div>
                  <p className="text-gray-600">MAPE Histórico</p>
                  <p className="font-semibold">{stats.retrain_recommendation.historical_mape != null ? `${stats.retrain_recommendation.historical_mape}%` : '-'}</p>
                </div>
                <div>
                  <p className="text-gray-600">Degradación</p>
                  <p className={`font-semibold ${
                    stats.retrain_recommendation.degradation_percentage > 20 
                      ? 'text-red-600' 
                      : 'text-green-600'
                  }`}>
                    {stats.retrain_recommendation.degradation_percentage != null
                      ? `${stats.retrain_recommendation.degradation_percentage > 0 ? '+' : ''}${stats.retrain_recommendation.degradation_percentage}%`
                      : '-'
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Accuracy Metrics */}
      {accuracy?.success && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Precisión de Ventas</h3>
              <Target className="h-5 w-5 text-purple-600" />
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-xs text-gray-600">MAE (Error Absoluto Medio)</p>
                <p className="text-2xl font-bold text-gray-900">
                  {accuracy.sales_count.mae} ventas
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600">MAPE (Error Porcentual)</p>
                <p className={`text-2xl font-bold ${getAccuracyColor(accuracy.sales_count.mape)}`}>
                  {accuracy.sales_count.mape}%
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Precisión (±2 ventas)</p>
                <p className="text-2xl font-bold text-green-600">
                  {accuracy.sales_count.accuracy_within_2}%
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Precisión de Monto</h3>
              <TrendingUp className="h-5 w-5 text-green-600" />
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-xs text-gray-600">MAPE (Error Porcentual)</p>
                <p className={`text-2xl font-bold ${getAccuracyColor(accuracy.sales_amount.mape)}`}>
                  {accuracy.sales_amount.mape}%
                </p>
              </div>
              <p className="text-sm text-gray-600 mt-4">
                Error promedio en la predicción del monto de ventas
              </p>
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Precisión de Personal</h3>
              <Activity className="h-5 w-5 text-blue-600" />
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-xs text-gray-600">MAPE (Error Porcentual)</p>
                <p className={`text-2xl font-bold ${getAccuracyColor(accuracy.staff_count.mape)}`}>
                  {accuracy.staff_count.mape}%
                </p>
              </div>
              <p className="text-sm text-gray-600 mt-4">
                Error promedio en la recomendación de personal
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Accuracy by Hour */}
      {byHour?.success && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Precisión por Hora del Día</h3>
            <Clock className="h-5 w-5 text-purple-600" />
          </div>
          <div className="grid grid-cols-6 md:grid-cols-13 gap-2">
            {byHour.by_hour.map((item) => (
              <div
                key={item.hour}
                className="text-center p-2 rounded border border-gray-200 hover:shadow-md transition-shadow"
              >
                <p className="text-xs font-semibold text-gray-700">{item.hour}h</p>
                <p className={`text-sm font-bold ${getAccuracyColor(item.avg_error_percentage)}`}>
                  {item.avg_error_percentage}%
                </p>
                <p className="text-xs text-gray-500">n={item.sample_size}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Accuracy by Day of Week */}
      {byDay && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Precisión por Día de la Semana</h3>
            <Calendar className="h-5 w-5 text-purple-600" />
          </div>
          {byDay.success && Array.isArray(byDay.by_day) && byDay.by_day.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-7 gap-4">
              {byDay.by_day.map((item) => (
                <div
                  key={item.day_of_week}
                  className="text-center p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
                >
                  <p className="text-sm font-semibold text-gray-700 mb-2">{item.day_name}</p>
                  <p className={`text-2xl font-bold ${getAccuracyColor(item.avg_error_percentage)}`}>
                    {item.avg_error_percentage}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">n={item.sample_size}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center">
              <p className="text-sm text-gray-600">No hay datos de precisión disponibles todavía.</p>
            </div>
          )}
        </div>
      )}

      {/* Alerts Section */}
      {alerts?.success && alerts.total > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-orange-600" />
              <span>Alertas Activas ({alerts.total})</span>
            </h3>
          </div>
          <div className="space-y-3">
            {alerts.alerts.slice(0, 5).map((alert) => (
              <div
                key={alert.id}
                className={`border rounded-lg p-4 ${getSeverityColor(alert.severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-xs font-semibold uppercase">{alert.severity}</span>
                      <span className="text-xs text-gray-600">
                        {format(new Date(alert.date), 'dd/MM/yyyy')} - {alert.hour}:00
                      </span>
                    </div>
                    <p className="text-sm">
                      <strong>Recomendado:</strong> {alert.recommended_staff} personas
                      {' | '}
                      <strong>Programado:</strong> {alert.scheduled_staff} personas
                      {' | '}
                      <strong>Diferencia:</strong> {alert.difference > 0 ? '+' : ''}{alert.difference} 
                      ({alert.difference_percentage > 0 ? '+' : ''}{alert.difference_percentage.toFixed(1)}%)
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {alerts.total > 5 && (
            <p className="text-sm text-gray-600 mt-4 text-center">
              Y {alerts.total - 5} alertas más...
            </p>
          )}
        </div>
      )}

      {/* Info Footer */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <BarChart3 className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-gray-700">
            <p className="font-semibold mb-2">Sobre las métricas:</p>
            <ul className="space-y-1 text-xs">
              <li><strong>MAE:</strong> Error absoluto medio - cuántas ventas en promedio se desvía la predicción</li>
              <li><strong>MAPE:</strong> Error porcentual medio absoluto - porcentaje de error en las predicciones</li>
              <li><strong>Precisión (±2):</strong> Porcentaje de predicciones que están dentro de ±2 ventas del valor real</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MLDashboard
