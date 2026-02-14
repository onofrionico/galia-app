import { useState, useEffect, useCallback } from 'react';
import { 
  Upload, Download, Plus, Search, Filter, X, ChevronLeft, ChevronRight,
  FileText, AlertCircle, CheckCircle, DollarSign, TrendingDown, Building2,
  CreditCard, Eye, Edit2, Trash2, RefreshCw, Wallet
} from 'lucide-react';
import api from '../services/api';

const Expenses = () => {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [filters, setFilters] = useState({
    fecha_desde: '',
    fecha_hasta: '',
    proveedor: '',
    categoria: '',
    estado_pago: '',
    medio_pago: ''
  });
  const [filterOptions, setFilterOptions] = useState({
    categorias: [],
    proveedores: [],
    estados_pago: [],
    medios_pago: []
  });
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 50,
    total: 0,
    pages: 0
  });
  const [showFilters, setShowFilters] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showFormModal, setShowFormModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedExpense, setSelectedExpense] = useState(null);
  const [importFile, setImportFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importResults, setImportResults] = useState(null);
  const [formData, setFormData] = useState({
    fecha: new Date().toISOString().split('T')[0],
    fecha_vencimiento: '',
    proveedor: '',
    categoria: '',
    subcategoria: '',
    comentario: '',
    estado_pago: 'Pendiente',
    importe: '',
    de_caja: false,
    caja: '',
    medio_pago: '',
    numero_fiscal: '',
    tipo_comprobante: '',
    numero_comprobante: ''
  });
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState(null);

  const fetchExpenses = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', pagination.page);
      params.append('per_page', pagination.per_page);
      
      if (filters.fecha_desde) params.append('fecha_desde', filters.fecha_desde);
      if (filters.fecha_hasta) params.append('fecha_hasta', filters.fecha_hasta);
      if (filters.proveedor) params.append('proveedor', filters.proveedor);
      if (filters.categoria) params.append('categoria', filters.categoria);
      if (filters.estado_pago) params.append('estado_pago', filters.estado_pago);
      if (filters.medio_pago) params.append('medio_pago', filters.medio_pago);
      
      const response = await api.get(`/expenses?${params.toString()}`);
      setExpenses(response.data.expenses);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        pages: response.data.pages
      }));
    } catch (error) {
      console.error('Error fetching expenses:', error);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.per_page, filters]);

  const fetchStats = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filters.fecha_desde) params.append('fecha_desde', filters.fecha_desde);
      if (filters.fecha_hasta) params.append('fecha_hasta', filters.fecha_hasta);
      
      const response = await api.get(`/expenses/stats?${params.toString()}`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }, [filters.fecha_desde, filters.fecha_hasta]);

  const fetchFilterOptions = async () => {
    try {
      const response = await api.get('/expenses/filters');
      setFilterOptions(response.data);
    } catch (error) {
      console.error('Error fetching filter options:', error);
    }
  };

  useEffect(() => {
    fetchExpenses();
    fetchStats();
  }, [fetchExpenses, fetchStats]);

  useEffect(() => {
    fetchFilterOptions();
  }, []);

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const clearFilters = () => {
    setFilters({
      fecha_desde: '',
      fecha_hasta: '',
      proveedor: '',
      categoria: '',
      estado_pago: '',
      medio_pago: ''
    });
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleImportFile = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.csv')) {
      setImportFile(file);
      setImportResults(null);
    } else {
      alert('Por favor selecciona un archivo CSV');
      e.target.value = '';
    }
  };

  const handleImport = async () => {
    if (!importFile) return;
    
    setImporting(true);
    setImportResults(null);
    
    try {
      const formData = new FormData();
      formData.append('file', importFile);
      
      const response = await api.post('/expenses/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setImportResults(response.data.results);
      fetchExpenses();
      fetchStats();
      fetchFilterOptions();
    } catch (error) {
      console.error('Error importing:', error);
      setImportResults({
        error: error.response?.data?.error || 'Error al importar el archivo'
      });
    } finally {
      setImporting(false);
    }
  };

  const handleExport = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.fecha_desde) params.append('fecha_desde', filters.fecha_desde);
      if (filters.fecha_hasta) params.append('fecha_hasta', filters.fecha_hasta);
      
      const response = await api.get(`/expenses/export?${params.toString()}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `gastos_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Error exporting:', error);
      alert('Error al exportar los datos');
    }
  };

  const resetForm = () => {
    setFormData({
      fecha: new Date().toISOString().split('T')[0],
      fecha_vencimiento: '',
      proveedor: '',
      categoria: '',
      subcategoria: '',
      comentario: '',
      estado_pago: 'Pendiente',
      importe: '',
      de_caja: false,
      caja: '',
      medio_pago: '',
      numero_fiscal: '',
      tipo_comprobante: '',
      numero_comprobante: ''
    });
    setEditingId(null);
  };

  const handleFormChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      const payload = {
        ...formData,
        importe: parseFloat(formData.importe) || 0
      };
      
      if (editingId) {
        await api.put(`/expenses/${editingId}`, payload);
      } else {
        await api.post('/expenses', payload);
      }
      
      setShowFormModal(false);
      resetForm();
      fetchExpenses();
      fetchStats();
      fetchFilterOptions();
    } catch (error) {
      console.error('Error saving expense:', error);
      alert(error.response?.data?.error || 'Error al guardar el gasto');
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (expense) => {
    setFormData({
      fecha: expense.fecha || '',
      fecha_vencimiento: expense.fecha_vencimiento || '',
      proveedor: expense.proveedor || '',
      categoria: expense.categoria || '',
      subcategoria: expense.subcategoria || '',
      comentario: expense.comentario || '',
      estado_pago: expense.estado_pago || 'Pendiente',
      importe: expense.importe || '',
      de_caja: expense.de_caja || false,
      caja: expense.caja || '',
      medio_pago: expense.medio_pago || '',
      numero_fiscal: expense.numero_fiscal || '',
      tipo_comprobante: expense.tipo_comprobante || '',
      numero_comprobante: expense.numero_comprobante || ''
    });
    setEditingId(expense.id);
    setShowFormModal(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('¿Estás seguro de eliminar este gasto?')) return;
    
    try {
      await api.delete(`/expenses/${id}`);
      fetchExpenses();
      fetchStats();
    } catch (error) {
      console.error('Error deleting expense:', error);
      alert('Error al eliminar el gasto');
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('es-AR');
  };

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Gastos</h1>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => { resetForm(); setShowFormModal(true); }}
            className="inline-flex items-center px-3 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 text-sm font-medium"
          >
            <Plus className="w-4 h-4 mr-1" />
            Nuevo Gasto
          </button>
          <button
            onClick={() => setShowImportModal(true)}
            className="inline-flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
          >
            <Upload className="w-4 h-4 mr-1" />
            Importar CSV
          </button>
          <button
            onClick={handleExport}
            className="inline-flex items-center px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium"
          >
            <Download className="w-4 h-4 mr-1" />
            Exportar
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center">
              <div className="p-2 bg-red-100 rounded-lg">
                <TrendingDown className="w-6 h-6 text-red-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Gastos</p>
                <p className="text-xl font-bold text-gray-900">{formatCurrency(stats.total_importe)}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Cantidad</p>
                <p className="text-xl font-bold text-gray-900">{stats.total_gastos}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center">
              <div className="p-2 bg-emerald-100 rounded-lg">
                <Building2 className="w-6 h-6 text-emerald-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Top Proveedor</p>
                <p className="text-sm font-bold text-gray-900 truncate">
                  {stats.top_proveedores?.[0]?.proveedor || '-'}
                </p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Wallet className="w-6 h-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Promedio</p>
                <p className="text-xl font-bold text-gray-900">
                  {formatCurrency(stats.total_gastos > 0 ? stats.total_importe / stats.total_gastos : 0)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="inline-flex items-center text-sm font-medium text-gray-700 hover:text-gray-900"
          >
            <Filter className="w-4 h-4 mr-2" />
            Filtros
            {Object.values(filters).some(v => v) && (
              <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-xs">
                Activos
              </span>
            )}
          </button>
          {Object.values(filters).some(v => v) && (
            <button
              onClick={clearFilters}
              className="text-sm text-red-600 hover:text-red-800"
            >
              Limpiar filtros
            </button>
          )}
        </div>
        
        {showFilters && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Desde</label>
              <input
                type="date"
                value={filters.fecha_desde}
                onChange={(e) => handleFilterChange('fecha_desde', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Hasta</label>
              <input
                type="date"
                value={filters.fecha_hasta}
                onChange={(e) => handleFilterChange('fecha_hasta', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Proveedor</label>
              <input
                type="text"
                placeholder="Buscar proveedor..."
                value={filters.proveedor}
                onChange={(e) => handleFilterChange('proveedor', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Categoría</label>
              <select
                value={filters.categoria}
                onChange={(e) => handleFilterChange('categoria', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todas</option>
                {filterOptions.categorias.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Estado</label>
              <select
                value={filters.estado_pago}
                onChange={(e) => handleFilterChange('estado_pago', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todos</option>
                {filterOptions.estados_pago.map(estado => (
                  <option key={estado} value={estado}>{estado}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Medio de Pago</label>
              <select
                value={filters.medio_pago}
                onChange={(e) => handleFilterChange('medio_pago', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Todos</option>
                {filterOptions.medios_pago.map(medio => (
                  <option key={medio} value={medio}>{medio}</option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Proveedor</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Categoría</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Comentario</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Importe</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Medio Pago</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="8" className="px-4 py-8 text-center text-gray-500">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                    Cargando gastos...
                  </td>
                </tr>
              ) : expenses.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-4 py-8 text-center text-gray-500">
                    No hay gastos para mostrar
                  </td>
                </tr>
              ) : (
                expenses.map((expense) => (
                  <tr key={expense.id} className={`hover:bg-gray-50 ${expense.cancelado ? 'opacity-50 line-through' : ''}`}>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(expense.fecha)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {expense.proveedor || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {expense.categoria || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                      {expense.comentario || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        expense.estado_pago === 'Pagado' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {expense.estado_pago}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 text-right">
                      {formatCurrency(expense.importe)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {expense.medio_pago || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => { setSelectedExpense(expense); setShowDetailModal(true); }}
                          className="p-1 text-gray-400 hover:text-blue-600"
                          title="Ver detalle"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleEdit(expense)}
                          className="p-1 text-gray-400 hover:text-emerald-600"
                          title="Editar"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(expense.id)}
                          className="p-1 text-gray-400 hover:text-red-600"
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

        {/* Pagination */}
        {pagination.pages > 1 && (
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Mostrando {((pagination.page - 1) * pagination.per_page) + 1} - {Math.min(pagination.page * pagination.per_page, pagination.total)} de {pagination.total}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                disabled={pagination.page === 1}
                className="p-2 rounded-lg border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                disabled={pagination.page === pagination.pages}
                className="p-2 rounded-lg border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">Importar Gastos desde CSV</h2>
                <button onClick={() => { setShowImportModal(false); setImportFile(null); setImportResults(null); }} className="text-gray-400 hover:text-gray-600">
                  <X className="w-6 h-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <Upload className="w-10 h-10 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600 mb-2">
                    Selecciona un archivo CSV con el formato del sistema externo
                  </p>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleImportFile}
                    className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  />
                </div>
                
                {importFile && (
                  <div className="flex items-center p-3 bg-blue-50 rounded-lg">
                    <FileText className="w-5 h-5 text-blue-600 mr-2" />
                    <span className="text-sm text-blue-800">{importFile.name}</span>
                  </div>
                )}
                
                {importResults && (
                  <div className={`p-4 rounded-lg ${importResults.error ? 'bg-red-50' : 'bg-green-50'}`}>
                    {importResults.error ? (
                      <div className="flex items-start">
                        <AlertCircle className="w-5 h-5 text-red-600 mr-2 flex-shrink-0" />
                        <p className="text-sm text-red-800">{importResults.error}</p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <div className="flex items-center">
                          <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
                          <span className="text-sm font-medium text-green-800">Importación completada</span>
                        </div>
                        <div className="text-sm text-green-700 pl-7">
                          <p>• {importResults.imported} registros importados</p>
                          <p>• {importResults.skipped} registros omitidos (ya existían)</p>
                          {importResults.errors?.length > 0 && (
                            <p className="text-red-600">• {importResults.errors.length} errores</p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => { setShowImportModal(false); setImportFile(null); setImportResults(null); }}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  >
                    Cerrar
                  </button>
                  <button
                    onClick={handleImport}
                    disabled={!importFile || importing}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {importing ? 'Importando...' : 'Importar'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Form Modal */}
      {showFormModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">
                  {editingId ? 'Editar Gasto' : 'Nuevo Gasto'}
                </h2>
                <button onClick={() => { setShowFormModal(false); resetForm(); }} className="text-gray-400 hover:text-gray-600">
                  <X className="w-6 h-6" />
                </button>
              </div>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Fecha *</label>
                    <input
                      type="date"
                      required
                      value={formData.fecha}
                      onChange={(e) => handleFormChange('fecha', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Importe *</label>
                    <input
                      type="number"
                      required
                      step="0.01"
                      min="0"
                      value={formData.importe}
                      onChange={(e) => handleFormChange('importe', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="0.00"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Proveedor</label>
                    <input
                      type="text"
                      value={formData.proveedor}
                      onChange={(e) => handleFormChange('proveedor', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Nombre del proveedor"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Categoría</label>
                    <input
                      type="text"
                      value={formData.categoria}
                      onChange={(e) => handleFormChange('categoria', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Ej: Mercadería, Servicios"
                      list="categorias-list"
                    />
                    <datalist id="categorias-list">
                      {filterOptions.categorias.map(cat => (
                        <option key={cat} value={cat} />
                      ))}
                    </datalist>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Estado de Pago</label>
                    <select
                      value={formData.estado_pago}
                      onChange={(e) => handleFormChange('estado_pago', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="Pendiente">Pendiente</option>
                      <option value="Pagado">Pagado</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Medio de Pago</label>
                    <input
                      type="text"
                      value={formData.medio_pago}
                      onChange={(e) => handleFormChange('medio_pago', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Ej: Efectivo, Mercado Pago"
                      list="medios-pago-list"
                    />
                    <datalist id="medios-pago-list">
                      {filterOptions.medios_pago.map(medio => (
                        <option key={medio} value={medio} />
                      ))}
                    </datalist>
                  </div>
                  <div className="sm:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Comentario</label>
                    <textarea
                      value={formData.comentario}
                      onChange={(e) => handleFormChange('comentario', e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Descripción del gasto..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Vencimiento</label>
                    <input
                      type="date"
                      value={formData.fecha_vencimiento}
                      onChange={(e) => handleFormChange('fecha_vencimiento', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Caja</label>
                    <input
                      type="text"
                      value={formData.caja}
                      onChange={(e) => handleFormChange('caja', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Ej: Principal"
                    />
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="de_caja"
                      checked={formData.de_caja}
                      onChange={(e) => handleFormChange('de_caja', e.target.checked)}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    <label htmlFor="de_caja" className="ml-2 text-sm text-gray-700">De Caja</label>
                  </div>
                </div>
                
                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => { setShowFormModal(false); resetForm(); }}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {saving ? 'Guardando...' : (editingId ? 'Actualizar' : 'Crear')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {showDetailModal && selectedExpense && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">Detalle del Gasto</h2>
                <button onClick={() => setShowDetailModal(false)} className="text-gray-400 hover:text-gray-600">
                  <X className="w-6 h-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-gray-500">Fecha</p>
                    <p className="font-medium">{formatDate(selectedExpense.fecha)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Importe</p>
                    <p className="font-bold text-lg text-red-600">{formatCurrency(selectedExpense.importe)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Proveedor</p>
                    <p className="font-medium">{selectedExpense.proveedor || '-'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Categoría</p>
                    <p className="font-medium">{selectedExpense.categoria || '-'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Estado de Pago</p>
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      selectedExpense.estado_pago === 'Pagado' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {selectedExpense.estado_pago}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Medio de Pago</p>
                    <p className="font-medium">{selectedExpense.medio_pago || '-'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">De Caja</p>
                    <p className="font-medium">{selectedExpense.de_caja ? 'Sí' : 'No'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Caja</p>
                    <p className="font-medium">{selectedExpense.caja || '-'}</p>
                  </div>
                </div>
                {selectedExpense.comentario && (
                  <div>
                    <p className="text-xs text-gray-500">Comentario</p>
                    <p className="font-medium whitespace-pre-wrap">{selectedExpense.comentario}</p>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-gray-500">Creado por</p>
                    <p className="font-medium">{selectedExpense.creado_por || '-'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">ID Externo</p>
                    <p className="font-medium">{selectedExpense.external_id || '-'}</p>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-3 pt-6">
                <button
                  onClick={() => setShowDetailModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cerrar
                </button>
                <button
                  onClick={() => { setShowDetailModal(false); handleEdit(selectedExpense); }}
                  className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
                >
                  Editar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Expenses;
