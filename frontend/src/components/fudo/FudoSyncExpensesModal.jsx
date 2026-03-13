import { useState, useEffect } from 'react';
import { X, RefreshCw, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';
import fudoService from '../../services/fudoService';

const FudoSyncExpensesModal = ({ isOpen, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [fudoCategories, setFudoCategories] = useState([]);
  const [galiaCategories, setGaliaCategories] = useState([]);
  const [categoryMapping, setCategoryMapping] = useState({});
  const [syncConfig, setSyncConfig] = useState({
    startDate: '',
    endDate: '',
    updateExisting: false
  });
  const [syncResults, setSyncResults] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadCategories();
    }
  }, [isOpen]);

  const loadCategories = async () => {
    try {
      const data = await fudoService.getCategories();
      console.log('Categorías de Fudo recibidas:', data.fudo_categories);
      console.log('Categorías de Galia recibidas:', data.galia_categories);
      setFudoCategories(data.fudo_categories || []);
      setGaliaCategories(data.galia_categories || []);
    } catch (err) {
      console.error('Error cargando categorías:', err);
      setError('Error al cargar categorías: ' + (err.response?.data?.error || err.message));
    }
  };

  const testConnection = async () => {
    setTestingConnection(true);
    setConnectionStatus(null);
    try {
      const result = await fudoService.testConnection();
      setConnectionStatus({ success: true, message: result.message });
    } catch (err) {
      setConnectionStatus({ 
        success: false, 
        message: err.response?.data?.message || 'Error al conectar con Fudo'
      });
    } finally {
      setTestingConnection(false);
    }
  };

  const handleMappingChange = (fudoId, galiaId) => {
    setCategoryMapping(prev => ({
      ...prev,
      [fudoId]: galiaId ? parseInt(galiaId) : null
    }));
  };

  const handleSync = async () => {
    const mappedCategories = Object.fromEntries(
      Object.entries(categoryMapping).filter(([_, value]) => value !== null)
    );

    // Allow sync without category mapping - expenses will have category_id = None

    setLoading(true);
    setError(null);
    setSyncResults(null);

    try {
      const result = await fudoService.syncExpenses(
        syncConfig.startDate,
        syncConfig.endDate,
        mappedCategories,
        syncConfig.updateExisting
      );
      setSyncResults(result.results);
      if (result.results.imported > 0 || result.results.updated > 0) {
        setTimeout(() => {
          onSuccess();
          onClose();
        }, 2000);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al sincronizar gastos');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="p-4 border-b flex items-center justify-between sticky top-0 bg-white z-10">
          <h2 className="text-lg font-semibold">Sincronizar Gastos desde Fudo</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Connection Test */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-gray-900">Estado de Conexión</h3>
              <button
                onClick={testConnection}
                disabled={testingConnection}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${testingConnection ? 'animate-spin' : ''}`} />
                Probar Conexión
              </button>
            </div>
            {connectionStatus && (
              <div className={`flex items-center gap-2 mt-2 p-2 rounded ${
                connectionStatus.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
              }`}>
                {connectionStatus.success ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <AlertCircle className="w-4 h-4" />
                )}
                <span className="text-sm">{connectionStatus.message}</span>
              </div>
            )}
          </div>

          {/* Date Range */}
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Rango de Fechas</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Desde</label>
                <input
                  type="date"
                  value={syncConfig.startDate}
                  onChange={(e) => setSyncConfig(prev => ({ ...prev, startDate: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Hasta</label>
                <input
                  type="date"
                  value={syncConfig.endDate}
                  onChange={(e) => setSyncConfig(prev => ({ ...prev, endDate: e.target.value }))}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <label className="flex items-center gap-2 mt-3">
              <input
                type="checkbox"
                checked={syncConfig.updateExisting}
                onChange={(e) => setSyncConfig(prev => ({ ...prev, updateExisting: e.target.checked }))}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Actualizar gastos existentes</span>
            </label>
          </div>

          {/* Category Mapping */}
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Mapeo de Categorías</h3>
            <p className="text-sm text-gray-600 mb-4">
              Relaciona las categorías de Fudo con las categorías de Galia. Solo se sincronizarán los gastos de las categorías mapeadas.
            </p>
            <div className="space-y-2 max-h-64 overflow-y-auto border rounded-lg p-3">
              {fudoCategories.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">No hay categorías de Fudo disponibles</p>
              ) : (
                fudoCategories.map((fudoCat) => (
                  <div key={fudoCat.id} className="flex items-center gap-3 p-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 transition-colors">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 truncate">
                        {fudoCat.name || `Categoría ${fudoCat.id}`}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        <span className="font-mono bg-gray-100 px-1.5 py-0.5 rounded">ID: {fudoCat.id}</span>
                        {!fudoCat.active && <span className="ml-2 text-orange-600">(Inactiva)</span>}
                      </p>
                    </div>
                    <ArrowRight className="w-5 h-5 text-blue-400 flex-shrink-0" />
                    <select
                      value={categoryMapping[fudoCat.id] || ''}
                      onChange={(e) => handleMappingChange(fudoCat.id, e.target.value)}
                      className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">Sin mapear</option>
                      {galiaCategories.map((galiaCat) => (
                        <option key={galiaCat.id} value={galiaCat.id}>
                          {galiaCat.name} ({galiaCat.expense_type === 'directo' ? 'Directo' : 'Indirecto'})
                        </option>
                      ))}
                    </select>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Sync Results */}
          {syncResults && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-3">Resultados de la Sincronización</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-white rounded p-2 text-center">
                  <div className="text-2xl font-bold text-blue-900">{syncResults.total_fetched}</div>
                  <div className="text-xs text-blue-600">Obtenidos</div>
                </div>
                <div className="bg-white rounded p-2 text-center">
                  <div className="text-2xl font-bold text-green-900">{syncResults.imported}</div>
                  <div className="text-xs text-green-600">Importados</div>
                </div>
                <div className="bg-white rounded p-2 text-center">
                  <div className="text-2xl font-bold text-yellow-900">{syncResults.updated}</div>
                  <div className="text-xs text-yellow-600">Actualizados</div>
                </div>
                <div className="bg-white rounded p-2 text-center">
                  <div className="text-2xl font-bold text-gray-900">{syncResults.no_category_mapping || 0}</div>
                  <div className="text-xs text-gray-600">Sin mapear</div>
                </div>
              </div>
              {syncResults.errors && syncResults.errors.length > 0 && (
                <div className="mt-3 text-sm text-red-600">
                  {syncResults.errors.length} errores encontrados
                </div>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="p-4 border-t bg-gray-50 flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            Cerrar
          </button>
          <button
            onClick={handleSync}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Sincronizando...' : 'Sincronizar Gastos'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FudoSyncExpensesModal;
