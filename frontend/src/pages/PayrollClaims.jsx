import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import payrollService from '../services/payrollService';
import { 
  AlertTriangle,
  Calendar,
  User,
  CheckCircle,
  XCircle,
  Clock,
  FileText
} from 'lucide-react';

const PayrollClaims = () => {
  const navigate = useNavigate();
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('pending');
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [adminResponse, setAdminResponse] = useState('');
  const [action, setAction] = useState('approve');
  const [submitting, setSubmitting] = useState(false);

  const months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];

  useEffect(() => {
    loadClaims();
  }, [filter]);

  const loadClaims = async () => {
    try {
      setLoading(true);
      const params = filter !== 'all' ? { status: filter } : {};
      const data = await payrollService.getAllClaims(params);
      setClaims(data);
    } catch (error) {
      console.error('Error loading claims:', error);
      alert('Error al cargar los reclamos');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (claim) => {
    setSelectedClaim(claim);
    setAdminResponse('');
    setAction('approve');
    setShowModal(true);
  };

  const handleRespondToClaim = async () => {
    if (!adminResponse.trim()) {
      alert('Por favor ingrese una respuesta');
      return;
    }

    try {
      setSubmitting(true);
      await payrollService.respondToClaim(selectedClaim.id, adminResponse, action);
      alert(`Reclamo ${action === 'approve' ? 'aprobado' : 'rechazado'} exitosamente`);
      setShowModal(false);
      loadClaims();
    } catch (error) {
      console.error('Error responding to claim:', error);
      alert('Error al responder el reclamo: ' + (error.response?.data?.error || error.message));
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800'
    };
    const labels = {
      pending: 'Pendiente',
      approved: 'Aprobado',
      rejected: 'Rechazado'
    };
    return (
      <span className={`px-2 py-1 rounded text-xs font-semibold ${badges[status]}`}>
        {labels[status]}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
          Reclamos de Nóminas
        </h1>

        {/* Filters */}
        <div className="flex gap-2">
          <button
            onClick={() => setFilter('pending')}
            className={`px-4 py-2 rounded-lg ${
              filter === 'pending'
                ? 'bg-yellow-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Pendientes
          </button>
          <button
            onClick={() => setFilter('approved')}
            className={`px-4 py-2 rounded-lg ${
              filter === 'approved'
                ? 'bg-green-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Aprobados
          </button>
          <button
            onClick={() => setFilter('rejected')}
            className={`px-4 py-2 rounded-lg ${
              filter === 'rejected'
                ? 'bg-red-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Rechazados
          </button>
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg ${
              filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Todos
          </button>
        </div>
      </div>

      {/* Claims List */}
      {claims.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No hay reclamos {filter !== 'all' ? filter + 's' : ''}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {claims.map((claim) => (
            <div key={claim.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <User className="w-5 h-5 text-gray-600" />
                    <h3 className="font-semibold text-lg">{claim.employee_name}</h3>
                    {getStatusBadge(claim.status)}
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>
                        {claim.payroll ? `${months[claim.payroll.month - 1]} ${claim.payroll.year}` : 'N/A'}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      <span>{new Date(claim.created_at).toLocaleDateString('es-AR')}</span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => navigate(`/payroll/${claim.payroll_id}`)}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                  >
                    Ver Nómina
                  </button>
                  {claim.status === 'pending' && (
                    <button
                      onClick={() => handleOpenModal(claim)}
                      className="px-3 py-1 text-sm bg-orange-600 text-white rounded hover:bg-orange-700"
                    >
                      Responder
                    </button>
                  )}
                </div>
              </div>

              <div className="border-t pt-4">
                <p className="text-sm font-semibold text-gray-700 mb-1">Motivo del reclamo:</p>
                <p className="text-sm text-gray-600 mb-3">{claim.claim_reason}</p>

                {claim.admin_response && (
                  <div className="bg-gray-50 rounded p-3">
                    <p className="text-sm font-semibold text-gray-700 mb-1">Respuesta del administrador:</p>
                    <p className="text-sm text-gray-600">{claim.admin_response}</p>
                    {claim.resolved_at && (
                      <p className="text-xs text-gray-500 mt-2">
                        Resuelto el {new Date(claim.resolved_at).toLocaleDateString('es-AR')}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Response Modal */}
      {showModal && selectedClaim && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Responder Reclamo - {selectedClaim.employee_name}
            </h3>

            <div className="mb-4 p-4 bg-gray-50 rounded">
              <p className="text-sm font-semibold text-gray-700 mb-1">Motivo del reclamo:</p>
              <p className="text-sm text-gray-600">{selectedClaim.claim_reason}</p>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Acción:
              </label>
              <div className="flex gap-4">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="approve"
                    checked={action === 'approve'}
                    onChange={(e) => setAction(e.target.value)}
                    className="mr-2"
                  />
                  <CheckCircle className="w-4 h-4 text-green-600 mr-1" />
                  <span>Aprobar (la nómina volverá a borrador para ajustes)</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="reject"
                    checked={action === 'reject'}
                    onChange={(e) => setAction(e.target.value)}
                    className="mr-2"
                  />
                  <XCircle className="w-4 h-4 text-red-600 mr-1" />
                  <span>Rechazar</span>
                </label>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Respuesta al empleado:
              </label>
              <textarea
                value={adminResponse}
                onChange={(e) => setAdminResponse(e.target.value)}
                placeholder="Escribe tu respuesta al empleado..."
                className="w-full border rounded-lg p-3 h-32 resize-none"
              />
            </div>

            {action === 'approve' && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
                <p className="text-sm text-blue-800">
                  <strong>Nota:</strong> Al aprobar el reclamo, la nómina volverá al estado de borrador.
                  Podrás realizar los ajustes necesarios y luego validarla nuevamente para que el empleado la revise.
                </p>
              </div>
            )}

            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  setShowModal(false);
                  setSelectedClaim(null);
                }}
                className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                disabled={submitting}
              >
                Cancelar
              </button>
              <button
                onClick={handleRespondToClaim}
                disabled={submitting}
                className={`px-4 py-2 text-white rounded-lg disabled:bg-gray-400 ${
                  action === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                {submitting ? 'Procesando...' : action === 'approve' ? 'Aprobar Reclamo' : 'Rechazar Reclamo'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PayrollClaims;
