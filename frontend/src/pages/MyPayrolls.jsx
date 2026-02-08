import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import payrollService from '../services/payrollService';
import { 
  DollarSign, 
  Calendar, 
  CheckCircle, 
  Clock,
  AlertCircle,
  FileText,
  Download,
  Eye
} from 'lucide-react';

const MyPayrolls = () => {
  const navigate = useNavigate();
  const [payrolls, setPayrolls] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const currentDate = new Date();
  const [selectedYear, setSelectedYear] = useState(currentDate.getFullYear());
  const [selectedMonth, setSelectedMonth] = useState('');

  const months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];

  useEffect(() => {
    loadMyPayrolls();
  }, [selectedYear, selectedMonth]);

  const loadMyPayrolls = async () => {
    try {
      setLoading(true);
      const filters = { year: selectedYear };
      if (selectedMonth) filters.month = selectedMonth;
      
      const data = await payrollService.getMyPayrolls(filters);
      setPayrolls(data);
    } catch (error) {
      console.error('Error loading my payrolls:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = (payrollId) => {
    navigate(`/my-payrolls/${payrollId}`);
  };

  const handleDownloadPDF = async (payrollId) => {
    try {
      const blob = await payrollService.downloadMyPayrollPDF(payrollId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `nomina_${payrollId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Error al descargar el PDF');
    }
  };

  const getStatusBadge = (payroll) => {
    if (payroll.employee_validated_at) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
          <CheckCircle className="w-3 h-3" />
          Aceptada
        </span>
      );
    }
    
    if (payroll.status === 'validated') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          <AlertCircle className="w-3 h-3" />
          Pendiente de aceptar
        </span>
      );
    }
    
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
        <Clock className="w-3 h-3" />
        En proceso
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
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">Mis Nóminas</h1>
        <p className="text-gray-600">Consulta tu historial de sueldos y descarga tus recibos</p>
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-lg shadow mb-6 p-4 md:p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Año</label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              className="w-full border rounded-lg px-3 py-2"
            >
              {[2024, 2025, 2026].map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mes</label>
            <select
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
            >
              <option value="">Todos</option>
              {months.map((month, idx) => (
                <option key={idx} value={idx + 1}>{month}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Lista de nóminas */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 md:p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Historial de Nóminas
          </h2>
        </div>

        {payrolls.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p>No hay nóminas disponibles para el período seleccionado</p>
          </div>
        ) : (
          <div className="divide-y">
            {payrolls.map((payroll) => (
              <div key={payroll.id} className="p-4 md:p-6 hover:bg-gray-50 transition-colors">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Calendar className="w-5 h-5 text-blue-600" />
                      <h3 className="font-semibold text-gray-900">
                        {months[payroll.month - 1]} {payroll.year}
                      </h3>
                      {getStatusBadge(payroll)}
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mt-3">
                      <div>
                        <span className="text-gray-600">Horas trabajadas:</span>
                        <p className="font-semibold text-gray-900">{payroll.hours_worked.toFixed(2)}h</p>
                      </div>
                      <div>
                        <span className="text-gray-600">Horas programadas:</span>
                        <p className="font-semibold text-gray-900">{payroll.scheduled_hours.toFixed(2)}h</p>
                      </div>
                      <div>
                        <span className="text-gray-600">Diferencia:</span>
                        <p className={`font-semibold ${payroll.hours_difference >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {payroll.hours_difference >= 0 ? '+' : ''}{payroll.hours_difference.toFixed(2)}h
                        </p>
                      </div>
                      <div>
                        <span className="text-gray-600">Sueldo bruto:</span>
                        <p className="font-bold text-lg text-green-600">
                          ${payroll.gross_salary.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row gap-2">
                    <button
                      onClick={() => handleViewDetail(payroll.id)}
                      className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      <Eye className="w-4 h-4" />
                      <span className="hidden sm:inline">Ver Detalle</span>
                      <span className="sm:hidden">Detalle</span>
                    </button>
                    
                    {payroll.pdf_generated && (
                      <button
                        onClick={() => handleDownloadPDF(payroll.id)}
                        className="flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        <Download className="w-4 h-4" />
                        <span className="hidden sm:inline">Descargar PDF</span>
                        <span className="sm:hidden">PDF</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MyPayrolls;
