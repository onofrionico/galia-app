import { useState, useEffect } from 'react';
import { X, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import fudoService from '../../services/fudoService';
import { errorCount, formatRunDate, isRunFinished, summarizeRun, validateRange } from './syncRunSummary';

const POLL_MS = 2000;

const FudoSyncExpensesModal = ({ isOpen, onClose, onSuccess }) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [run, setRun] = useState(null);
  const [lastRun, setLastRun] = useState(null);
  const [error, setError] = useState(null);
  const [starting, setStarting] = useState(false);

  const running = run && !isRunFinished(run);

  useEffect(() => {
    if (!isOpen) return;
    setRun(null);
    setError(null);
    fudoService.getSyncRuns('expenses', 1)
      .then((runs) => {
        const latest = runs[0] || null;
        setLastRun(latest);
        if (latest && !isRunFinished(latest)) setRun(latest);
      })
      .catch(() => setLastRun(null));
  }, [isOpen]);

  useEffect(() => {
    if (!running) return undefined;
    const timer = setInterval(async () => {
      try {
        const updated = await fudoService.getSyncRun(run.id);
        setRun(updated);
        if (isRunFinished(updated)) {
          setLastRun(updated);
          if (updated.status === 'ok') onSuccess?.();
        }
      } catch (err) {
        setError(err.response?.data?.error || 'No se pudo consultar el estado de la sincronización');
      }
    }, POLL_MS);
    return () => clearInterval(timer);
  }, [running, run?.id, onSuccess]);

  const handleSync = async () => {
    const rangeError = validateRange(startDate, endDate);
    if (rangeError) {
      setError(rangeError);
      return;
    }
    setStarting(true);
    setError(null);
    try {
      const { run_id: runId } = await fudoService.syncExpenses(startDate, endDate);
      setRun({ id: runId, status: 'running' });
    } catch (err) {
      if (err.response?.status === 409 && err.response.data?.run_id) {
        setError('Ya hay una sincronización en curso; te muestro su avance.');
        setRun({ id: err.response.data.run_id, status: 'running' });
      } else {
        setError(err.response?.data?.error || 'Error al iniciar la sincronización');
      }
    } finally {
      setStarting(false);
    }
  };

  if (!isOpen) return null;

  const shown = run && isRunFinished(run) ? run : null;
  const failed = shown ? errorCount(shown) : 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-4 border-b flex items-center justify-between sticky top-0 bg-white z-10">
          <h2 className="text-lg font-semibold">Sincronizar gastos desde Fudo</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700" aria-label="Cerrar">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <p className="text-sm text-gray-600">
            Trae los gastos del rango elegido. Los proveedores y categorías se vinculan solos con los de Galia
            (o se crean si no existen). Si corregiste a mano la categoría o el proveedor de un gasto, se respeta.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="block">
              <span className="block text-sm font-medium text-gray-700 mb-1">Desde</span>
              <input type="date" value={startDate} disabled={running}
                     onChange={(e) => setStartDate(e.target.value)}
                     className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500" />
            </label>
            <label className="block">
              <span className="block text-sm font-medium text-gray-700 mb-1">Hasta</span>
              <input type="date" value={endDate} disabled={running}
                     onChange={(e) => setEndDate(e.target.value)}
                     className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500" />
            </label>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {running && (
            <div className="flex items-center gap-2 text-sm text-blue-800 bg-blue-50 rounded-lg p-3">
              <RefreshCw className="w-4 h-4 animate-spin" />
              Sincronizando… podés cerrar esta ventana, sigue en segundo plano.
            </div>
          )}

          {shown && shown.status === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
              La sincronización falló: {shown.error}
            </div>
          )}

          {shown && shown.status === 'ok' && (
            <div className={`${failed ? 'bg-amber-50 border-amber-200' : 'bg-green-50 border-green-200'} border rounded-lg p-4 space-y-3`}>
              <div className={`flex items-center gap-2 font-medium ${failed ? 'text-amber-900' : 'text-green-900'}`}>
                {failed ? <AlertCircle className="w-5 h-5" /> : <CheckCircle className="w-5 h-5" />}
                {failed ? 'Sincronización terminada con errores' : 'Sincronización terminada'}
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {summarizeRun(shown).map(({ key, label, value }) => (
                  <div key={key} className="bg-white rounded p-2 text-center">
                    <div className="text-xl font-bold text-gray-900">{value}</div>
                    <div className="text-xs text-gray-600">{label}</div>
                  </div>
                ))}
              </div>
              {shown.stats?.warnings?.length > 0 && (
                <details className="text-sm text-amber-800">
                  <summary>{shown.stats.warnings.length} avisos</summary>
                  <ul className="list-disc ml-5 mt-1">
                    {shown.stats.warnings.map((warning) => <li key={warning}>{warning}</li>)}
                  </ul>
                </details>
              )}
              {failed > 0 && (
                <details className="text-sm text-red-700">
                  <summary>
                    {failed} gastos no se pudieron importar
                    {failed > (shown.stats.errors?.length ?? 0) && ` (se muestran los primeros ${shown.stats.errors?.length ?? 0})`}
                  </summary>
                  <ul className="list-disc ml-5 mt-1">
                    {shown.stats.errors.map((item) => (
                      <li key={item.expense_id}>Gasto {item.expense_id}: {item.error}</li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          )}

          {!run && lastRun && (
            <p className="text-xs text-gray-500">
              Última sincronización: {formatRunDate(lastRun.started_at)} ·{' '}
              {lastRun.status === 'ok' ? 'OK' : lastRun.status === 'error' ? 'con error' : 'en curso'}
              {lastRun.params && ` · ${lastRun.params.start_date} a ${lastRun.params.end_date}`}
            </p>
          )}
        </div>

        <div className="p-4 border-t bg-gray-50 flex gap-3 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg">
            Cerrar
          </button>
          <button
            onClick={handleSync}
            disabled={starting || running}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${starting || running ? 'animate-spin' : ''}`} />
            {running ? 'Sincronizando…' : 'Sincronizar gastos'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FudoSyncExpensesModal;
