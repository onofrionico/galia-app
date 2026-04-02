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
  FileText,
  AlertTriangle
} from 'lucide-react';

const MyPayrollDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [payroll, setPayroll] = useState(null);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [showClaimModal, setShowClaimModal] = useState(false);
  const [claimReason, setClaimReason] = useState('');
  const [submittingClaim, setSubmittingClaim] = useState(false);
  const [claims, setClaims] = useState([]);

  const months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];

  useEffect(() => {
    loadPayrollDetail();
    loadClaims();
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

  const loadClaims = async () => {
    try {
      const data = await payrollService.getMyPayrollClaims(id);
      setClaims(data);
    } catch (error) {
      console.error('Error loading claims:', error);
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

  const handleSubmitClaim = async () => {
    if (!claimReason.trim()) {
      alert('Por favor ingrese un motivo para el reclamo');
      return;
    }

    try {
      setSubmittingClaim(true);
      await payrollService.createPayrollClaim(id, claimReason);
      alert('Reclamo enviado exitosamente');
      setShowClaimModal(false);
      setClaimReason('');
      loadClaims();
      loadPayrollDetail();
    } catch (error) {
      console.error('Error submitting claim:', error);
      alert('Error al enviar el reclamo: ' + (error.response?.data?.error || error.message));
    } finally {
      setSubmittingClaim(false);
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
  const hasPendingClaim = claims.some(c => c.status === 'pending');
  const canClaim = isValidatedByAdmin && !isValidatedByEmployee && !hasPendingClaim;

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
            
            {canClaim && (
              <button
                onClick={() => setShowClaimModal(true)}
                className="flex items-center justify-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
              >
                <AlertTriangle className="w-4 h-4" />
                Reclamar
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

      {hasPendingClaim && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-orange-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-orange-900">Reclamo pendiente</h3>
              <p className="text-sm text-orange-800 mt-1">
                Has enviado un reclamo sobre esta nómina. El administrador lo revisará y te responderá pronto.
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
                Por favor revisa los detalles de tu nómina. Si estás de acuerdo, acéptala. Si no, puedes hacer un reclamo.
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
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {(() => {
              const allDates = new Set([
                ...(payroll.daily_records || []).map(r => r.date),
                ...(payroll.scheduled_records || []).map(r => r.date)
              ]);
              const sortedDates = Array.from(allDates).sort();
              
              return sortedDates.map((date) => {
                const workedRecords = (payroll.daily_records || []).filter(r => r.date === date);
                const scheduledRecords = (payroll.scheduled_records || []).filter(r => r.date === date);
                
                return (
                  <div key={date} className="border rounded-lg p-4 bg-gray-50">
                    <h4 className="font-semibold text-gray-900 mb-3">
                      {new Date(date + 'T00:00:00').toLocaleDateString('es-AR', { 
                        weekday: 'long', 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                      })}
                    </h4>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      <div>
                        <h5 className="text-sm font-medium text-blue-600 mb-2 flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          Horas Trabajadas
                        </h5>
                        {workedRecords.length > 0 ? (
                          <div className="space-y-1">
                            {workedRecords.map((record, idx) => (
                              <div key={idx}>
                                {record.blocks && record.blocks.length > 0 ? (
                                  record.blocks.map((block) => (
                                    <div key={block.id} className="flex justify-between items-center bg-blue-50 p-2 rounded text-sm">
                                      <span>{block.start_time} - {block.end_time}</span>
                                      <span className="font-semibold text-blue-600">{block.hours.toFixed(2)}h</span>
                                    </div>
                                  ))
                                ) : (
                                  <div className="flex justify-between items-center bg-blue-50 p-2 rounded text-sm">
                                    <span>Total del día</span>
                                    <span className="font-semibold text-blue-600">{record.hours.toFixed(2)}h</span>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-gray-500 text-sm italic">Sin registros</p>
                        )}
                      </div>
                      
                      <div>
                        <h5 className="text-sm font-medium text-purple-600 mb-2 flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          Horas Grilla
                        </h5>
                        {scheduledRecords.length > 0 ? (
                          <div className="space-y-1">
                            {scheduledRecords.map((record, idx) => (
                              <div key={idx} className="flex justify-between items-center bg-purple-50 p-2 rounded text-sm">
                                <span>{record.start_time} - {record.end_time}</span>
                                <span className="font-semibold text-purple-600">{record.hours.toFixed(2)}h</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-gray-500 text-sm italic">Sin turnos programados</p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              });
            })()}
          </div>
        </div>
      </div>

      {/* Notas */}
      {payroll.notes && (
        <div className="bg-white rounded-lg shadow mb-6">
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

      {/* Claims History */}
      {claims.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 md:p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              Historial de Reclamos
            </h2>
          </div>
          <div className="p-4 md:p-6">
            <div className="space-y-4">
              {claims.map((claim) => (
                <div key={claim.id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      claim.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      claim.status === 'approved' ? 'bg-green-100 text-green-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {claim.status === 'pending' ? 'Pendiente' :
                       claim.status === 'approved' ? 'Aprobado' : 'Rechazado'}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(claim.created_at).toLocaleDateString('es-AR')}
                    </span>
                  </div>
                  <div className="mb-2">
                    <p className="text-sm font-semibold text-gray-700">Tu reclamo:</p>
                    <p className="text-sm text-gray-600">{claim.claim_reason}</p>
                  </div>
                  {claim.admin_response && (
                    <div className="bg-gray-50 rounded p-3 mt-2">
                      <p className="text-sm font-semibold text-gray-700">Respuesta del administrador:</p>
                      <p className="text-sm text-gray-600">{claim.admin_response}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Claim Modal */}
      {showClaimModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Reclamar Nómina</h3>
            <p className="text-sm text-gray-600 mb-4">
              Por favor describe el motivo de tu reclamo. El administrador lo revisará y podrá ajustar la nómina si es necesario.
            </p>
            <textarea
              value={claimReason}
              onChange={(e) => setClaimReason(e.target.value)}
              placeholder="Describe el motivo de tu reclamo..."
              className="w-full border rounded-lg p-3 mb-4 h-32 resize-none"
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setShowClaimModal(false);
                  setClaimReason('');
                }}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                disabled={submittingClaim}
              >
                Cancelar
              </button>
              <button
                onClick={handleSubmitClaim}
                disabled={submittingClaim}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-400"
              >
                {submittingClaim ? 'Enviando...' : 'Enviar Reclamo'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyPayrollDetail;
