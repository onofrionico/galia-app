import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import payrollService from '../services/payrollService';
import { 
  ArrowLeft, 
  Calendar, 
  Clock, 
  DollarSign, 
  User, 
  CheckCircle, 
  Edit2, 
  Trash2, 
  Save,
  X,
  FileText,
  Download,
  AlertCircle
} from 'lucide-react';

const PayrollDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [payroll, setPayroll] = useState(null);
  const [workBlocks, setWorkBlocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingBlock, setEditingBlock] = useState(null);
  const [notes, setNotes] = useState('');
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [validating, setValidating] = useState(false);
  const [generatingPDF, setGeneratingPDF] = useState(false);

  const months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];

  useEffect(() => {
    loadPayrollDetail();
  }, [id]);

  const loadPayrollDetail = async () => {
    try {
      setLoading(true);
      const [payrollData, blocksData] = await Promise.all([
        payrollService.getPayrollDetail(id),
        payrollService.getWorkBlocks(id)
      ]);
      setPayroll(payrollData);
      setWorkBlocks(blocksData);
      setNotes(payrollData.notes || '');
    } catch (error) {
      console.error('Error loading payroll detail:', error);
      alert('Error al cargar el detalle de la nómina');
    } finally {
      setLoading(false);
    }
  };

  const handleValidate = async () => {
    if (!confirm('¿Está seguro de validar esta nómina? Una vez validada no se podrá modificar.')) {
      return;
    }

    try {
      setValidating(true);
      await payrollService.validatePayroll(id);
      alert('Nómina validada exitosamente');
      loadPayrollDetail();
    } catch (error) {
      console.error('Error validating payroll:', error);
      alert(error.response?.data?.error || 'Error al validar la nómina');
    } finally {
      setValidating(false);
    }
  };

  const handleGeneratePDF = async () => {
    try {
      setGeneratingPDF(true);
      const blob = await payrollService.generatePDF(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `nomina_${payroll.employee_name}_${payroll.year}_${payroll.month}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      loadPayrollDetail();
    } catch (error) {
      console.error('Error generating PDF:', error);
      alert('Error al generar el PDF');
    } finally {
      setGeneratingPDF(false);
    }
  };

  const handleDownloadPDF = async () => {
    try {
      const blob = await payrollService.downloadPDF(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `nomina_${payroll.employee_name}_${payroll.year}_${payroll.month}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Error al descargar el PDF');
    }
  };

  const handleUpdateNotes = async () => {
    try {
      await payrollService.updatePayroll(id, { notes });
      setIsEditingNotes(false);
      alert('Observaciones actualizadas');
      loadPayrollDetail();
    } catch (error) {
      console.error('Error updating notes:', error);
      alert('Error al actualizar las observaciones');
    }
  };

  const handleRecalculate = async () => {
    if (!confirm('¿Recalcular las horas y el sueldo? Esto actualizará los valores con los datos más recientes.')) {
      return;
    }

    try {
      await payrollService.updatePayroll(id, { recalculate: true });
      alert('Nómina recalculada exitosamente');
      loadPayrollDetail();
    } catch (error) {
      console.error('Error recalculating:', error);
      alert('Error al recalcular la nómina');
    }
  };

  const formatTimeForInput = (timeStr) => {
    // Convert "HH:MM:SS" to "HH:MM" for time input
    if (!timeStr) return '';
    return timeStr.substring(0, 5);
  };

  const handleEditBlock = (block) => {
    setEditingBlock({
      id: block.id,
      start_time: formatTimeForInput(block.start_time),
      end_time: formatTimeForInput(block.end_time)
    });
  };

  const handleSaveBlock = async () => {
    try {
      // Ensure time format is HH:MM
      await payrollService.updateWorkBlock(editingBlock.id, {
        start_time: formatTimeForInput(editingBlock.start_time),
        end_time: formatTimeForInput(editingBlock.end_time)
      });
      setEditingBlock(null);
      alert('Bloque actualizado exitosamente');
      loadPayrollDetail();
    } catch (error) {
      console.error('Error updating block:', error);
      alert('Error al actualizar el bloque: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleDeleteBlock = async (blockId) => {
    if (!confirm('¿Está seguro de eliminar este bloque de trabajo?')) {
      return;
    }

    try {
      await payrollService.deleteWorkBlock(blockId);
      alert('Bloque eliminado exitosamente');
      loadPayrollDetail();
    } catch (error) {
      console.error('Error deleting block:', error);
      alert('Error al eliminar el bloque');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Cargando detalle de nómina...</div>
      </div>
    );
  }

  if (!payroll) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-600">Nómina no encontrada</p>
        <button
          onClick={() => navigate('/payroll')}
          className="mt-4 text-blue-600 hover:text-blue-700"
        >
          Volver a Nóminas
        </button>
      </div>
    );
  }

  const isValidated = payroll.status === 'validated';

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto">
      <button
        onClick={() => navigate('/payroll')}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Volver a Nóminas</span>
      </button>

      <div className="bg-white rounded-lg shadow mb-6">
        <div className="p-4 md:p-6 border-b">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{payroll.employee_name}</h1>
              <p className="text-gray-600 mt-1">
                Nómina - {months[payroll.month - 1]} {payroll.year}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {isValidated ? (
                <span className="px-4 py-2 bg-green-100 text-green-800 rounded-lg font-medium flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  Validado
                </span>
              ) : (
                <button
                  onClick={handleValidate}
                  disabled={validating}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 flex items-center gap-2"
                >
                  <CheckCircle className="w-4 h-4" />
                  {validating ? 'Validando...' : 'Validar Nómina'}
                </button>
              )}
              {payroll.pdf_generated ? (
                <button
                  onClick={handleDownloadPDF}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  <span className="hidden sm:inline">Descargar PDF</span>
                </button>
              ) : (
                <button
                  onClick={handleGeneratePDF}
                  disabled={generatingPDF}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 flex items-center gap-2"
                >
                  <FileText className="w-4 h-4" />
                  {generatingPDF ? 'Generando...' : <span className="hidden sm:inline">Generar PDF</span>}
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="p-4 md:p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 text-blue-600 mb-2">
                <Clock className="w-5 h-5" />
                <span className="text-sm font-medium">Horas Trabajadas</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{payroll.hours_worked.toFixed(2)}</p>
            </div>

            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 text-purple-600 mb-2">
                <Calendar className="w-5 h-5" />
                <span className="text-sm font-medium">Horas Grilla</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{payroll.scheduled_hours.toFixed(2)}</p>
            </div>

            <div className={`p-4 rounded-lg ${
              payroll.hours_difference > 0 ? 'bg-green-50' : 
              payroll.hours_difference < 0 ? 'bg-red-50' : 'bg-gray-50'
            }`}>
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className={`w-5 h-5 ${
                  payroll.hours_difference > 0 ? 'text-green-600' : 
                  payroll.hours_difference < 0 ? 'text-red-600' : 'text-gray-600'
                }`} />
                <span className="text-sm font-medium text-gray-700">Diferencia</span>
              </div>
              <p className={`text-2xl font-bold ${
                payroll.hours_difference > 0 ? 'text-green-600' : 
                payroll.hours_difference < 0 ? 'text-red-600' : 'text-gray-600'
              }`}>
                {payroll.hours_difference > 0 ? '+' : ''}{payroll.hours_difference.toFixed(2)}
              </p>
            </div>

            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 text-green-600 mb-2">
                <DollarSign className="w-5 h-5" />
                <span className="text-sm font-medium">Sueldo Bruto</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">${payroll.gross_salary.toFixed(2)}</p>
              <p className="text-xs text-gray-600 mt-1">Tarifa: ${payroll.hourly_rate.toFixed(2)}/hora</p>
            </div>
          </div>

          {payroll.employee_details && (
            <div className="bg-gray-50 p-4 rounded-lg mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">Información del Empleado</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
                <div>
                  <span className="text-gray-600">DNI:</span>
                  <p className="font-medium">{payroll.employee_details.dni}</p>
                </div>
                <div>
                  <span className="text-gray-600">CUIL:</span>
                  <p className="font-medium">{payroll.employee_details.cuil}</p>
                </div>
                <div>
                  <span className="text-gray-600">Puesto:</span>
                  <p className="font-medium">{payroll.employee_details.job_position || 'N/A'}</p>
                </div>
                <div>
                  <span className="text-gray-600">Tipo de relación:</span>
                  <p className="font-medium">{payroll.employee_details.employment_relationship}</p>
                </div>
              </div>
            </div>
          )}

          <div className="bg-gray-50 p-4 rounded-lg mb-6">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-semibold text-gray-900">Observaciones</h3>
              {!isValidated && (
                <button
                  onClick={() => setIsEditingNotes(!isEditingNotes)}
                  className="text-blue-600 hover:text-blue-700 text-sm flex items-center gap-1"
                >
                  {isEditingNotes ? <X className="w-4 h-4" /> : <Edit2 className="w-4 h-4" />}
                  {isEditingNotes ? 'Cancelar' : 'Editar'}
                </button>
              )}
            </div>
            {isEditingNotes ? (
              <div>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="w-full border rounded-lg px-3 py-2 mb-2"
                  placeholder="Agregar observaciones..."
                />
                <button
                  onClick={handleUpdateNotes}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  Guardar
                </button>
              </div>
            ) : (
              <p className="text-gray-700">{payroll.notes || 'Sin observaciones'}</p>
            )}
          </div>

          {!isValidated && (
            <div className="mb-6">
              <button
                onClick={handleRecalculate}
                className="w-full sm:w-auto bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700"
              >
                Recalcular Horas y Sueldo
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow mb-6">
        <div className="p-4 md:p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Comparación: Horas Trabajadas vs Horas Grilla</h2>
        </div>
        <div className="p-4 md:p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Clock className="w-5 h-5 text-blue-600" />
                Horas Trabajadas (Registradas)
              </h3>
              {payroll.daily_records && payroll.daily_records.length > 0 ? (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {payroll.daily_records.map((record, idx) => (
                    <div key={idx} className="border rounded-lg p-3 bg-blue-50">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium text-sm">
                          {new Date(record.date).toLocaleDateString('es-AR')}
                        </span>
                        <span className="font-semibold text-blue-600">
                          {record.hours.toFixed(2)}h
                        </span>
                      </div>
                      {record.blocks && record.blocks.length > 0 && (
                        <div className="space-y-1 text-xs text-gray-600">
                          {record.blocks.map((block) => (
                            <div key={block.id} className="flex justify-between items-center">
                              <span>{block.start_time} - {block.end_time}</span>
                              <span>{block.hours.toFixed(2)}h</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No hay registros de horas trabajadas</p>
              )}
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-purple-600" />
                Horas Grilla (Programadas)
              </h3>
              {payroll.scheduled_records && payroll.scheduled_records.length > 0 ? (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {payroll.scheduled_records.map((record, idx) => (
                    <div key={idx} className="border rounded-lg p-3 bg-purple-50">
                      <div className="flex justify-between items-center">
                        <div>
                          <span className="font-medium text-sm block">
                            {new Date(record.date).toLocaleDateString('es-AR')}
                          </span>
                          <span className="text-xs text-gray-600">
                            {record.start_time} - {record.end_time}
                          </span>
                        </div>
                        <span className="font-semibold text-purple-600">
                          {record.hours.toFixed(2)}h
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No hay turnos programados</p>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-4 md:p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Bloques de Trabajo Detallados</h2>
          {!isValidated && (
            <p className="text-sm text-gray-600 mt-1">
              Puede editar o eliminar bloques de trabajo antes de validar la nómina
            </p>
          )}
        </div>
        <div className="p-4 md:p-6">
          {workBlocks.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No hay bloques de trabajo registrados</p>
          ) : (
            <div className="space-y-4">
              {workBlocks.map((record) => (
                <div key={record.id} className="border rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-3">
                    {new Date(record.date).toLocaleDateString('es-AR', { 
                      weekday: 'long', 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </h4>
                  {record.work_blocks.length === 0 ? (
                    <p className="text-gray-500 text-sm">Sin bloques registrados</p>
                  ) : (
                    <div className="space-y-2">
                      {record.work_blocks.map((block) => (
                        <div key={block.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-gray-50 p-3 rounded">
                          {editingBlock && editingBlock.id === block.id ? (
                            <>
                              <div className="flex gap-2 flex-1">
                                <input
                                  type="time"
                                  value={editingBlock.start_time}
                                  onChange={(e) => setEditingBlock({
                                    ...editingBlock,
                                    start_time: e.target.value
                                  })}
                                  className="border rounded px-2 py-1 text-sm"
                                />
                                <span className="self-center">-</span>
                                <input
                                  type="time"
                                  value={editingBlock.end_time}
                                  onChange={(e) => setEditingBlock({
                                    ...editingBlock,
                                    end_time: e.target.value
                                  })}
                                  className="border rounded px-2 py-1 text-sm"
                                />
                              </div>
                              <div className="flex gap-2">
                                <button
                                  onClick={handleSaveBlock}
                                  className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 flex items-center gap-1"
                                >
                                  <Save className="w-3 h-3" />
                                  Guardar
                                </button>
                                <button
                                  onClick={() => setEditingBlock(null)}
                                  className="bg-gray-300 text-gray-700 px-3 py-1 rounded text-sm hover:bg-gray-400 flex items-center gap-1"
                                >
                                  <X className="w-3 h-3" />
                                  Cancelar
                                </button>
                              </div>
                            </>
                          ) : (
                            <>
                              <div className="flex-1">
                                <span className="font-medium">{block.start_time}</span>
                                <span className="mx-2">-</span>
                                <span className="font-medium">{block.end_time}</span>
                              </div>
                              {!isValidated && (
                                <div className="flex gap-2">
                                  <button
                                    onClick={() => handleEditBlock(block)}
                                    className="text-blue-600 hover:text-blue-700 p-1"
                                    title="Editar"
                                  >
                                    <Edit2 className="w-4 h-4" />
                                  </button>
                                  <button
                                    onClick={() => handleDeleteBlock(block.id)}
                                    className="text-red-600 hover:text-red-700 p-1"
                                    title="Eliminar"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PayrollDetail;
