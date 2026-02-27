import { useState, useEffect } from 'react';
import vacationService from '../services/vacationService';
import employeeService from '../services/employeeService';
import { Calendar, Plus, Edit2, Trash2, Save, X, AlertCircle } from 'lucide-react';

const VacationPeriods = () => {
  const [vacations, setVacations] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    employee_id: '',
    start_date: '',
    end_date: '',
    status: 'aprobado',
    notes: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [vacationsData, employeesData] = await Promise.all([
        vacationService.getVacationPeriods(),
        employeeService.getEmployees({ include_inactive: false })
      ]);
      setVacations(vacationsData);
      setEmployees(Array.isArray(employeesData) ? employeesData : (employeesData?.employees || []));
    } catch (error) {
      console.error('Error loading data:', error);
      alert('Error al cargar los datos');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (new Date(formData.start_date) > new Date(formData.end_date)) {
      alert('La fecha de inicio debe ser anterior a la fecha de fin');
      return;
    }

    try {
      if (editingId) {
        await vacationService.updateVacationPeriod(editingId, formData);
        alert('Período de vacaciones actualizado exitosamente');
      } else {
        await vacationService.createVacationPeriod(formData);
        alert('Período de vacaciones creado exitosamente');
      }
      resetForm();
      loadData();
    } catch (error) {
      console.error('Error saving vacation period:', error);
      alert(error.response?.data?.error || 'Error al guardar el período de vacaciones');
    }
  };

  const handleEdit = (vacation) => {
    setFormData({
      employee_id: vacation.employee_id,
      start_date: vacation.start_date,
      end_date: vacation.end_date,
      status: vacation.status,
      notes: vacation.notes || ''
    });
    setEditingId(vacation.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Está seguro de eliminar este período de vacaciones?')) return;
    
    try {
      await vacationService.deleteVacationPeriod(id);
      alert('Período de vacaciones eliminado exitosamente');
      loadData();
    } catch (error) {
      console.error('Error deleting vacation period:', error);
      alert('Error al eliminar el período de vacaciones');
    }
  };

  const resetForm = () => {
    setFormData({
      employee_id: '',
      start_date: '',
      end_date: '',
      status: 'aprobado',
      notes: ''
    });
    setEditingId(null);
    setShowForm(false);
  };

  const getStatusBadge = (status) => {
    const config = {
      solicitado: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Solicitado' },
      aprobado: { bg: 'bg-green-100', text: 'text-green-800', label: 'Aprobado' },
      rechazado: { bg: 'bg-red-100', text: 'text-red-800', label: 'Rechazado' }
    };
    const style = config[status] || config.aprobado;
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${style.bg} ${style.text}`}>
        {style.label}
      </span>
    );
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-AR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const calculateDays = (startDate, endDate) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
    return diffDays;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Períodos de Vacaciones</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          {showForm ? <X size={20} /> : <Plus size={20} />}
          {showForm ? 'Cancelar' : 'Nuevo Período'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">
            {editingId ? 'Editar Período de Vacaciones' : 'Nuevo Período de Vacaciones'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Empleado *
                </label>
                <select
                  value={formData.employee_id}
                  onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Seleccionar empleado</option>
                  {employees.map(emp => (
                    <option key={emp.id} value={emp.id}>
                      {emp.first_name} {emp.last_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Estado
                </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="solicitado">Solicitado</option>
                  <option value="aprobado">Aprobado</option>
                  <option value="rechazado">Rechazado</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fecha de Inicio *
                </label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Fecha de Fin *
                </label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notas
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  rows="3"
                  placeholder="Observaciones adicionales..."
                />
              </div>
            </div>

            {formData.start_date && formData.end_date && (
              <div className="flex items-center gap-2 text-sm text-gray-600 bg-blue-50 p-3 rounded-lg">
                <AlertCircle size={18} className="text-blue-600" />
                <span>
                  Duración: {calculateDays(formData.start_date, formData.end_date)} días
                </span>
              </div>
            )}

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={resetForm}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                <Save size={18} />
                {editingId ? 'Actualizar' : 'Guardar'}
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-500">Cargando períodos de vacaciones...</div>
      ) : vacations.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center text-gray-500">
          No hay períodos de vacaciones registrados
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Empleado</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Inicio</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Fin</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase">Días</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase">Estado</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Notas</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {vacations.map((vacation) => (
                  <tr key={vacation.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {vacation.employee_name}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {formatDate(vacation.start_date)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {formatDate(vacation.end_date)}
                    </td>
                    <td className="px-4 py-3 text-sm text-center font-medium">
                      {calculateDays(vacation.start_date, vacation.end_date)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {getStatusBadge(vacation.status)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {vacation.notes || '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => handleEdit(vacation)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Editar"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button
                          onClick={() => handleDelete(vacation.id)}
                          className="text-red-600 hover:text-red-800"
                          title="Eliminar"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default VacationPeriods;
