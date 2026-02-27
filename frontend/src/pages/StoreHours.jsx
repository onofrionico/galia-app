import { useState, useEffect } from 'react';
import storeHoursService from '../services/storeHoursService';
import { Clock, Plus, Edit2, Trash2, Save, X } from 'lucide-react';

const StoreHours = () => {
  const [storeHours, setStoreHours] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    location_name: '',
    day_of_week: 0,
    opening_time: '08:00',
    closing_time: '20:00',
    is_active: true
  });

  const daysOfWeek = [
    { value: 0, label: 'Lunes' },
    { value: 1, label: 'Martes' },
    { value: 2, label: 'Miércoles' },
    { value: 3, label: 'Jueves' },
    { value: 4, label: 'Viernes' },
    { value: 5, label: 'Sábado' },
    { value: 6, label: 'Domingo' }
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [hoursData, locationsData] = await Promise.all([
        storeHoursService.getStoreHours(),
        storeHoursService.getLocations()
      ]);
      setStoreHours(hoursData);
      setLocations(locationsData);
    } catch (error) {
      console.error('Error loading data:', error);
      alert('Error al cargar los datos');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await storeHoursService.updateStoreHours(editingId, formData);
        alert('Horario actualizado exitosamente');
      } else {
        await storeHoursService.createStoreHours(formData);
        alert('Horario creado exitosamente');
      }
      resetForm();
      loadData();
    } catch (error) {
      console.error('Error saving store hours:', error);
      alert(error.response?.data?.error || 'Error al guardar el horario');
    }
  };

  const handleEdit = (hours) => {
    setFormData({
      location_name: hours.location_name,
      day_of_week: hours.day_of_week,
      opening_time: hours.opening_time,
      closing_time: hours.closing_time,
      is_active: hours.is_active
    });
    setEditingId(hours.id);
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Está seguro de eliminar este horario?')) return;
    
    try {
      await storeHoursService.deleteStoreHours(id);
      alert('Horario eliminado exitosamente');
      loadData();
    } catch (error) {
      console.error('Error deleting store hours:', error);
      alert('Error al eliminar el horario');
    }
  };

  const resetForm = () => {
    setFormData({
      location_name: '',
      day_of_week: 0,
      opening_time: '08:00',
      closing_time: '20:00',
      is_active: true
    });
    setEditingId(null);
    setShowForm(false);
  };

  const groupedHours = storeHours.reduce((acc, hour) => {
    if (!acc[hour.location_name]) {
      acc[hour.location_name] = [];
    }
    acc[hour.location_name].push(hour);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Horarios de Local</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          {showForm ? <X size={20} /> : <Plus size={20} />}
          {showForm ? 'Cancelar' : 'Nuevo Horario'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">
            {editingId ? 'Editar Horario' : 'Nuevo Horario'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Local
                </label>
                <input
                  type="text"
                  value={formData.location_name}
                  onChange={(e) => setFormData({ ...formData, location_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                  list="locations"
                />
                <datalist id="locations">
                  {locations.map((loc, idx) => (
                    <option key={idx} value={loc} />
                  ))}
                </datalist>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Día de la Semana
                </label>
                <select
                  value={formData.day_of_week}
                  onChange={(e) => setFormData({ ...formData, day_of_week: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                >
                  {daysOfWeek.map(day => (
                    <option key={day.value} value={day.value}>{day.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Hora de Apertura
                </label>
                <input
                  type="time"
                  value={formData.opening_time}
                  onChange={(e) => setFormData({ ...formData, opening_time: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Hora de Cierre
                </label>
                <input
                  type="time"
                  value={formData.closing_time}
                  onChange={(e) => setFormData({ ...formData, closing_time: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">
                  Activo
                </label>
              </div>
            </div>

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
        <div className="text-center py-8 text-gray-500">Cargando horarios...</div>
      ) : Object.keys(groupedHours).length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center text-gray-500">
          No hay horarios configurados
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedHours).map(([locationName, hours]) => (
            <div key={locationName} className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="p-4 border-b border-gray-200 bg-gray-50">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Clock size={20} />
                  {locationName}
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Día</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Apertura</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Cierre</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase">Estado</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {hours.sort((a, b) => a.day_of_week - b.day_of_week).map((hour) => (
                      <tr key={hour.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">
                          {hour.day_name}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {hour.opening_time}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {hour.closing_time}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            hour.is_active 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {hour.is_active ? 'Activo' : 'Inactivo'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <button
                              onClick={() => handleEdit(hour)}
                              className="text-blue-600 hover:text-blue-800"
                              title="Editar"
                            >
                              <Edit2 size={18} />
                            </button>
                            <button
                              onClick={() => handleDelete(hour.id)}
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
          ))}
        </div>
      )}
    </div>
  );
};

export default StoreHours;
