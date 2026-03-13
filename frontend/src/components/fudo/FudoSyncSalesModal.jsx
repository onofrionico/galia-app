import { useState, useEffect } from 'react';
import { X, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import fudoService from '../../services/fudoService';

const FudoSyncSalesModal = ({ isOpen, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [syncConfig, setSyncConfig] = useState({
    startDate: '',
    endDate: '',
    updateExisting: false
  });
  const [syncResults, setSyncResults] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      testConnection();
    }
  }, [isOpen]);

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

  const handleSync = async () => {
    setLoading(true);
    setError(null);
    setSyncResults(null);

    try {
      // Convert dates to ISO format for sales API
      const startDateISO = syncConfig.startDate ? `${syncConfig.startDate}T00:00:00Z` : null;
      const endDateISO = syncConfig.endDate ? `${syncConfig.endDate}T23:59:59Z` : null;

      const result = await fudoService.syncSales(
        startDateISO,
        endDateISO,
        syncConfig.updateExisting
      );
      
      // Handle async response (202)
      if (result.status === 'processing') {
        setSyncResults({
          message: result.message,
          processing: true
        });
        setTimeout(() => {
          onSuccess();
          onClose();
        }, 3000);
      } else {
        // Handle sync response (200) - for backwards compatibility
        setSyncResults(result.results);
        if (result.results.imported > 0 || result.results.updated > 0) {
          setTimeout(() => {
            onSuccess();
            onClose();
          }, 2000);
        }
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Error al sincronizar ventas');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl">
        <div className="p-4 border-b flex items-center justify-between">
          <h2 className="text-lg font-semibold">Sincronizar Ventas desde Fudo</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Connection Status */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-gray-900">Estado de Conexión</h3>
              <button
                onClick={testConnection}
                disabled={testingConnection}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${testingConnection ? 'animate-spin' : ''}`} />
                Probar
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
            <h3 className="font-medium text-gray-900 mb-3">Rango de Fechas (Opcional)</h3>
            <p className="text-sm text-gray-600 mb-3">
              Si no especificas fechas, se sincronizarán todas las ventas disponibles.
            </p>
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
              <span className="text-sm text-gray-700">Actualizar ventas existentes</span>
            </label>
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
              <h4 className="font-medium text-blue-900 mb-3 flex items-center gap-2">
                <CheckCircle className="w-5 h-5" />
                {syncResults.processing ? 'Sincronización Iniciada' : 'Resultados de la Sincronización'}
              </h4>
              {syncResults.processing ? (
                <div className="bg-white rounded p-4">
                  <p className="text-sm text-gray-700">
                    {syncResults.message}
                  </p>
                  <p className="text-xs text-gray-500 mt-2">
                    La sincronización se está ejecutando en segundo plano. Los datos se actualizarán automáticamente cuando finalice el proceso.
                  </p>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-4 gap-3">
                    <div className="bg-white rounded p-3 text-center">
                      <div className="text-2xl font-bold text-blue-900">{syncResults.total_fetched}</div>
                      <div className="text-xs text-blue-600">Obtenidas</div>
                    </div>
                    <div className="bg-white rounded p-3 text-center">
                      <div className="text-2xl font-bold text-green-900">{syncResults.imported}</div>
                      <div className="text-xs text-green-600">Importadas</div>
                    </div>
                    <div className="bg-white rounded p-3 text-center">
                      <div className="text-2xl font-bold text-yellow-900">{syncResults.updated}</div>
                      <div className="text-xs text-yellow-600">Actualizadas</div>
                    </div>
                    <div className="bg-white rounded p-3 text-center">
                      <div className="text-2xl font-bold text-gray-900">{syncResults.skipped}</div>
                      <div className="text-xs text-gray-600">Omitidas</div>
                    </div>
                  </div>
                  {syncResults.errors && syncResults.errors.length > 0 && (
                    <div className="mt-3 p-2 bg-red-50 rounded text-sm text-red-600">
                      ⚠️ {syncResults.errors.length} errores encontrados
                    </div>
                  )}
                </>
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
            disabled={loading || !connectionStatus?.success}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Sincronizando...' : 'Sincronizar Ventas'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FudoSyncSalesModal;
