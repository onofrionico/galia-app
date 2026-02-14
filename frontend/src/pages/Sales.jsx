import { useState, useEffect, useCallback } from 'react';
import { 
  Upload, Download, Plus, Search, Filter, X, ChevronLeft, ChevronRight,
  FileText, AlertCircle, CheckCircle, DollarSign, TrendingUp, Users,
  CreditCard, Store, Truck, Eye, Edit2, Trash2, RefreshCw
} from 'lucide-react';
import api from '../services/api';

const Sales = () => {
  const [sales, setSales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [filters, setFilters] = useState({
    fecha_desde: '',
    fecha_hasta: '',
    estado: '',
    tipo_venta: '',
    origen: ''
  });
  const [filterOptions, setFilterOptions] = useState({
    estados: [],
    tipos_venta: [],
    origenes: [],
    salas: [],
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
  const [selectedSale, setSelectedSale] = useState(null);
  const [importFile, setImportFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importResults, setImportResults] = useState(null);
  const [formData, setFormData] = useState({
    fecha: new Date().toISOString().split('T')[0],
    caja: 'Principal',
    estado: 'Cerrada',
    cliente: '',
    mesa: '',
    sala: '',
    personas: '',
    camarero: '',
    medio_pago: '',
    total: '',
    fiscal: false,
    tipo_venta: 'Local',
    comentario: '',
    origen: '',
    id_origen: ''
  });
  const [saving, setSaving] = useState(false);

  const fetchSales = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', pagination.page);
      params.append('per_page', pagination.per_page);
      
      if (filters.fecha_desde) params.append('fecha_desde', filters.fecha_desde);
      if (filters.fecha_hasta) params.append('fecha_hasta', filters.fecha_hasta);
      if (filters.estado) params.append('estado', filters.estado);
      if (filters.tipo_venta) params.append('tipo_venta', filters.tipo_venta);
      if (filters.origen) params.append('origen', filters.origen);
      
      const response = await api.get(`/sales?${params.toString()}`);
      setSales(response.data.sales);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        pages: response.data.pages
      }));
    } catch (error) {
      console.error('Error fetching sales:', error);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.per_page, filters]);

  const fetchStats = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filters.fecha_desde) params.append('fecha_desde', filters.fecha_desde);
      if (filters.fecha_hasta) params.append('fecha_hasta', filters.fecha_hasta);
      
      const response = await api.get(`/sales/stats?${params.toString()}`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }, [filters.fecha_desde, filters.fecha_hasta]);

  const fetchFilterOptions = async () => {
    try {
      const response = await api.get('/sales/filters');
      setFilterOptions(response.data);
    } catch (error) {
      console.error('Error fetching filter options:', error);
    }
  };

  useEffect(() => {
    fetchSales();
    fetchStats();
  }, [fetchSales, fetchStats]);

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
      estado: '',
      tipo_venta: '',
      origen: ''
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
      
      const response = await api.post('/sales/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setImportResults(response.data.results);
      
      if (response.data.results.imported > 0) {
        fetchSales();
        fetchStats();
        fetchFilterOptions();
      }
    } catch (error) {
      console.error('Error importing:', error);
      alert('Error al importar: ' + (error.response?.data?.error || error.message));
    } finally {
      setImporting(false);
    }
  };

  const handleExport = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.fecha_desde) params.append('fecha_desde', filters.fecha_desde);
      if (filters.fecha_hasta) params.append('fecha_hasta', filters.fecha_hasta);
      
      const response = await api.get(`/sales/export?${params.toString()}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `ventas_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting:', error);
      alert('Error al exportar');
    }
  };

  const handleFormChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSaveSale = async () => {
    if (!formData.fecha || !formData.total) {
      alert('Fecha y Total son requeridos');
      return;
    }
    
    setSaving(true);
    try {
      const payload = {
        ...formData,
        total: parseFloat(formData.total) || 0,
        personas: formData.personas ? parseInt(formData.personas) : null
      };
      
      if (selectedSale?.id) {
        await api.put(`/sales/${selectedSale.id}`, payload);
      } else {
        await api.post('/sales', payload);
      }
      
      setShowFormModal(false);
      setSelectedSale(null);
      resetForm();
      fetchSales();
      fetchStats();
      fetchFilterOptions();
    } catch (error) {
      console.error('Error saving sale:', error);
      alert('Error al guardar: ' + (error.response?.data?.error || error.message));
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteSale = async (id) => {
    if (!confirm('¿Estás seguro de eliminar esta venta?')) return;
    
    try {
      await api.delete(`/sales/${id}`);
      fetchSales();
      fetchStats();
    } catch (error) {
      console.error('Error deleting sale:', error);
      alert('Error al eliminar');
    }
  };

  const openEditModal = (sale) => {
    setSelectedSale(sale);
    setFormData({
      fecha: sale.fecha,
      caja: sale.caja || 'Principal',
      estado: sale.estado || 'Cerrada',
      cliente: sale.cliente || '',
      mesa: sale.mesa || '',
      sala: sale.sala || '',
      personas: sale.personas || '',
      camarero: sale.camarero || '',
      medio_pago: sale.medio_pago || '',
      total: sale.total || '',
      fiscal: sale.fiscal || false,
      tipo_venta: sale.tipo_venta || 'Local',
      comentario: sale.comentario || '',
      origen: sale.origen || '',
      id_origen: sale.id_origen || ''
    });
    setShowFormModal(true);
  };

  const resetForm = () => {
    setFormData({
      fecha: new Date().toISOString().split('T')[0],
      caja: 'Principal',
      estado: 'Cerrada',
      cliente: '',
      mesa: '',
      sala: '',
      personas: '',
      camarero: '',
      medio_pago: '',
      total: '',
      fiscal: false,
      tipo_venta: 'Local',
      comentario: '',
      origen: '',
      id_origen: ''
    });
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-AR', {
      style: 'currency',
      currency: 'ARS',
      minimumFractionDigits: 0
    }).format(value || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('es-AR');
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('es-AR', {
      dateStyle: 'short',
      timeStyle: 'short'
    });
  };

  const getStatusColor = (estado) => {
    switch (estado) {
      case 'Cerrada': return 'bg-green-100 text-green-800';
      case 'En curso': return 'bg-yellow-100 text-yellow-800';
      case 'Enviado': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTipoVentaIcon = (tipo) => {
    switch (tipo) {
      case 'Delivery': return <Truck className="w-4 h-4" />;
      case 'Mostrador': return <Store className="w-4 h-4" />;
      default: return <Users className="w-4 h-4" />;
    }
  };

  return (
    <div className="p-4 md:p-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Ventas</h1>
          <p className="text-gray-600 mt-1">Gestión y análisis de ventas</p>
        </div>
        
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setShowImportModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Upload className="w-4 h-4" />
            Importar CSV
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            <Download className="w-4 h-4" />
            Exportar
          </button>
          <button
            onClick={() => { resetForm(); setSelectedSale(null); setShowFormModal(true); }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            Nueva Venta
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Ventas</p>
                <p className="text-xl font-bold text-gray-900">{stats.total_ventas}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <DollarSign className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Monto Total</p>
                <p className="text-xl font-bold text-gray-900">{formatCurrency(stats.total_monto)}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Store className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Promedio</p>
                <p className="text-xl font-bold text-gray-900">
                  {formatCurrency(stats.total_ventas > 0 ? stats.total_monto / stats.total_ventas : 0)}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <CreditCard className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Métodos de Pago</p>
                <p className="text-xl font-bold text-gray-900">{stats.por_medio_pago?.length || 0}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="p-4 border-b flex items-center justify-between">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 text-gray-700 hover:text-gray-900"
          >
            <Filter className="w-4 h-4" />
            Filtros
            {Object.values(filters).some(v => v) && (
              <span className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full">
                Activos
              </span>
            )}
          </button>
          
          <button
            onClick={() => { fetchSales(); fetchStats(); }}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-800"
          >
            <RefreshCw className="w-4 h-4" />
            Actualizar
          </button>
        </div>
        
        {showFilters && (
          <div className="p-4 grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Desde</label>
              <input
                type="date"
                value={filters.fecha_desde}
                onChange={(e) => handleFilterChange('fecha_desde', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Hasta</label>
              <input
                type="date"
                value={filters.fecha_hasta}
                onChange={(e) => handleFilterChange('fecha_hasta', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
              <select
                value={filters.estado}
                onChange={(e) => handleFilterChange('estado', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos</option>
                {filterOptions.estados.map(e => (
                  <option key={e} value={e}>{e}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
              <select
                value={filters.tipo_venta}
                onChange={(e) => handleFilterChange('tipo_venta', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos</option>
                {filterOptions.tipos_venta.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Origen</label>
              <select
                value={filters.origen}
                onChange={(e) => handleFilterChange('origen', e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Todos</option>
                {filterOptions.origenes.map(o => (
                  <option key={o} value={o}>{o}</option>
                ))}
              </select>
            </div>
            
            <div className="md:col-span-5 flex justify-end">
              <button
                onClick={clearFilters}
                className="text-sm text-gray-600 hover:text-gray-800"
              >
                Limpiar filtros
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Sales Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Mesa/Sala</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cliente</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Medio Pago</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan="9" className="px-4 py-8 text-center text-gray-500">
                    Cargando...
                  </td>
                </tr>
              ) : sales.length === 0 ? (
                <tr>
                  <td colSpan="9" className="px-4 py-8 text-center text-gray-500">
                    No hay ventas registradas
                  </td>
                </tr>
              ) : (
                sales.map((sale) => (
                  <tr key={sale.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {sale.external_id || sale.id}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {formatDate(sale.fecha)}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(sale.estado)}`}>
                        {sale.estado}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      <span className="flex items-center gap-1">
                        {getTipoVentaIcon(sale.tipo_venta)}
                        {sale.tipo_venta}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {sale.mesa && sale.sala ? `${sale.mesa} - ${sale.sala}` : sale.mesa || sale.sala || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 max-w-[150px] truncate">
                      {sale.cliente || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {sale.medio_pago || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                      {formatCurrency(sale.total)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => { setSelectedSale(sale); setShowDetailModal(true); }}
                          className="p-1 text-gray-500 hover:text-blue-600"
                          title="Ver detalle"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => openEditModal(sale)}
                          className="p-1 text-gray-500 hover:text-green-600"
                          title="Editar"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteSale(sale.id)}
                          className="p-1 text-gray-500 hover:text-red-600"
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
          <div className="px-4 py-3 border-t flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Mostrando {((pagination.page - 1) * pagination.per_page) + 1} - {Math.min(pagination.page * pagination.per_page, pagination.total)} de {pagination.total}
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                disabled={pagination.page === 1}
                className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-sm text-gray-600">
                Página {pagination.page} de {pagination.pages}
              </span>
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                disabled={pagination.page === pagination.pages}
                className="p-2 rounded-lg hover:bg-gray-100 disabled:opacity-50"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="text-lg font-semibold">Importar Ventas desde CSV</h2>
              <button onClick={() => { setShowImportModal(false); setImportFile(null); setImportResults(null); }}>
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            
            <div className="p-4 space-y-4">
              {/* Format info */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Formato del archivo CSV
                </h3>
                <p className="text-sm text-blue-800 mb-2">
                  El archivo debe tener las columnas del sistema de ventas:
                </p>
                <div className="text-xs text-blue-700 bg-white p-2 rounded border border-blue-200 overflow-x-auto">
                  <code>Id, Fecha, Creación, Cerrada, Caja, Estado, Cliente, Mesa, Sala, Personas, Camarero / Repartidor, Medio de Pago, Total, Fiscal, Tipo de Venta, Comentario, Origen, Id. Origen</code>
                </div>
              </div>
              
              {/* File input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Seleccionar archivo CSV
                </label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleImportFile}
                  className="block w-full text-sm text-gray-500
                    file:mr-4 file:py-2 file:px-4
                    file:rounded-lg file:border-0
                    file:text-sm file:font-semibold
                    file:bg-blue-50 file:text-blue-700
                    hover:file:bg-blue-100
                    cursor-pointer"
                />
              </div>
              
              {importFile && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <FileText className="w-4 h-4" />
                  <span>{importFile.name}</span>
                  <span className="text-gray-400">({(importFile.size / 1024).toFixed(2)} KB)</span>
                </div>
              )}
              
              {/* Import results */}
              {importResults && (
                <div className="border-t pt-4 mt-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Resultados de la Importación</h3>
                  
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="bg-blue-50 rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-blue-900">{importResults.total_rows}</div>
                      <div className="text-xs text-blue-600">Total filas</div>
                    </div>
                    <div className="bg-green-50 rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-green-900">{importResults.imported}</div>
                      <div className="text-xs text-green-600">Importados</div>
                    </div>
                    <div className="bg-yellow-50 rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-yellow-900">{importResults.skipped}</div>
                      <div className="text-xs text-yellow-600">Omitidos (duplicados)</div>
                    </div>
                  </div>
                  
                  {importResults.errors.length > 0 && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <h4 className="font-medium text-red-900 mb-2 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        Errores ({importResults.errors.length})
                      </h4>
                      <div className="max-h-40 overflow-y-auto space-y-2">
                        {importResults.errors.slice(0, 10).map((err, idx) => (
                          <div key={idx} className="text-sm text-red-800">
                            <strong>Fila {err.row}:</strong> {err.errors.join(', ')}
                          </div>
                        ))}
                        {importResults.errors.length > 10 && (
                          <p className="text-sm text-red-600">... y {importResults.errors.length - 10} errores más</p>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {importResults.imported > 0 && importResults.errors.length === 0 && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3 flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <span className="text-green-800 font-medium">¡Importación completada exitosamente!</span>
                    </div>
                  )}
                </div>
              )}
              
              {/* Actions */}
              <div className="flex gap-2 justify-end pt-4 border-t">
                <button
                  onClick={() => { setShowImportModal(false); setImportFile(null); setImportResults(null); }}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
                >
                  Cerrar
                </button>
                <button
                  onClick={handleImport}
                  disabled={!importFile || importing}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
                >
                  <Upload className="w-4 h-4" />
                  {importing ? 'Importando...' : 'Importar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Form Modal */}
      {showFormModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="text-lg font-semibold">
                {selectedSale ? 'Editar Venta' : 'Nueva Venta'}
              </h2>
              <button onClick={() => { setShowFormModal(false); setSelectedSale(null); resetForm(); }}>
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Fecha *</label>
                  <input
                    type="date"
                    value={formData.fecha}
                    onChange={(e) => handleFormChange('fecha', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Total *</label>
                  <input
                    type="number"
                    value={formData.total}
                    onChange={(e) => handleFormChange('total', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="0"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
                  <select
                    value={formData.estado}
                    onChange={(e) => handleFormChange('estado', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Cerrada">Cerrada</option>
                    <option value="En curso">En curso</option>
                    <option value="Enviado">Enviado</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Venta</label>
                  <select
                    value={formData.tipo_venta}
                    onChange={(e) => handleFormChange('tipo_venta', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Local">Local</option>
                    <option value="Delivery">Delivery</option>
                    <option value="Mostrador">Mostrador</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Mesa</label>
                  <input
                    type="text"
                    value={formData.mesa}
                    onChange={(e) => handleFormChange('mesa', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Ej: 5"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Sala</label>
                  <input
                    type="text"
                    value={formData.sala}
                    onChange={(e) => handleFormChange('sala', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Ej: Salón, Patio"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Personas</label>
                  <input
                    type="number"
                    value={formData.personas}
                    onChange={(e) => handleFormChange('personas', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="0"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Medio de Pago</label>
                  <input
                    type="text"
                    value={formData.medio_pago}
                    onChange={(e) => handleFormChange('medio_pago', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Ej: Efectivo, Mercado pago"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cliente</label>
                  <input
                    type="text"
                    value={formData.cliente}
                    onChange={(e) => handleFormChange('cliente', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Nombre del cliente"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Camarero/Repartidor</label>
                  <input
                    type="text"
                    value={formData.camarero}
                    onChange={(e) => handleFormChange('camarero', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Nombre"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Caja</label>
                  <input
                    type="text"
                    value={formData.caja}
                    onChange={(e) => handleFormChange('caja', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Principal"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Origen</label>
                  <input
                    type="text"
                    value={formData.origen}
                    onChange={(e) => handleFormChange('origen', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Ej: Pedidos Ya"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">ID Origen</label>
                  <input
                    type="text"
                    value={formData.id_origen}
                    onChange={(e) => handleFormChange('id_origen', e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="ID externo"
                  />
                </div>
                
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="fiscal"
                    checked={formData.fiscal}
                    onChange={(e) => handleFormChange('fiscal', e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="fiscal" className="text-sm font-medium text-gray-700">
                    Fiscal (con factura)
                  </label>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Comentario</label>
                <textarea
                  value={formData.comentario}
                  onChange={(e) => handleFormChange('comentario', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  rows="2"
                  placeholder="Notas adicionales"
                />
              </div>
              
              <div className="flex gap-2 justify-end pt-4 border-t">
                <button
                  onClick={() => { setShowFormModal(false); setSelectedSale(null); resetForm(); }}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSaveSale}
                  disabled={saving}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {saving ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {showDetailModal && selectedSale && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="text-lg font-semibold">Detalle de Venta #{selectedSale.external_id || selectedSale.id}</h2>
              <button onClick={() => { setShowDetailModal(false); setSelectedSale(null); }}>
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Fecha</p>
                  <p className="font-medium">{formatDate(selectedSale.fecha)}</p>
                </div>
                <div>
                  <p className="text-gray-500">Total</p>
                  <p className="font-bold text-lg text-green-600">{formatCurrency(selectedSale.total)}</p>
                </div>
                <div>
                  <p className="text-gray-500">Estado</p>
                  <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(selectedSale.estado)}`}>
                    {selectedSale.estado}
                  </span>
                </div>
                <div>
                  <p className="text-gray-500">Tipo de Venta</p>
                  <p className="font-medium flex items-center gap-1">
                    {getTipoVentaIcon(selectedSale.tipo_venta)}
                    {selectedSale.tipo_venta}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Creación</p>
                  <p className="font-medium">{formatDateTime(selectedSale.creacion)}</p>
                </div>
                <div>
                  <p className="text-gray-500">Cerrada</p>
                  <p className="font-medium">{formatDateTime(selectedSale.cerrada)}</p>
                </div>
                {selectedSale.mesa && (
                  <div>
                    <p className="text-gray-500">Mesa</p>
                    <p className="font-medium">{selectedSale.mesa}</p>
                  </div>
                )}
                {selectedSale.sala && (
                  <div>
                    <p className="text-gray-500">Sala</p>
                    <p className="font-medium">{selectedSale.sala}</p>
                  </div>
                )}
                {selectedSale.personas && (
                  <div>
                    <p className="text-gray-500">Personas</p>
                    <p className="font-medium">{selectedSale.personas}</p>
                  </div>
                )}
                {selectedSale.cliente && (
                  <div className="col-span-2">
                    <p className="text-gray-500">Cliente</p>
                    <p className="font-medium">{selectedSale.cliente}</p>
                  </div>
                )}
                {selectedSale.camarero && (
                  <div>
                    <p className="text-gray-500">Camarero/Repartidor</p>
                    <p className="font-medium">{selectedSale.camarero}</p>
                  </div>
                )}
                {selectedSale.medio_pago && (
                  <div>
                    <p className="text-gray-500">Medio de Pago</p>
                    <p className="font-medium">{selectedSale.medio_pago}</p>
                  </div>
                )}
                <div>
                  <p className="text-gray-500">Fiscal</p>
                  <p className="font-medium">{selectedSale.fiscal ? 'Sí' : 'No'}</p>
                </div>
                {selectedSale.caja && (
                  <div>
                    <p className="text-gray-500">Caja</p>
                    <p className="font-medium">{selectedSale.caja}</p>
                  </div>
                )}
                {selectedSale.origen && (
                  <div>
                    <p className="text-gray-500">Origen</p>
                    <p className="font-medium">{selectedSale.origen}</p>
                  </div>
                )}
                {selectedSale.id_origen && (
                  <div>
                    <p className="text-gray-500">ID Origen</p>
                    <p className="font-medium">{selectedSale.id_origen}</p>
                  </div>
                )}
                {selectedSale.comentario && (
                  <div className="col-span-2">
                    <p className="text-gray-500">Comentario</p>
                    <p className="font-medium">{selectedSale.comentario}</p>
                  </div>
                )}
              </div>
              
              <div className="flex gap-2 justify-end pt-4 border-t">
                <button
                  onClick={() => { setShowDetailModal(false); openEditModal(selectedSale); }}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  <Edit2 className="w-4 h-4" />
                  Editar
                </button>
                <button
                  onClick={() => { setShowDetailModal(false); setSelectedSale(null); }}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
                >
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sales;
