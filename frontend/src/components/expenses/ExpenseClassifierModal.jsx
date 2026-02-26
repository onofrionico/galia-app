import { useState, useEffect } from 'react';
import { X, Tag, Save, RefreshCw, AlertCircle, CheckCircle } from 'lucide-react';
import api from '../../services/api';

const ExpenseClassifierModal = ({ isOpen, onClose, onClassified }) => {
  const [expenses, setExpenses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [classifications, setClassifications] = useState({});
  const [result, setResult] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 50,
    total: 0,
    pages: 0
  });
  const [showOnlyUnclassified, setShowOnlyUnclassified] = useState(true);

  useEffect(() => {
    if (isOpen) {
      fetchData();
    }
  }, [isOpen, pagination.page, showOnlyUnclassified]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [expensesRes, categoriesRes] = await Promise.all([
        api.get(`/expenses/unclassified?page=${pagination.page}&per_page=${pagination.per_page}&only_unclassified=${showOnlyUnclassified}`),
        api.get('/expenses/categories')
      ]);

      setExpenses(expensesRes.data.expenses);
      setCategories(categoriesRes.data);
      setPagination(prev => ({
        ...prev,
        total: expensesRes.data.total,
        pages: expensesRes.data.pages
      }));
      
      const initialClassifications = {};
      expensesRes.data.expenses.forEach(expense => {
        if (expense.category_id) {
          initialClassifications[expense.id] = expense.category_id;
        }
      });
      setClassifications(initialClassifications);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryChange = (expenseId, categoryId) => {
    setClassifications(prev => ({
      ...prev,
      [expenseId]: categoryId
    }));
  };

  const handleSave = async () => {
    const classificationsArray = Object.entries(classifications)
      .filter(([_, categoryId]) => categoryId)
      .map(([expenseId, categoryId]) => ({
        expense_id: parseInt(expenseId),
        category_id: parseInt(categoryId)
      }));

    if (classificationsArray.length === 0) {
      alert('No hay clasificaciones para guardar');
      return;
    }

    setSaving(true);
    setResult(null);

    try {
      const response = await api.post('/expenses/classify', {
        classifications: classificationsArray
      });

      setResult({
        success: true,
        message: response.data.message,
        updated_count: response.data.updated_count,
        errors: response.data.errors
      });

      setClassifications({});
      fetchData();
      
      if (onClassified) {
        onClassified();
      }
    } catch (error) {
      console.error('Error saving classifications:', error);
      setResult({
        success: false,
        message: error.response?.data?.error || 'Error al guardar las clasificaciones'
      });
    } finally {
      setSaving(false);
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

  const getCategoryBadgeColor = (expenseType) => {
    return expenseType === 'directo' 
      ? 'bg-blue-100 text-blue-800' 
      : 'bg-purple-100 text-purple-800';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                <Tag className="w-6 h-6 mr-2 text-emerald-600" />
                Clasificador de Gastos
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Clasifica tus gastos para un mejor análisis financiero
              </p>
            </div>
            <button 
              onClick={onClose} 
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="mt-4 flex items-center gap-3">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={showOnlyUnclassified}
                onChange={(e) => {
                  setShowOnlyUnclassified(e.target.checked);
                  setPagination(prev => ({ ...prev, page: 1 }));
                }}
                className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
              />
              <span className="ml-2 text-sm text-gray-700">
                Mostrar solo gastos sin clasificar
              </span>
            </label>
          </div>

          {result && (
            <div className={`mt-4 p-4 rounded-lg ${result.success ? 'bg-green-50' : 'bg-red-50'}`}>
              <div className="flex items-start">
                {result.success ? (
                  <CheckCircle className="w-5 h-5 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
                )}
                <div className="flex-1">
                  <p className={`text-sm font-medium ${result.success ? 'text-green-800' : 'text-red-800'}`}>
                    {result.message}
                  </p>
                  {result.errors && result.errors.length > 0 && (
                    <ul className="mt-2 text-sm text-red-700 list-disc list-inside">
                      {result.errors.map((error, idx) => (
                        <li key={idx}>{error}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
              <span className="ml-3 text-gray-600">Cargando gastos...</span>
            </div>
          ) : expenses.length === 0 ? (
            <div className="text-center py-12">
              <Tag className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600 text-lg font-medium">
                ¡Excelente! No hay gastos sin clasificar
              </p>
              <p className="text-gray-500 text-sm mt-2">
                Todos tus gastos están clasificados correctamente
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-gray-600">
                  <span className="font-semibold text-gray-900">{pagination.total}</span> {showOnlyUnclassified ? 'gastos sin clasificar' : 'gastos totales'}
                </p>
                <p className="text-sm text-gray-600">
                  <span className="font-semibold text-emerald-600">{Object.keys(classifications).filter(id => {
                    const expense = expenses.find(e => e.id === parseInt(id));
                    return !expense || expense.category_id !== classifications[id];
                  }).length}</span> cambios pendientes
                </p>
              </div>

              {expenses.map((expense) => (
                <div 
                  key={expense.id} 
                  className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:border-emerald-300 transition-colors"
                >
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
                    <div className="lg:col-span-2">
                      <p className="text-xs text-gray-500">Fecha</p>
                      <p className="font-medium text-gray-900">{formatDate(expense.fecha)}</p>
                    </div>

                    <div className="lg:col-span-2">
                      <p className="text-xs text-gray-500">Proveedor</p>
                      <p className="font-medium text-gray-900 truncate">
                        {expense.proveedor || '-'}
                      </p>
                    </div>

                    <div className="lg:col-span-3">
                      <p className="text-xs text-gray-500">Descripción</p>
                      <p className="text-sm text-gray-700 truncate">
                        {expense.comentario || expense.categoria || '-'}
                      </p>
                    </div>

                    <div className="lg:col-span-2">
                      <p className="text-xs text-gray-500">Importe</p>
                      <p className="font-bold text-red-600">{formatCurrency(expense.importe)}</p>
                    </div>

                    <div className="lg:col-span-3">
                      <p className="text-xs text-gray-500 mb-1">
                        {expense.category_id ? 'Reclasificar como' : 'Clasificar como'}
                      </p>
                      <select
                        value={classifications[expense.id] || ''}
                        onChange={(e) => handleCategoryChange(expense.id, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                      >
                        <option value="">Seleccionar categoría...</option>
                        {categories.map((category) => (
                          <option key={category.id} value={category.id}>
                            {category.name} ({category.expense_type})
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {classifications[expense.id] && (
                    <div className="mt-2 pt-2 border-t border-gray-200">
                      <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${
                        getCategoryBadgeColor(
                          categories.find(c => c.id === parseInt(classifications[expense.id]))?.expense_type
                        )
                      }`}>
                        <Tag className="w-3 h-3 mr-1" />
                        {categories.find(c => c.id === parseInt(classifications[expense.id]))?.name}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {expenses.length > 0 && (
          <div className="p-6 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between mb-4">
              <div className="text-sm text-gray-600">
                Página {pagination.page} de {pagination.pages}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                  disabled={pagination.page === 1}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white"
                >
                  Anterior
                </button>
                <button
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                  disabled={pagination.page === pagination.pages}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white"
                >
                  Siguiente
                </button>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-white font-medium"
              >
                Cerrar
              </button>
              <button
                onClick={handleSave}
                disabled={saving || Object.keys(classifications).filter(id => {
                  const expense = expenses.find(e => e.id === parseInt(id));
                  return !expense || expense.category_id !== classifications[id];
                }).length === 0}
                className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium inline-flex items-center justify-center"
              >
                {saving ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Guardando...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Guardar Clasificaciones ({Object.keys(classifications).filter(id => {
                      const expense = expenses.find(e => e.id === parseInt(id));
                      return !expense || expense.category_id !== classifications[id];
                    }).length})
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExpenseClassifierModal;
