import { useState, useEffect } from 'react';
import employeeDocumentsService from '../services/employeeDocumentsService';
import DocumentList from '../components/DocumentList';
import { 
  FileText, 
  Download,
  Calendar,
  Filter
} from 'lucide-react';

const MyDocuments = () => {
  const [activeTab, setActiveTab] = useState('all');
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedMonth, setSelectedMonth] = useState('');

  const months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];

  const tabs = [
    { id: 'all', label: 'Todos', icon: FileText },
    { id: 'payroll', label: 'Recibos de Sueldo', icon: FileText },
    { id: 'social_security', label: 'Cargas Sociales', icon: FileText },
    { id: 'absence', label: 'Ausencias', icon: FileText }
  ];

  useEffect(() => {
    loadDocuments();
  }, [activeTab, selectedYear, selectedMonth]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const params = {
        year: selectedYear
      };

      if (selectedMonth) {
        params.month = selectedMonth;
      }

      if (activeTab !== 'all') {
        params.type = activeTab;
      }

      const data = await employeeDocumentsService.getMyDocuments(params);
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error loading documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (document) => {
    try {
      const documentType = document.type;
      const documentId = document.reference_id;
      
      console.log('Descargando documento:', { type: documentType, id: documentId, fileName: document.file_name });
      
      const blob = await employeeDocumentsService.downloadDocument(documentType, documentId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = document.file_name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading document:', error);
      
      let errorMessage = 'Error al descargar el documento';
      
      if (error.response?.status === 404) {
        errorMessage = 'Documento no encontrado. El archivo puede no estar disponible en el servidor.';
      } else if (error.response?.status === 403) {
        errorMessage = 'No tienes permisos para descargar este documento.';
      } else if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (!error.response) {
        errorMessage = 'No se puede conectar con el servidor. Verifica que el backend esté ejecutándose.';
      }
      
      alert(errorMessage);
    }
  };

  const getYearOptions = () => {
    const currentYear = new Date().getFullYear();
    const years = [];
    for (let i = 0; i < 5; i++) {
      years.push(currentYear - i);
    }
    return years;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Cargando documentos...</div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">Mis Recibos</h1>
        <p className="text-gray-600">Accede a todos tus documentos laborales en un solo lugar</p>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow mb-6 p-4 md:p-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-600" />
          <h2 className="text-lg font-semibold text-gray-900">Filtros</h2>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Año</label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {getYearOptions().map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mes</label>
            <select
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Todos</option>
              {months.map((month, idx) => (
                <option key={idx} value={idx + 1}>{month}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center gap-2 px-4 md:px-6 py-3 border-b-2 font-medium text-sm whitespace-nowrap
                    transition-colors
                    ${isActive 
                      ? 'border-blue-600 text-blue-600' 
                      : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Document List */}
        <DocumentList 
          documents={documents} 
          onDownload={handleDownload}
          emptyMessage={`No hay ${activeTab === 'all' ? 'documentos' : tabs.find(t => t.id === activeTab)?.label.toLowerCase()} disponibles para el período seleccionado`}
        />
      </div>
    </div>
  );
};

export default MyDocuments;
