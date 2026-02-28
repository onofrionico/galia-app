import { useState, useEffect } from 'react'
import { Calendar, CheckCircle, XCircle, Clock, Download, Filter, User } from 'lucide-react'
import { absenceRequestService } from '../services/absenceRequestService'

const AbsenceRequestsAdmin = () => {
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('pending')
  const [selectedRequest, setSelectedRequest] = useState(null)
  const [showReviewModal, setShowReviewModal] = useState(false)
  const [reviewNotes, setReviewNotes] = useState('')
  const [processing, setProcessing] = useState(false)
  const [pendingCount, setPendingCount] = useState(0)

  useEffect(() => {
    loadRequests()
    loadPendingCount()
  }, [filter])

  const loadRequests = async () => {
    try {
      setLoading(true)
      const params = filter !== 'all' ? { status: filter } : {}
      const data = await absenceRequestService.getAllRequests(params)
      setRequests(data)
      setError(null)
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar solicitudes')
    } finally {
      setLoading(false)
    }
  }

  const loadPendingCount = async () => {
    try {
      const data = await absenceRequestService.getPendingCount()
      setPendingCount(data.pending_count)
    } catch (err) {
      console.error('Error loading pending count:', err)
    }
  }

  const handleApprove = async () => {
    if (!selectedRequest) return

    setProcessing(true)
    try {
      await absenceRequestService.approveRequest(selectedRequest.id, { review_notes: reviewNotes })
      setShowReviewModal(false)
      setSelectedRequest(null)
      setReviewNotes('')
      loadRequests()
      loadPendingCount()
    } catch (err) {
      alert(err.response?.data?.error || 'Error al aprobar solicitud')
    } finally {
      setProcessing(false)
    }
  }

  const handleReject = async () => {
    if (!selectedRequest) return
    if (!reviewNotes.trim()) {
      alert('Debe proporcionar una razón para el rechazo')
      return
    }

    setProcessing(true)
    try {
      await absenceRequestService.rejectRequest(selectedRequest.id, { review_notes: reviewNotes })
      setShowReviewModal(false)
      setSelectedRequest(null)
      setReviewNotes('')
      loadRequests()
      loadPendingCount()
    } catch (err) {
      alert(err.response?.data?.error || 'Error al rechazar solicitud')
    } finally {
      setProcessing(false)
    }
  }

  const openReviewModal = (request, action) => {
    setSelectedRequest({ ...request, action })
    setReviewNotes('')
    setShowReviewModal(true)
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { color: 'bg-yellow-100 text-yellow-800', icon: Clock, label: 'Pendiente' },
      approved: { color: 'bg-green-100 text-green-800', icon: CheckCircle, label: 'Aprobada' },
      rejected: { color: 'bg-red-100 text-red-800', icon: XCircle, label: 'Rechazada' }
    }
    const config = statusConfig[status] || statusConfig.pending
    const Icon = config.icon

    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${config.color}`}>
        <Icon className="w-4 h-4" />
        {config.label}
      </span>
    )
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  const calculateDays = (startDate, endDate) => {
    const start = new Date(startDate)
    const end = new Date(endDate)
    const diffTime = Math.abs(end - start)
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1
    return diffDays
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Solicitudes de Ausencia</h1>
          {pendingCount > 0 && (
            <p className="text-sm text-gray-600 mt-1">
              {pendingCount} solicitud{pendingCount !== 1 ? 'es' : ''} pendiente{pendingCount !== 1 ? 's' : ''}
            </p>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Filtrar por estado:</span>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setFilter('pending')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'pending'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Pendientes {filter === 'pending' && `(${requests.length})`}
          </button>
          <button
            onClick={() => setFilter('approved')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'approved'
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Aprobadas {filter === 'approved' && `(${requests.length})`}
          </button>
          <button
            onClick={() => setFilter('rejected')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'rejected'
                ? 'bg-red-100 text-red-800'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Rechazadas {filter === 'rejected' && `(${requests.length})`}
          </button>
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'all'
                ? 'bg-blue-100 text-blue-800'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Todas {filter === 'all' && `(${requests.length})`}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      <div className="grid gap-4">
        {requests.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
            <Calendar className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p>No hay solicitudes de ausencia {filter !== 'all' ? `en estado "${filter}"` : ''}</p>
          </div>
        ) : (
          requests.map((request) => (
            <div key={request.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <User className="w-5 h-5 text-gray-500" />
                    <h3 className="text-lg font-semibold text-gray-900">
                      {request.employee.full_name}
                    </h3>
                    {getStatusBadge(request.status)}
                  </div>
                  <p className="text-sm text-gray-600 ml-8">
                    {request.employee.job_position || 'Sin puesto asignado'} - DNI: {request.employee.dni}
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-sm font-medium text-gray-700 mb-1">Período de ausencia:</p>
                  <p className="text-gray-900">
                    {formatDate(request.start_date)} - {formatDate(request.end_date)}
                    <span className="text-gray-600 ml-2">
                      ({calculateDays(request.start_date, request.end_date)} día{calculateDays(request.start_date, request.end_date) !== 1 ? 's' : ''})
                    </span>
                  </p>
                </div>

                <div>
                  <p className="text-sm font-medium text-gray-700 mb-1">Justificación:</p>
                  <p className="text-gray-900">{request.justification}</p>
                </div>

                {request.has_attachment && (
                  <div>
                    <button
                      onClick={() => absenceRequestService.downloadAttachment(request.id)}
                      className="text-blue-600 hover:text-blue-800 flex items-center gap-2 text-sm"
                    >
                      <Download className="w-4 h-4" />
                      Descargar comprobante ({request.attachment_filename})
                    </button>
                  </div>
                )}

                {request.status === 'pending' && (
                  <div className="flex gap-3 pt-3 border-t">
                    <button
                      onClick={() => openReviewModal(request, 'approve')}
                      className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
                    >
                      <CheckCircle className="w-5 h-5" />
                      Aprobar
                    </button>
                    <button
                      onClick={() => openReviewModal(request, 'reject')}
                      className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center gap-2"
                    >
                      <XCircle className="w-5 h-5" />
                      Rechazar
                    </button>
                  </div>
                )}

                {request.status !== 'pending' && (
                  <div className="border-t pt-3 mt-3">
                    <p className="text-sm font-medium text-gray-700 mb-1">
                      Revisado el: {new Date(request.reviewed_at).toLocaleString('es-AR')}
                    </p>
                    {request.reviewed_by && (
                      <p className="text-sm text-gray-600 mb-2">
                        Por: {request.reviewed_by.email}
                      </p>
                    )}
                    {request.review_notes && (
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-1">Observaciones:</p>
                        <p className="text-gray-900">{request.review_notes}</p>
                      </div>
                    )}
                  </div>
                )}

                <p className="text-xs text-gray-500">
                  Solicitado el: {new Date(request.created_at).toLocaleString('es-AR')}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      {showReviewModal && selectedRequest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full">
            <div className="p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                {selectedRequest.action === 'approve' ? 'Aprobar' : 'Rechazar'} Solicitud
              </h2>

              <div className="bg-gray-50 p-4 rounded-lg mb-4">
                <p className="text-sm text-gray-700">
                  <strong>Empleado:</strong> {selectedRequest.employee.full_name}
                </p>
                <p className="text-sm text-gray-700">
                  <strong>Período:</strong> {formatDate(selectedRequest.start_date)} - {formatDate(selectedRequest.end_date)}
                </p>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Observaciones {selectedRequest.action === 'reject' && '*'}
                </label>
                <textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows="4"
                  placeholder={selectedRequest.action === 'reject' ? 'Explique el motivo del rechazo...' : 'Observaciones opcionales...'}
                  required={selectedRequest.action === 'reject'}
                />
              </div>

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => {
                    setShowReviewModal(false)
                    setSelectedRequest(null)
                    setReviewNotes('')
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                  disabled={processing}
                >
                  Cancelar
                </button>
                <button
                  onClick={selectedRequest.action === 'approve' ? handleApprove : handleReject}
                  className={`px-4 py-2 rounded-lg text-white transition-colors disabled:opacity-50 ${
                    selectedRequest.action === 'approve'
                      ? 'bg-green-600 hover:bg-green-700'
                      : 'bg-red-600 hover:bg-red-700'
                  }`}
                  disabled={processing}
                >
                  {processing ? 'Procesando...' : selectedRequest.action === 'approve' ? 'Aprobar' : 'Rechazar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AbsenceRequestsAdmin
