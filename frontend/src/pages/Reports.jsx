import { useState, useEffect } from 'react'
import { 
  TrendingUp, TrendingDown, DollarSign, ShoppingCart, Receipt, 
  Users, Target, Settings, Calendar, RefreshCw, ChevronDown,
  AlertTriangle, CheckCircle, Clock, BarChart3, PieChart, Scale
} from 'lucide-react'
import { reportsService } from '@/services/reportsService'

const Reports = () => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dashboard, setDashboard] = useState(null)
  const [filterMode, setFilterMode] = useState('period') // 'period' o 'range'
  const [period, setPeriod] = useState('mensual')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [showGoalsModal, setShowGoalsModal] = useState(false)
  const [goals, setGoals] = useState([])
  const [activeTab, setActiveTab] = useState('dashboard')

  useEffect(() => {
    if (filterMode === 'period') {
      loadDashboard()
    }
  }, [period, filterMode])

  const loadDashboard = async () => {
    try {
      setLoading(true)
      setError(null)
      let data
      if (filterMode === 'range' && startDate && endDate) {
        data = await reportsService.getDashboard(null, null, startDate, endDate)
      } else {
        data = await reportsService.getDashboard(period)
      }
      setDashboard(data)
    } catch (err) {
      console.error('Error loading dashboard:', err)
      setError('Error al cargar el dashboard')
    } finally {
      setLoading(false)
    }
  }

  const handleApplyDateRange = () => {
    if (startDate && endDate) {
      loadDashboard()
    }
  }

  const loadGoals = async () => {
    try {
      const data = await reportsService.getGoals()
      setGoals(data)
    } catch (err) {
      console.error('Error loading goals:', err)
    }
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  const formatPercent = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
  }

  const VariationBadge = ({ value }) => {
    const isPositive = value >= 0
    return (
      <span className={`inline-flex items-center gap-1 text-xs font-medium ${
        isPositive ? 'text-green-600' : 'text-red-600'
      }`}>
        {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
        {formatPercent(value)}
      </span>
    )
  }

  const GoalProgress = ({ goal }) => {
    const progressColor = goal.on_track ? 'bg-green-500' : 'bg-amber-500'
    const bgColor = goal.on_track ? 'bg-green-100' : 'bg-amber-100'
    
    const getGoalLabel = (type) => {
      const labels = {
        'ventas': 'Ventas',
        'rentabilidad': 'Rentabilidad',
        'productividad': 'Productividad',
        'gastos_directos': 'Gastos Directos',
        'gastos_indirectos': 'Gastos Indirectos',
        'costo_laboral': 'Costo Laboral'
      }
      return labels[type] || type
    }

    const formatValue = (value, unit) => {
      if (unit === 'monto') return formatCurrency(value)
      if (unit === 'porcentaje') return `${value.toFixed(1)}%`
      return value.toFixed(2)
    }

    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">{getGoalLabel(goal.type)}</span>
          {goal.on_track ? (
            <CheckCircle size={16} className="text-green-500" />
          ) : (
            <AlertTriangle size={16} className="text-amber-500" />
          )}
        </div>
        <div className="flex items-end justify-between mb-2">
          <span className="text-lg font-bold text-gray-900">
            {formatValue(goal.current_value, goal.target_unit)}
          </span>
          <span className="text-xs text-gray-500">
            Meta: {formatValue(goal.target_value, goal.target_unit)}
          </span>
        </div>
        <div className={`w-full h-2 rounded-full ${bgColor}`}>
          <div 
            className={`h-full rounded-full ${progressColor} transition-all duration-500`}
            style={{ width: `${Math.min(goal.progress, 100)}%` }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-1">{goal.progress.toFixed(0)}% completado</p>
      </div>
    )
  }

  const KPICard = ({ title, value, subtitle, variation, icon: Icon, color }) => {
    const colorClasses = {
      blue: 'bg-blue-50 text-blue-600',
      green: 'bg-green-50 text-green-600',
      purple: 'bg-purple-50 text-purple-600',
      amber: 'bg-amber-50 text-amber-600',
      red: 'bg-red-50 text-red-600'
    }

    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 md:p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm text-gray-500 mb-1">{title}</p>
            <p className="text-xl md:text-2xl font-bold text-gray-900">{value}</p>
            {subtitle && (
              <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
            )}
          </div>
          <div className={`p-3 rounded-lg ${colorClasses[color] || colorClasses.blue}`}>
            <Icon size={24} />
          </div>
        </div>
        {variation !== undefined && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">vs período anterior</span>
              <VariationBadge value={variation} />
            </div>
          </div>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-500">Cargando reportes...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Dashboard de Reportes</h1>
            {dashboard?.period && (
              <p className="text-sm text-gray-500 mt-1">
                {new Date(dashboard.period.start_date).toLocaleDateString('es-AR')} - {new Date(dashboard.period.end_date).toLocaleDateString('es-AR')}
                {dashboard.period.type === 'custom' && <span className="ml-2 text-blue-600">(Rango personalizado)</span>}
              </p>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={loadDashboard}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Actualizar"
            >
              <RefreshCw size={20} />
            </button>
            
            <button
              onClick={() => {
                loadGoals()
                setShowGoalsModal(true)
              }}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              <Target size={16} />
              <span className="hidden sm:inline">Metas</span>
            </button>
          </div>
        </div>

        {/* Filtros */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex flex-wrap items-center gap-4">
            {/* Toggle modo de filtro */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setFilterMode('period')}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  filterMode === 'period' 
                    ? 'bg-white text-gray-900 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Período
              </button>
              <button
                onClick={() => setFilterMode('range')}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  filterMode === 'range' 
                    ? 'bg-white text-gray-900 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Rango de Fechas
              </button>
            </div>

            {filterMode === 'period' ? (
              /* Selector de período */
              <div className="relative">
                <select
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                  className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="diario">Hoy</option>
                  <option value="semanal">Esta Semana</option>
                  <option value="mensual">Este Mes</option>
                  <option value="trimestral">Este Trimestre</option>
                  <option value="anual">Este Año</option>
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={16} />
              </div>
            ) : (
              /* Selector de rango de fechas */
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-600">Desde:</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-600">Hasta:</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <button
                  onClick={handleApplyDateRange}
                  disabled={!startDate || !endDate}
                  className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Calendar size={16} />
                  Aplicar
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="text-red-500 flex-shrink-0" size={20} />
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {dashboard && (
        <>
          {/* KPIs principales */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICard
              title="Ventas"
              value={formatCurrency(dashboard.ventas?.total || 0)}
              subtitle={`${dashboard.ventas?.cantidad || 0} transacciones`}
              variation={dashboard.ventas?.variacion}
              icon={ShoppingCart}
              color="green"
            />
            <KPICard
              title="Gastos"
              value={formatCurrency(dashboard.gastos?.total || 0)}
              subtitle={`Dir: ${formatCurrency(dashboard.gastos?.directos || 0)} | Ind: ${formatCurrency(dashboard.gastos?.indirectos || 0)}`}
              variation={dashboard.gastos?.variacion}
              icon={Receipt}
              color="red"
            />
            <KPICard
              title="Sueldos"
              value={formatCurrency(dashboard.sueldos?.total || 0)}
              subtitle={`${dashboard.sueldos?.horas_trabajadas?.toFixed(0) || 0} horas trabajadas`}
              variation={dashboard.sueldos?.variacion}
              icon={Users}
              color="purple"
            />
            <KPICard
              title="Rentabilidad"
              value={`${dashboard.rentabilidad?.margen_porcentaje || 0}%`}
              subtitle={`Neto: ${formatCurrency(dashboard.rentabilidad?.resultado_neto || 0)}`}
              icon={TrendingUp}
              color={dashboard.rentabilidad?.resultado_neto >= 0 ? 'green' : 'red'}
            />
          </div>

          {/* Desglose financiero */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Balance resumido */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <BarChart3 size={20} className="text-blue-600" />
                Balance del Período
              </h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b border-gray-100">
                  <span className="text-gray-600">Ingresos (Ventas)</span>
                  <span className="font-semibold text-green-600">
                    {formatCurrency(dashboard.ventas?.total || 0)}
                  </span>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center justify-between py-2">
                    <span className="text-gray-500 text-sm">(-) Gastos Directos</span>
                    <span className="text-red-500">
                      {formatCurrency(dashboard.gastos?.directos || 0)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-gray-500 text-sm">(-) Gastos Indirectos</span>
                    <span className="text-red-500">
                      {formatCurrency(dashboard.gastos?.indirectos || 0)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-gray-500 text-sm">(-) Sueldos</span>
                    <span className="text-red-500">
                      {formatCurrency(dashboard.sueldos?.total || 0)}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between py-3 border-t-2 border-gray-200">
                  <span className="font-semibold text-gray-900">Resultado Neto</span>
                  <span className={`text-xl font-bold ${
                    dashboard.rentabilidad?.resultado_neto >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(dashboard.rentabilidad?.resultado_neto || 0)}
                  </span>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4 mt-4">
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Margen Bruto</p>
                      <p className="text-lg font-bold text-gray-900">
                        {dashboard.rentabilidad?.margen_bruto_porcentaje || 0}%
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Margen Neto</p>
                      <p className={`text-lg font-bold ${
                        dashboard.rentabilidad?.margen_porcentaje >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {dashboard.rentabilidad?.margen_porcentaje || 0}%
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Metas/Alcanzables */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Target size={20} className="text-amber-600" />
                  Progreso hacia Metas
                </h3>
                <button
                  onClick={() => {
                    loadGoals()
                    setShowGoalsModal(true)
                  }}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  Configurar
                </button>
              </div>
              
              {dashboard.goals && dashboard.goals.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {dashboard.goals.map((goal) => (
                    <GoalProgress key={goal.id} goal={goal} />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Target size={48} className="mx-auto text-gray-300 mb-3" />
                  <p className="text-gray-500 mb-4">No hay metas configuradas</p>
                  <button
                    onClick={() => {
                      loadGoals()
                      setShowGoalsModal(true)
                    }}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Configurar metas
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Distribución de gastos */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <PieChart size={20} className="text-purple-600" />
                Distribución de Gastos
              </h3>
              
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Gastos Directos</span>
                    <span className="font-medium">
                      {dashboard.gastos?.total > 0 
                        ? ((dashboard.gastos.directos / dashboard.gastos.total) * 100).toFixed(1)
                        : 0}%
                    </span>
                  </div>
                  <div className="w-full h-3 bg-gray-100 rounded-full">
                    <div 
                      className="h-full bg-blue-500 rounded-full"
                      style={{ 
                        width: `${dashboard.gastos?.total > 0 
                          ? (dashboard.gastos.directos / dashboard.gastos.total) * 100 
                          : 0}%` 
                      }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatCurrency(dashboard.gastos?.directos || 0)}
                  </p>
                </div>
                
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Gastos Indirectos</span>
                    <span className="font-medium">
                      {dashboard.gastos?.total > 0 
                        ? ((dashboard.gastos.indirectos / dashboard.gastos.total) * 100).toFixed(1)
                        : 0}%
                    </span>
                  </div>
                  <div className="w-full h-3 bg-gray-100 rounded-full">
                    <div 
                      className="h-full bg-purple-500 rounded-full"
                      style={{ 
                        width: `${dashboard.gastos?.total > 0 
                          ? (dashboard.gastos.indirectos / dashboard.gastos.total) * 100 
                          : 0}%` 
                      }}
                    />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatCurrency(dashboard.gastos?.indirectos || 0)}
                  </p>
                </div>
              </div>
            </div>
            
            {/* Ratios sobre ventas */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 lg:col-span-2">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Ratios sobre Ventas</h3>
              
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">
                    {dashboard.ventas?.total > 0 
                      ? ((dashboard.gastos?.directos / dashboard.ventas.total) * 100).toFixed(1)
                      : 0}%
                  </p>
                  <p className="text-xs text-gray-600 mt-1">Gastos Directos / Ventas</p>
                </div>
                
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <p className="text-2xl font-bold text-purple-600">
                    {dashboard.ventas?.total > 0 
                      ? ((dashboard.gastos?.indirectos / dashboard.ventas.total) * 100).toFixed(1)
                      : 0}%
                  </p>
                  <p className="text-xs text-gray-600 mt-1">Gastos Indirectos / Ventas</p>
                </div>
                
                <div className="text-center p-4 bg-amber-50 rounded-lg">
                  <p className="text-2xl font-bold text-amber-600">
                    {dashboard.ventas?.total > 0 
                      ? ((dashboard.sueldos?.total / dashboard.ventas.total) * 100).toFixed(1)
                      : 0}%
                  </p>
                  <p className="text-xs text-gray-600 mt-1">Costo Laboral / Ventas</p>
                </div>
              </div>
              
              {/* Ticket promedio y productividad */}
              <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-gray-100">
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <DollarSign className="text-green-600" size={24} />
                  <div>
                    <p className="text-sm text-gray-500">Ticket Promedio</p>
                    <p className="text-lg font-bold text-gray-900">
                      {formatCurrency(dashboard.ventas?.ticket_promedio || 0)}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <Clock className="text-blue-600" size={24} />
                  <div>
                    <p className="text-sm text-gray-500">Ventas / Hora</p>
                    <p className="text-lg font-bold text-gray-900">
                      {dashboard.sueldos?.horas_trabajadas > 0
                        ? formatCurrency(dashboard.ventas?.total / dashboard.sueldos.horas_trabajadas)
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Punto de Equilibrio */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Scale size={20} className="text-indigo-600" />
              Punto de Equilibrio
            </h3>
            
            {dashboard.punto_equilibrio && (
              <div className="space-y-4">
                {/* Estado visual */}
                <div className={`p-4 rounded-lg ${
                  dashboard.punto_equilibrio.estado === 'por_encima' 
                    ? 'bg-green-50 border border-green-200' 
                    : dashboard.punto_equilibrio.estado === 'por_debajo'
                    ? 'bg-red-50 border border-red-200'
                    : dashboard.punto_equilibrio.estado === 'en_equilibrio'
                    ? 'bg-amber-50 border border-amber-200'
                    : 'bg-gray-50 border border-gray-200'
                }`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">
                      {dashboard.punto_equilibrio.estado === 'por_encima' && '✓ Por encima del equilibrio'}
                      {dashboard.punto_equilibrio.estado === 'por_debajo' && '⚠ Por debajo del equilibrio'}
                      {dashboard.punto_equilibrio.estado === 'en_equilibrio' && '≈ En punto de equilibrio'}
                      {dashboard.punto_equilibrio.estado === 'sin_datos' && 'Sin datos suficientes'}
                      {dashboard.punto_equilibrio.estado === 'inalcanzable' && '✗ Margen insuficiente'}
                    </span>
                    <span className={`text-lg font-bold ${
                      dashboard.punto_equilibrio.estado === 'por_encima' 
                        ? 'text-green-600' 
                        : dashboard.punto_equilibrio.estado === 'por_debajo'
                        ? 'text-red-600'
                        : 'text-amber-600'
                    }`}>
                      {dashboard.punto_equilibrio.cobertura_actual_porcentaje}%
                    </span>
                  </div>
                  
                  {/* Barra de progreso */}
                  <div className="w-full h-4 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-500 ${
                        dashboard.punto_equilibrio.estado === 'por_encima' 
                          ? 'bg-green-500' 
                          : dashboard.punto_equilibrio.estado === 'por_debajo'
                          ? 'bg-red-500'
                          : 'bg-amber-500'
                      }`}
                      style={{ width: `${Math.min(dashboard.punto_equilibrio.cobertura_actual_porcentaje, 150)}%` }}
                    />
                  </div>
                  
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>0%</span>
                    <span className="font-medium">100% = Equilibrio</span>
                    <span>150%</span>
                  </div>
                </div>
                
                {/* Métricas detalladas */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-indigo-50 rounded-lg">
                    <p className="text-xs text-gray-500 mb-1">Punto de Equilibrio</p>
                    <p className="text-lg font-bold text-indigo-600">
                      {dashboard.punto_equilibrio.punto_equilibrio_pesos 
                        ? formatCurrency(dashboard.punto_equilibrio.punto_equilibrio_pesos)
                        : 'N/A'}
                    </p>
                  </div>
                  
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500 mb-1">Costos Fijos</p>
                    <p className="text-lg font-bold text-gray-700">
                      {formatCurrency(dashboard.punto_equilibrio.costos_fijos || 0)}
                    </p>
                    <p className="text-xs text-gray-400">Indirectos + Sueldos</p>
                  </div>
                  
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500 mb-1">Costos Variables</p>
                    <p className="text-lg font-bold text-gray-700">
                      {formatCurrency(dashboard.punto_equilibrio.costos_variables || 0)}
                    </p>
                    <p className="text-xs text-gray-400">Gastos Directos</p>
                  </div>
                  
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <p className="text-xs text-gray-500 mb-1">Margen Contribución</p>
                    <p className="text-lg font-bold text-blue-600">
                      {dashboard.punto_equilibrio.margen_contribucion_porcentaje || 0}%
                    </p>
                  </div>
                </div>
                
                {/* Diferencia */}
                {dashboard.punto_equilibrio.estado !== 'sin_datos' && dashboard.punto_equilibrio.estado !== 'inalcanzable' && (
                  <div className={`p-4 rounded-lg text-center ${
                    dashboard.punto_equilibrio.diferencia >= 0 
                      ? 'bg-green-50' 
                      : 'bg-red-50'
                  }`}>
                    {dashboard.punto_equilibrio.diferencia >= 0 ? (
                      <>
                        <p className="text-sm text-gray-600">Excedente sobre punto de equilibrio</p>
                        <p className="text-2xl font-bold text-green-600">
                          +{formatCurrency(dashboard.punto_equilibrio.excedente)}
                        </p>
                      </>
                    ) : (
                      <>
                        <p className="text-sm text-gray-600">Ventas faltantes para alcanzar equilibrio</p>
                        <p className="text-2xl font-bold text-red-600">
                          {formatCurrency(dashboard.punto_equilibrio.ventas_faltantes)}
                        </p>
                      </>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}

      {/* Modal de configuración de metas */}
      {showGoalsModal && (
        <GoalsModal
          goals={goals}
          onClose={() => setShowGoalsModal(false)}
          onSave={async (newGoal) => {
            try {
              await reportsService.createGoal(newGoal)
              loadGoals()
              loadDashboard()
            } catch (err) {
              console.error('Error saving goal:', err)
            }
          }}
          onDelete={async (goalId) => {
            try {
              await reportsService.deleteGoal(goalId)
              loadGoals()
              loadDashboard()
            } catch (err) {
              console.error('Error deleting goal:', err)
            }
          }}
        />
      )}
    </div>
  )
}

const GoalsModal = ({ goals, onClose, onSave, onDelete }) => {
  const [newGoal, setNewGoal] = useState({
    goal_type: 'ventas',
    target_value: '',
    target_unit: 'monto',
    period_type: 'mensual',
    comparison_type: 'mayor_o_igual'
  })

  const goalTypes = [
    { value: 'ventas', label: 'Ventas', unit: 'monto', comparison: 'mayor_o_igual' },
    { value: 'rentabilidad', label: 'Rentabilidad', unit: 'porcentaje', comparison: 'mayor_o_igual' },
    { value: 'productividad', label: 'Productividad ($/hora)', unit: 'monto', comparison: 'mayor_o_igual' },
    { value: 'gastos_directos', label: 'Gastos Directos (% ventas)', unit: 'porcentaje', comparison: 'menor_o_igual' },
    { value: 'gastos_indirectos', label: 'Gastos Indirectos (% ventas)', unit: 'porcentaje', comparison: 'menor_o_igual' },
    { value: 'costo_laboral', label: 'Costo Laboral (% ventas)', unit: 'porcentaje', comparison: 'menor_o_igual' }
  ]

  const handleTypeChange = (type) => {
    const goalDef = goalTypes.find(g => g.value === type)
    setNewGoal({
      ...newGoal,
      goal_type: type,
      target_unit: goalDef?.unit || 'monto',
      comparison_type: goalDef?.comparison || 'mayor_o_igual'
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (newGoal.target_value) {
      onSave(newGoal)
      setNewGoal({
        goal_type: 'ventas',
        target_value: '',
        target_unit: 'monto',
        period_type: 'mensual',
        comparison_type: 'mayor_o_igual'
      })
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900">Configurar Metas</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
        </div>
        
        <div className="p-6">
          {/* Metas existentes */}
          {goals.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Metas Activas</h3>
              <div className="space-y-2">
                {goals.map((goal) => (
                  <div key={goal.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <span className="font-medium text-gray-900">
                        {goalTypes.find(g => g.value === goal.goal_type)?.label || goal.goal_type}
                      </span>
                      <span className="text-gray-500 ml-2">
                        {goal.target_unit === 'monto' 
                          ? `$${Number(goal.target_value).toLocaleString()}`
                          : `${goal.target_value}%`}
                      </span>
                    </div>
                    <button
                      onClick={() => onDelete(goal.id)}
                      className="text-red-500 hover:text-red-700 text-sm"
                    >
                      Eliminar
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Formulario nueva meta */}
          <form onSubmit={handleSubmit}>
            <h3 className="text-sm font-medium text-gray-700 mb-3">Nueva Meta</h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Tipo de Meta</label>
                <select
                  value={newGoal.goal_type}
                  onChange={(e) => handleTypeChange(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {goalTypes.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Valor Objetivo {newGoal.target_unit === 'porcentaje' ? '(%)' : '($)'}
                </label>
                <input
                  type="number"
                  value={newGoal.target_value}
                  onChange={(e) => setNewGoal({ ...newGoal, target_value: e.target.value })}
                  placeholder={newGoal.target_unit === 'porcentaje' ? 'ej: 25' : 'ej: 10000000'}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm text-gray-600 mb-1">Período</label>
                <select
                  value={newGoal.period_type}
                  onChange={(e) => setNewGoal({ ...newGoal, period_type: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="diario">Diario</option>
                  <option value="semanal">Semanal</option>
                  <option value="mensual">Mensual</option>
                  <option value="trimestral">Trimestral</option>
                  <option value="anual">Anual</option>
                </select>
              </div>
              
              <div className="flex items-end">
                <button
                  type="submit"
                  className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Agregar Meta
                </button>
              </div>
            </div>
          </form>
        </div>
        
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="w-full bg-gray-200 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors font-medium"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}

export default Reports
