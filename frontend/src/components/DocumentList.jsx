import { 
  FileText, 
  Download,
  Calendar,
  DollarSign,
  CheckCircle,
  Clock,
  AlertCircle,
  XCircle
} from 'lucide-react';

const DocumentList = ({ documents, onDownload, emptyMessage }) => {
  const getDocumentIcon = (type) => {
    switch (type) {
      case 'payroll':
        return <DollarSign className="w-5 h-5 text-green-600" />;
      case 'social_security':
        return <FileText className="w-5 h-5 text-blue-600" />;
      case 'absence':
        return <Calendar className="w-5 h-5 text-orange-600" />;
      default:
        return <FileText className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusBadge = (document) => {
    if (document.type === 'payroll') {
      if (document.status === 'validated') {
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <CheckCircle className="w-3 h-3" />
            Validado
          </span>
        );
      } else if (document.status === 'draft') {
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            <Clock className="w-3 h-3" />
            Borrador
          </span>
        );
      }
    }

    if (document.type === 'absence') {
      if (document.status === 'approved') {
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <CheckCircle className="w-3 h-3" />
            Aprobado
          </span>
        );
      } else if (document.status === 'rejected') {
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
            <XCircle className="w-3 h-3" />
            Rechazado
          </span>
        );
      } else if (document.status === 'pending') {
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            <Clock className="w-3 h-3" />
            Pendiente
          </span>
        );
      }
    }

    return null;
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '';
    
    const kb = bytes / 1024;
    if (kb < 1024) {
      return `${kb.toFixed(1)} KB`;
    }
    
    const mb = kb / 1024;
    return `${mb.toFixed(1)} MB`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  if (!documents || documents.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        <FileText className="w-12 h-12 mx-auto mb-3 text-gray-400" />
        <p>{emptyMessage || 'No hay documentos disponibles'}</p>
      </div>
    );
  }

  return (
    <div className="divide-y">
      {documents.map((document, index) => (
        <div key={`${document.type}_${document.reference_id}_${index}`} className="p-4 md:p-6 hover:bg-gray-50 transition-colors">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                {getDocumentIcon(document.type)}
                <h3 className="font-semibold text-gray-900">
                  {document.title}
                </h3>
                {getStatusBadge(document)}
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-sm mt-3">
                <div>
                  <span className="text-gray-600">Período:</span>
                  <p className="font-medium text-gray-900">{document.period}</p>
                </div>
                
                {document.file_size && (
                  <div>
                    <span className="text-gray-600">Tamaño:</span>
                    <p className="font-medium text-gray-900">{formatFileSize(document.file_size)}</p>
                  </div>
                )}
                
                {document.created_at && (
                  <div>
                    <span className="text-gray-600">Fecha:</span>
                    <p className="font-medium text-gray-900">{formatDate(document.created_at)}</p>
                  </div>
                )}
                
                {document.type === 'payroll' && document.gross_salary && (
                  <div>
                    <span className="text-gray-600">Sueldo bruto:</span>
                    <p className="font-bold text-green-600">
                      ${document.gross_salary.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                )}
                
                {document.type === 'absence' && document.start_date && (
                  <div>
                    <span className="text-gray-600">Desde:</span>
                    <p className="font-medium text-gray-900">{formatDate(document.start_date)}</p>
                  </div>
                )}
                
                {document.type === 'absence' && document.end_date && (
                  <div>
                    <span className="text-gray-600">Hasta:</span>
                    <p className="font-medium text-gray-900">{formatDate(document.end_date)}</p>
                  </div>
                )}
              </div>

              {document.type === 'absence' && document.justification && (
                <div className="mt-3 text-sm">
                  <span className="text-gray-600">Justificación:</span>
                  <p className="text-gray-900 mt-1">{document.justification}</p>
                </div>
              )}

              {document.notes && (
                <div className="mt-3 text-sm">
                  <span className="text-gray-600">Notas:</span>
                  <p className="text-gray-900 mt-1">{document.notes}</p>
                </div>
              )}
            </div>

            <div className="flex flex-col sm:flex-row gap-2">
              <button
                onClick={() => onDownload(document)}
                className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span>Descargar</span>
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default DocumentList;
