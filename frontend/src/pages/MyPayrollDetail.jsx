import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import payrollService from '../services/payrollService';
import { 
  ArrowLeft,
  Calendar,
  Clock,
  DollarSign,
  CheckCircle,
  AlertCircle,
  Download,
  FileText
} from 'lucide-react';

const MyPayrollDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [payroll, setPayroll] = useState(null);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);

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
      const data = await payrollService.getMyPayrollDetail(id);
      setPayroll(data);
    } catch (error) {
      console.error('Error loading payroll detail:', error);
      alert('Error al cargar el detalle de la nómina');
      navigate('/my-payrolls');
    } finally {
      setLoading(false);
    }
  };

  const handleValidate = async () => {
    if (!confirm('¿Confirma que acepta esta nómina? Esta acción no se puede deshacer.')) {
      return;
    }

    try {
      setValidating(true);
      await payrollService.validateMyPayroll(id);
      alert('Nómina aceptada exitosamente');
      loadPayrollDetail();
    } catch (error) {
      console.error('Error validating payroll:', error);
      alert('Error al aceptar la nómina: ' + (error.response?.data?.error || error.message));
    } finally {
      setValidating(false);
    }
  };

  const handleDownloadPDF = async () => {
    try {
      const blob = await payrollService.downloadMyPayrollPDF(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `nomina_${payroll.month}_${payroll.year}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Error al descargar el PDF');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Cargando...</div>
      </div>
    );
  }

  if (!payroll) {
    return null;
  }

  const isValidatedByAdmin = payroll.status === 'validated';
  const isValidatedByEmployee = !!payroll.employee_validated_at;
  const canValidate = isValidatedByAdmin && !isValidatedByEmployee;

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/my-payrolls')}
          className="flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver a Mis Nóminas
        </button>
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
              Nómina - {months[payroll.month - 1]} {payroll.year}
            </h1>
            <p className="text-gray-600 mt-1">{payroll.employee_name}</p>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            {payroll.pdf_generated && (
              <button
                onClick={handleDownloadPDF}
                className="flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                <Download className="w-4 h-4" />
                Descargar PDF
              </button>
            )}
            
            {canValidate && (
              <button
                onClick={handleValidate}
                disabled={validating}
                className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                <CheckCircle className="w-4 h-4" />
                {validating ? 'Aceptando...' : 'Aceptar Nómina'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Status Alert */}
      {!isValidatedByAdmin && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-yellow-900">Nómina en proceso</h3>
              <p className="text-sm text-yellow-800 mt-1">
                Esta nómina aún no ha sido validada por el administrador. Podrás aceptarla una vez que sea validada.
              </p>
            </div>
          </div>
        </div>
      )}

      {isValidatedByEmployee && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-green-900">Nómina aceptada</h3>
              <p className="text-sm text-green-800 mt-1">
                Aceptaste esta nómina el {new Date(payroll.employee_validated_at).toLocaleDateString('es-AR')}
              </p>
            </div>
          </div>
        </div>
      )}

      {canValidate && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-900">Acción requerida</h3>
              <p className="text-sm text-blue-800 mt-1">
                Por favor revisa los detalles de tu nómina y acéptala si estás de acuerdo con los datos.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-3 mb-2">
            <Clock className="w-5 h-5 text-blue-600" />
            <span className="text-sm text-gray-600">Horas Trabajadas</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{payroll.hours_worked.toFixed(2)}h</p>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-3 mb-2">
            <Calendar className="w-5 h-5 text-purple-600" />
            <span className="text-sm text-gray-600">Horas Programadas</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{payroll.scheduled_hours.toFixed(2)}h</p>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-3 mb-2">
            <AlertCircle className="w-5 h-5 text-orange-600" />
            <span className="text-sm text-gray-600">Diferencia</span>
          </div>
          <p className={`text-2xl font-bold ${payroll.hours_difference >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {payroll.hours_difference >= 0 ? '+' : ''}{payroll.hours_difference.toFixed(2)}h
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-3 mb-2">
            <DollarSign className="w-5 h-5 text-green-600" />
            <span className="text-sm text-gray-600">Sueldo Bruto</span>
          </div>
          <p className="text-2xl font-bold text-green-600">
            ${payroll.gross_salary.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
          </p>
        </div>
      </div>

      {/* Comparación de horas */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="p-4 md:p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Detalle de Horas</h2>
        </div>
        <div className="p-4 md:p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Horas Trabajadas */}
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
                            <div key={block.id} className="flex justify-between">
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

            {/* Horas Programadas */}
            <div>
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-purple-600" />
                Horas Programadas (Grilla)
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

      {/* Notas */}
      {payroll.notes && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 md:p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Notas
            </h2>
          </div>
          <div className="p-4 md:p-6">
            <p className="text-gray-700 whitespace-pre-wrap">{payroll.notes}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyPayrollDetail;
