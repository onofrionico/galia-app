import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import payrollService from '../services/payrollService';
import employeeService from '../services/employeeService';
import { 
  DollarSign, 
  Calendar, 
  Users, 
  TrendingUp, 
  FileText, 
  CheckCircle, 
  Clock,
  AlertCircle,
  Plus,
  Filter,
  Download
} from 'lucide-react';

const Payroll = () => {
  const navigate = useNavigate();
  const [employeesStatus, setEmployeesStatus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [historical, setHistorical] = useState([]);
  
  const currentDate = new Date();
  const [selectedYear, setSelectedYear] = useState(currentDate.getFullYear());
  const [selectedMonth, setSelectedMonth] = useState(currentDate.getMonth() + 1);
  
  const [showNewPayrollModal, setShowNewPayrollModal] = useState(false);
  const [selectedEmployeeForPayroll, setSelectedEmployeeForPayroll] = useState(null);

  const months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];

  useEffect(() => {
    loadData();
  }, [selectedYear, selectedMonth]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      const [employeesData, summaryData, historicalData] = await Promise.all([
        payrollService.getEmployeesPayrollStatus(selectedYear, selectedMonth),
        payrollService.getMonthlySummary(selectedYear, selectedMonth),
        payrollService.getHistoricalSummary(6)
      ]);
      
      setEmployeesStatus(employeesData.employees || []);
      setSummary(summaryData);
      setHistorical(historicalData);
    } catch (error) {
      console.error('Error loading payroll data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = (payrollId) => {
    navigate(`/payroll/${payrollId}`);
  };

  const handleDownloadPDF = async (payrollId, employeeName) => {
    try {
      const blob = await payrollService.downloadPDF(payrollId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `nomina_${employeeName}_${selectedYear}_${selectedMonth}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Error al descargar el PDF');
    }
  };

  const handleDeletePayroll = async (payrollId, employeeName) => {
    if (!window.confirm(`¿Está seguro de eliminar la nómina en borrador de ${employeeName}?`)) {
      return;
    }
    
    try {
      await payrollService.deletePayroll(payrollId);
      alert('Nómina eliminada exitosamente');
      loadData();
    } catch (error) {
      console.error('Error deleting payroll:', error);
      const errorMsg = error.response?.data?.message || 'Error al eliminar la nómina';
      alert(errorMsg);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      draft: 'bg-yellow-100 text-yellow-800',
      validated: 'bg-green-100 text-green-800'
    };
    
    const labels = {
      draft: 'Borrador',
      validated: 'Validado'
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-800'}`}>
        {labels[status] || status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Cargando datos de nómina...</div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Nómina de Sueldos</h1>
          <p className="text-sm md:text-base text-gray-600 mt-1">
            Gestión de sueldos y liquidaciones mensuales
          </p>
        </div>
        <button
          onClick={() => setShowNewPayrollModal(true)}
          className="w-full sm:w-auto bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2"
        >
          <Plus className="w-4 h-4" />
          <span>Nueva Nómina</span>
        </button>
      </div>

      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 md:p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Sueldos</p>
                <p className="text-xl md:text-2xl font-bold text-gray-900">
                  ${summary.total_salary.toFixed(2)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 md:w-10 md:h-10 text-green-600" />
            </div>
          </div>

          <div className="bg-white p-4 md:p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Horas</p>
                <p className="text-xl md:text-2xl font-bold text-gray-900">
                  {summary.total_hours.toFixed(2)}
                </p>
              </div>
              <Clock className="w-8 h-8 md:w-10 md:h-10 text-blue-600" />
            </div>
          </div>

          <div className="bg-white p-4 md:p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Empleados</p>
                <p className="text-xl md:text-2xl font-bold text-gray-900">
                  {summary.employee_count}
                </p>
              </div>
              <Users className="w-8 h-8 md:w-10 md:h-10 text-purple-600" />
            </div>
          </div>

          <div className="bg-white p-4 md:p-6 rounded-lg shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Validados</p>
                <p className="text-xl md:text-2xl font-bold text-gray-900">
                  {summary.validated_count}/{summary.employee_count}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 md:w-10 md:h-10 text-green-600" />
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow mb-6">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Seleccionar Período
          </h2>
        </div>
        <div className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Año</label>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(Number(e.target.value))}
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
                onChange={(e) => setSelectedMonth(Number(e.target.value))}
                className="w-full border rounded-lg px-3 py-2"
              >
                {months.map((month, idx) => (
                  <option key={idx} value={idx + 1}>{month}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {historical.length > 0 && (
        <div className="bg-white rounded-lg shadow mb-6 p-4 md:p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Histórico de Sueldos (Últimos 6 meses)
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-4 text-sm font-medium text-gray-700">Período</th>
                  <th className="text-right py-2 px-4 text-sm font-medium text-gray-700">Total Sueldos</th>
                  <th className="text-right py-2 px-4 text-sm font-medium text-gray-700">Total Horas</th>
                  <th className="text-right py-2 px-4 text-sm font-medium text-gray-700">Empleados</th>
                </tr>
              </thead>
              <tbody>
                {historical.map((item, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-4 text-sm">{item.month_name} {item.year}</td>
                    <td className="py-2 px-4 text-sm text-right font-medium">${item.total_salary.toFixed(2)}</td>
                    <td className="py-2 px-4 text-sm text-right">{item.total_hours.toFixed(2)}</td>
                    <td className="py-2 px-4 text-sm text-right">{item.employee_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            Empleados con Horas Registradas - {months[selectedMonth - 1]} {selectedYear}
          </h2>
        </div>

        {employeesStatus.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Users className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p>No hay empleados con horas registradas en este período</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full hidden md:table">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Empleado</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Puesto</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Horas Trabajadas</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase">Nómina Generada</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase">Estado</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Sueldo Bruto</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase">PDF</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {employeesStatus.map((employee) => (
                  <tr key={employee.employee_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {employee.employee_name}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {employee.job_position || 'Sin puesto'}
                    </td>
                    <td className="px-4 py-3 text-sm text-right">
                      {employee.hours_worked.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {employee.has_payroll ? (
                        <CheckCircle className="w-5 h-5 text-green-600 mx-auto" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-yellow-600 mx-auto" />
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {employee.has_payroll ? (
                        getStatusBadge(employee.payroll_status)
                      ) : (
                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                          Sin generar
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-right font-semibold">
                      {employee.gross_salary ? `$${employee.gross_salary.toFixed(2)}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {employee.pdf_generated ? (
                        <button
                          onClick={() => handleDownloadPDF(employee.payroll_id, employee.employee_name)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Descargar PDF"
                        >
                          <Download className="w-5 h-5 mx-auto" />
                        </button>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {employee.has_payroll ? (
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => handleViewDetail(employee.payroll_id)}
                            className="text-blue-600 hover:text-blue-800 font-medium text-sm"
                          >
                            Ver Detalle
                          </button>
                          {employee.payroll_status === 'draft' && (
                            <button
                              onClick={() => handleDeletePayroll(employee.payroll_id, employee.employee_name)}
                              className="text-red-600 hover:text-red-800 font-medium text-sm"
                              title="Eliminar borrador"
                            >
                              Eliminar
                            </button>
                          )}
                        </div>
                      ) : (
                        <button
                          onClick={() => {
                            setSelectedEmployeeForPayroll(employee);
                            setShowNewPayrollModal(true);
                          }}
                          className="text-green-600 hover:text-green-800 font-medium text-sm"
                        >
                          Generar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="md:hidden divide-y">
              {employeesStatus.map((employee) => (
                <div key={employee.employee_id} className="p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-medium text-gray-900">{employee.employee_name}</div>
                      <div className="text-sm text-gray-600">{employee.job_position || 'Sin puesto'}</div>
                    </div>
                    {employee.has_payroll ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-yellow-600" />
                    )}
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Horas trabajadas:</span>
                      <span className="font-medium">{employee.hours_worked.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Estado nómina:</span>
                      {employee.has_payroll ? (
                        getStatusBadge(employee.payroll_status)
                      ) : (
                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                          Sin generar
                        </span>
                      )}
                    </div>
                    {employee.gross_salary && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Sueldo bruto:</span>
                        <span className="font-semibold text-lg">${employee.gross_salary.toFixed(2)}</span>
                      </div>
                    )}
                  </div>
                  <div className="mt-3 flex gap-2">
                    {employee.has_payroll ? (
                      <>
                        <button
                          onClick={() => handleViewDetail(employee.payroll_id)}
                          className="flex-1 bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700"
                        >
                          Ver Detalle
                        </button>
                        {employee.pdf_generated && (
                          <button
                            onClick={() => handleDownloadPDF(employee.payroll_id, employee.employee_name)}
                            className="bg-gray-100 text-gray-700 px-3 py-2 rounded text-sm hover:bg-gray-200"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                        )}
                        {employee.payroll_status === 'draft' && (
                          <button
                            onClick={() => handleDeletePayroll(employee.payroll_id, employee.employee_name)}
                            className="bg-red-100 text-red-700 px-3 py-2 rounded text-sm hover:bg-red-200"
                            title="Eliminar borrador"
                          >
                            Eliminar
                          </button>
                        )}
                      </>
                    ) : (
                      <button
                        onClick={() => {
                          setSelectedEmployeeForPayroll(employee);
                          setShowNewPayrollModal(true);
                        }}
                        className="flex-1 bg-green-600 text-white px-3 py-2 rounded text-sm hover:bg-green-700"
                      >
                        Generar Nómina
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {showNewPayrollModal && (
        <NewPayrollModal
          preselectedEmployee={selectedEmployeeForPayroll}
          defaultYear={selectedYear}
          defaultMonth={selectedMonth}
          onClose={() => {
            setShowNewPayrollModal(false);
            setSelectedEmployeeForPayroll(null);
          }}
          onSuccess={() => {
            setShowNewPayrollModal(false);
            setSelectedEmployeeForPayroll(null);
            loadData();
          }}
        />
      )}
    </div>
  );
};

const NewPayrollModal = ({ preselectedEmployee, defaultYear, defaultMonth, onClose, onSuccess }) => {
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState(preselectedEmployee?.employee_id || '');
  const [year, setYear] = useState(defaultYear || new Date().getFullYear());
  const [month, setMonth] = useState(defaultMonth || new Date().getMonth() + 1);
  const [notes, setNotes] = useState('');
  const [calculation, setCalculation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);

  const months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];

  useEffect(() => {
    const loadEmployees = async () => {
      try {
        const data = await employeeService.getEmployees();
        setEmployees(Array.isArray(data) ? data : (data?.employees || []));
      } catch (error) {
        console.error('Error loading employees:', error);
      }
    };
    loadEmployees();
  }, []);

  const handleCalculate = async () => {
    if (!selectedEmployee) {
      alert('Seleccione un empleado');
      return;
    }

    try {
      setLoading(true);
      const data = await payrollService.calculatePayroll(selectedEmployee, year, month);
      setCalculation(data);
    } catch (error) {
      console.error('Error calculating payroll:', error);
      alert(error.response?.data?.error || 'Error al calcular la nómina');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      await payrollService.generatePayroll({
        employee_id: selectedEmployee,
        year,
        month,
        notes
      });
      alert('Nómina generada exitosamente');
      onSuccess();
    } catch (error) {
      console.error('Error generating payroll:', error);
      alert(error.response?.data?.error || 'Error al generar la nómina');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 md:p-6 border-b">
          <h2 className="text-xl font-bold text-gray-900">Generar Nueva Nómina</h2>
        </div>

        <div className="p-4 md:p-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Empleado *</label>
              {preselectedEmployee ? (
                <div className="w-full border rounded-lg px-3 py-2 bg-gray-50 text-gray-700">
                  {preselectedEmployee.employee_name}
                </div>
              ) : (
                <select
                  value={selectedEmployee}
                  onChange={(e) => {
                    setSelectedEmployee(e.target.value);
                    setCalculation(null);
                  }}
                  className="w-full border rounded-lg px-3 py-2"
                >
                  <option value="">Seleccionar empleado</option>
                  {employees.filter(e => e.status === 'activo').map(emp => (
                    <option key={emp.id} value={emp.id}>{emp.full_name}</option>
                  ))}
                </select>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Año *</label>
              <select
                value={year}
                onChange={(e) => {
                  setYear(Number(e.target.value));
                  setCalculation(null);
                }}
                className="w-full border rounded-lg px-3 py-2"
              >
                {[2024, 2025, 2026].map(y => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mes *</label>
              <select
                value={month}
                onChange={(e) => {
                  setMonth(Number(e.target.value));
                  setCalculation(null);
                }}
                className="w-full border rounded-lg px-3 py-2"
              >
                {months.map((m, idx) => (
                  <option key={idx} value={idx + 1}>{m}</option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={handleCalculate}
                disabled={loading || !selectedEmployee}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                {loading ? 'Calculando...' : 'Calcular'}
              </button>
            </div>
          </div>

          {calculation && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Resultado del Cálculo</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-gray-600">Horas trabajadas:</span>
                  <p className="font-semibold">{calculation.hours_worked.toFixed(2)}</p>
                </div>
                <div>
                  <span className="text-gray-600">Horas grilla:</span>
                  <p className="font-semibold">{calculation.scheduled_hours.toFixed(2)}</p>
                </div>
                <div>
                  <span className="text-gray-600">Diferencia:</span>
                  <p className={`font-semibold ${
                    calculation.hours_difference > 0 ? 'text-green-600' : 
                    calculation.hours_difference < 0 ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {calculation.hours_difference > 0 ? '+' : ''}{calculation.hours_difference.toFixed(2)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-600">Tarifa horaria:</span>
                  <p className="font-semibold">${calculation.hourly_rate.toFixed(2)}</p>
                </div>
                <div className="col-span-2 pt-2 border-t">
                  <span className="text-gray-600">Sueldo bruto:</span>
                  <p className="text-2xl font-bold text-green-600">${calculation.gross_salary.toFixed(2)}</p>
                </div>
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Observaciones</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="w-full border rounded-lg px-3 py-2"
              placeholder="Notas adicionales sobre esta nómina..."
            />
          </div>
        </div>

        <div className="p-4 md:p-6 border-t flex flex-col sm:flex-row gap-3 justify-end">
          <button
            onClick={onClose}
            className="w-full sm:w-auto px-4 py-2 border rounded-lg hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onClick={handleGenerate}
            disabled={!calculation || generating}
            className="w-full sm:w-auto bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:bg-gray-400"
          >
            {generating ? 'Generando...' : 'Generar Nómina'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Payroll;
