import { useState, useEffect } from 'react'
import { Calendar, FileText, Upload, X, CheckCircle, XCircle, Clock, Download } from 'lucide-react'
import { absenceRequestService } from '../services/absenceRequestService'

const MyAbsenceRequests = () => {
  const [requests, setRequests] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [formData, setFormData] = useState({
    start_date: '',
    end_date: '',
    justification: '',
    attachment: null
  })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    loadRequests()
  }, [])

  const loadRequests = async () => {
    try {
      setLoading(true)
      const data = await absenceRequestService.getMyRequests()
      setRequests(data)
      setError(null)
    } catch (err) {
      setError(err.response?.data?.error || 'Error al cargar solicitudes')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)

    try {
      const formDataToSend = new FormData()
      formDataToSend.append('start_date', formData.start_date)
      formDataToSend.append('end_date', formData.end_date)
      formDataToSend.append('justification', formData.justification)
      if (formData.attachment) {
        formDataToSend.append('attachment', formData.attachment)
      }

      await absenceRequestService.createRequest(formDataToSend)
      setShowModal(false)
      setFormData({ start_date: '', end_date: '', justification: '', attachment: null })
      loadRequests()
    } catch (err) {
      alert(err.response?.data?.error || 'Error al crear solicitud')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('¿Está seguro de eliminar esta solicitud?')) return

    try {
      await absenceRequestService.deleteRequest(id)
      loadRequests()
    } catch (err) {
      alert(err.response?.data?.error || 'Error al eliminar solicitud')
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf']
      if (!allowedTypes.includes(file.type)) {
        alert('Solo se permiten archivos PNG, JPG o PDF')
        e.target.value = ''
        return
      }
      if (file.size > 5 * 1024 * 1024) {
        alert('El archivo no debe superar 5MB')
        e.target.value = ''
        return
      }
      setFormData({ ...formData, attachment: file })
    }
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
        <h1 className="text-3xl font-bold text-gray-900">Mis Solicitudes de Ausencia</h1>
        <button
          onClick={() => setShowModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Calendar className="w-5 h-5" />
          Nueva Solicitud
        </button>
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
            <p>No tienes solicitudes de ausencia</p>
            <p className="text-sm mt-1">Crea una nueva solicitud para justificar una ausencia</p>
          </div>
        ) : (
          requests.map((request) => (
            <div key={request.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {formatDate(request.start_date)} - {formatDate(request.end_date)}
                    </h3>
                    {getStatusBadge(request.status)}
                  </div>
                  <p className="text-sm text-gray-600">
                    {calculateDays(request.start_date, request.end_date)} día(s)
                  </p>
                </div>
                {request.status === 'pending' && (
                  <button
                    onClick={() => handleDelete(request.id)}
                    className="text-red-600 hover:text-red-800 p-2"
                    title="Eliminar solicitud"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>

              <div className="space-y-3">
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

                {request.status !== 'pending' && (
                  <div className="border-t pt-3 mt-3">
                    <p className="text-sm font-medium text-gray-700 mb-1">
                      Revisado el: {new Date(request.reviewed_at).toLocaleString('es-AR')}
                    </p>
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

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Nueva Solicitud de Ausencia</h2>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Fecha de inicio *
                    </label>
                    <input
                      type="date"
                      value={formData.start_date}
                      onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Fecha de fin *
                    </label>
                    <input
                      type="date"
                      value={formData.end_date}
                      onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Justificación * (mínimo 10 caracteres)
                  </label>
                  <textarea
                    value={formData.justification}
                    onChange={(e) => setFormData({ ...formData, justification: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    rows="4"
                    required
                    minLength="10"
                    placeholder="Describa el motivo de su ausencia..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Comprobante (opcional)
                  </label>
                  <div className="flex items-center gap-3">
                    <label className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 cursor-pointer transition-colors">
                      <Upload className="w-5 h-5" />
                      Seleccionar archivo
                      <input
                        type="file"
                        onChange={handleFileChange}
                        accept=".png,.jpg,.jpeg,.pdf"
                        className="hidden"
                      />
                    </label>
                    {formData.attachment && (
                      <span className="text-sm text-gray-600">{formData.attachment.name}</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Formatos permitidos: PNG, JPG, PDF (máx. 5MB)
                  </p>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                    disabled={submitting}
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                    disabled={submitting}
                  >
                    {submitting ? 'Enviando...' : 'Enviar Solicitud'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MyAbsenceRequests
