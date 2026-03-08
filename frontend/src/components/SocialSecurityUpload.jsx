import { useState, useEffect } from 'react'
import { Upload, FileText, Download, Trash2, X, Filter, Calendar } from 'lucide-react'
import socialSecurityService from '../services/socialSecurityService'

const SocialSecurityUpload = ({ employeeId, isAdmin = false }) => {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [documentTypes, setDocumentTypes] = useState([])
  const [filters, setFilters] = useState({
    document_type: '',
    period_year: new Date().getFullYear(),
    period_month: ''
  })

  const [uploadForm, setUploadForm] = useState({
    document_type: 'cargas_sociales',
    period_month: new Date().getMonth() + 1,
    period_year: new Date().getFullYear(),
    file: null,
    notes: ''
  })

  useEffect(() => {
    loadDocumentTypes()
    loadDocuments()
  }, [employeeId])

  const loadDocumentTypes = async () => {
    try {
      const data = await socialSecurityService.getDocumentTypes()
      setDocumentTypes(data.document_types || [])
    } catch (err) {
      console.error('Error loading document types:', err)
    }
  }

  const loadDocuments = async () => {
    try {
      setLoading(true)
      const data = await socialSecurityService.getEmployeeDocuments(employeeId, filters)
      setDocuments(data)
      setError(null)
    } catch (err) {
      setError('Error al cargar documentos: ' + (err.response?.data?.error || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      if (file.type !== 'application/pdf') {
        setError('Solo se permiten archivos PDF')
        return
      }
      if (file.size > 10 * 1024 * 1024) {
        setError('El archivo no puede superar los 10MB')
        return
      }
      setUploadForm({ ...uploadForm, file })
      setError(null)
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    
    if (!uploadForm.file) {
      setError('Debe seleccionar un archivo')
      return
    }

    try {
      setLoading(true)
      await socialSecurityService.uploadDocument(
        employeeId,
        uploadForm.document_type,
        uploadForm.period_month,
        uploadForm.period_year,
        uploadForm.file,
        uploadForm.notes
      )
      setSuccess('Documento subido exitosamente')
      setShowUploadModal(false)
      setUploadForm({
        document_type: 'cargas_sociales',
        period_month: new Date().getMonth() + 1,
        period_year: new Date().getFullYear(),
        file: null,
        notes: ''
      })
      loadDocuments()
    } catch (err) {
      setError('Error al subir documento: ' + (err.response?.data?.error || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (documentId, fileName) => {
    try {
      const response = await socialSecurityService.downloadDocument(documentId)
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', fileName)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError('Error al descargar documento: ' + (err.response?.data?.error || err.message))
    }
  }

  const handleDelete = async (documentId) => {
    if (!window.confirm('¿Está seguro de eliminar este documento?')) {
      return
    }

    try {
      await socialSecurityService.deleteDocument(documentId)
      setSuccess('Documento eliminado exitosamente')
      loadDocuments()
    } catch (err) {
      setError('Error al eliminar documento: ' + (err.response?.data?.error || err.message))
    }
  }

  const getDocumentTypeLabel = (type) => {
    const docType = documentTypes.find(dt => dt.value === type)
    return docType ? docType.label : type
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const months = [
    { value: 1, label: 'Enero' },
    { value: 2, label: 'Febrero' },
    { value: 3, label: 'Marzo' },
    { value: 4, label: 'Abril' },
    { value: 5, label: 'Mayo' },
    { value: 6, label: 'Junio' },
    { value: 7, label: 'Julio' },
    { value: 8, label: 'Agosto' },
    { value: 9, label: 'Septiembre' },
    { value: 10, label: 'Octubre' },
    { value: 11, label: 'Noviembre' },
    { value: 12, label: 'Diciembre' }
  ]

  const years = Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <FileText size={20} className="text-gray-400" />
          Documentos de Cargas Sociales
        </h3>
        {isAdmin && (
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Upload size={16} />
            Subir Documento
          </button>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
          <div className="flex items-center justify-between">
            <p className="text-red-700 text-sm">{error}</p>
            <button onClick={() => setError(null)} className="text-red-700 hover:text-red-900">
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded">
          <div className="flex items-center justify-between">
            <p className="text-green-700 text-sm">{success}</p>
            <button onClick={() => setSuccess(null)} className="text-green-700 hover:text-green-900">
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="flex items-center gap-2 mb-3">
          <Filter size={16} className="text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Filtros</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <select
            value={filters.document_type}
            onChange={(e) => setFilters({ ...filters, document_type: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Todos los tipos</option>
            {documentTypes.map(type => (
              <option key={type.value} value={type.value}>{type.label}</option>
            ))}
          </select>
          <select
            value={filters.period_year}
            onChange={(e) => setFilters({ ...filters, period_year: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Todos los años</option>
            {years.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
          <button
            onClick={loadDocuments}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Aplicar Filtros
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-8 text-gray-500">Cargando documentos...</div>
      ) : documents.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No hay documentos disponibles
        </div>
      ) : (
        <div className="space-y-3">
          {documents.map(doc => (
            <div key={doc.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText size={18} className="text-blue-600 flex-shrink-0" />
                    <h4 className="font-medium text-gray-900 truncate">{doc.file_name}</h4>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                    <div>
                      <span className="font-medium">Tipo:</span> {getDocumentTypeLabel(doc.document_type)}
                    </div>
                    <div>
                      <span className="font-medium">Período:</span> {months.find(m => m.value === doc.period_month)?.label} {doc.period_year}
                    </div>
                    <div>
                      <span className="font-medium">Tamaño:</span> {formatFileSize(doc.file_size)}
                    </div>
                    <div>
                      <span className="font-medium">Subido:</span> {new Date(doc.uploaded_at).toLocaleDateString('es-AR')}
                    </div>
                  </div>
                  {doc.notes && (
                    <div className="mt-2 text-sm text-gray-600">
                      <span className="font-medium">Notas:</span> {doc.notes}
                    </div>
                  )}
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <button
                    onClick={() => handleDownload(doc.id, doc.file_name)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="Descargar"
                  >
                    <Download size={18} />
                  </button>
                  {isAdmin && (
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Eliminar"
                    >
                      <Trash2 size={18} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Subir Documento</h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Documento
                </label>
                <select
                  value={uploadForm.document_type}
                  onChange={(e) => setUploadForm({ ...uploadForm, document_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                >
                  {documentTypes.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Mes
                  </label>
                  <select
                    value={uploadForm.period_month}
                    onChange={(e) => setUploadForm({ ...uploadForm, period_month: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  >
                    {months.map(month => (
                      <option key={month.value} value={month.value}>{month.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Año
                  </label>
                  <select
                    value={uploadForm.period_year}
                    onChange={(e) => setUploadForm({ ...uploadForm, period_year: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  >
                    {years.map(year => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Archivo PDF (máx. 10MB)
                </label>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
                {uploadForm.file && (
                  <p className="text-sm text-gray-600 mt-1">
                    Archivo seleccionado: {uploadForm.file.name}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notas (opcional)
                </label>
                <textarea
                  value={uploadForm.notes}
                  onChange={(e) => setUploadForm({ ...uploadForm, notes: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows="3"
                  placeholder="Agregar notas adicionales..."
                />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Subiendo...' : 'Subir Documento'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default SocialSecurityUpload
