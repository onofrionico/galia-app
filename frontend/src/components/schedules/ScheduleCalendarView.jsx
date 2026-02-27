import { useState } from 'react';
import { format, parseISO, eachDayOfInterval } from 'date-fns';
import { es } from 'date-fns/locale';
import { Calendar, Download, Printer } from 'lucide-react';

const ScheduleCalendarView = ({ schedule, scheduleData, employees }) => {
  const [selectedView, setSelectedView] = useState('week'); // 'week' or 'month'

  if (!scheduleData || !employees) {
    return <div className="p-8 text-center text-gray-500">Cargando...</div>;
  }

  const dates = eachDayOfInterval({
    start: parseISO(scheduleData.start_date),
    end: parseISO(scheduleData.end_date),
  });

  const getShiftsForDate = (date) => {
    const dateStr = format(date, 'yyyy-MM-dd');
    return scheduleData.shifts?.filter(shift => shift.shift_date === dateStr) || [];
  };

  const handlePrint = () => {
    window.print();
  };

  const handleExportPDF = () => {
    // Esta funcionalidad requeriría una librería como jsPDF o html2pdf
    alert('Exportar a PDF - Funcionalidad a implementar con jsPDF');
  };

  return (
    <div className="space-y-4">
      {/* Header con controles */}
      <div className="flex items-center justify-between print:hidden">
        <h3 className="text-xl font-semibold text-gray-900">Vista de Calendario</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setSelectedView('week')}
            className={`px-3 py-1 text-sm rounded ${
              selectedView === 'week'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Semana
          </button>
          <button
            onClick={() => setSelectedView('month')}
            className={`px-3 py-1 text-sm rounded ${
              selectedView === 'month'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Mes
          </button>
          <div className="h-6 w-px bg-gray-300 mx-2" />
          <button
            onClick={handlePrint}
            className="flex items-center gap-2 px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            title="Imprimir"
          >
            <Printer size={16} />
            Imprimir
          </button>
          <button
            onClick={handleExportPDF}
            className="flex items-center gap-2 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            title="Exportar a PDF"
          >
            <Download size={16} />
            PDF
          </button>
        </div>
      </div>

      {/* Título para impresión */}
      <div className="hidden print:block mb-4">
        <h1 className="text-2xl font-bold text-gray-900">
          Grilla de Horarios
        </h1>
        <p className="text-gray-600">
          {format(parseISO(scheduleData.start_date), 'dd MMMM', { locale: es })} - {format(parseISO(scheduleData.end_date), 'dd MMMM yyyy', { locale: es })}
        </p>
      </div>

      {/* Vista de calendario */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="grid grid-cols-7 gap-px bg-gray-200">
          {/* Headers de días */}
          {['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'].map((day, idx) => (
            <div key={idx} className="bg-gray-50 px-2 py-3 text-center text-sm font-semibold text-gray-700">
              {day}
            </div>
          ))}

          {/* Celdas de días */}
          {dates.map((date) => {
            const shifts = getShiftsForDate(date);
            const dayOfWeek = date.getDay();
            const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;

            return (
              <div
                key={date.toISOString()}
                className={`bg-white p-2 min-h-[120px] print:min-h-[100px] ${
                  isWeekend ? 'bg-gray-50' : ''
                }`}
              >
                <div className="text-sm font-semibold text-gray-900 mb-2">
                  {format(date, 'd')}
                </div>
                <div className="space-y-1">
                  {shifts.map((shift) => {
                    const employee = employees.find(e => e.id === shift.employee_id);
                    return (
                      <div
                        key={shift.id}
                        className="text-xs bg-blue-100 border border-blue-300 rounded px-1 py-0.5 print:break-inside-avoid"
                      >
                        <div className="font-medium text-blue-900 truncate">
                          {employee?.full_name || 'Empleado'}
                        </div>
                        <div className="text-blue-700">
                          {shift.start_time.substring(0, 5)} - {shift.end_time.substring(0, 5)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Resumen por empleado */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 print:break-before-page">
        <h4 className="text-lg font-semibold text-gray-900 mb-3">Resumen por Empleado</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {employees.map((employee) => {
            const employeeShifts = scheduleData.shifts?.filter(s => s.employee_id === employee.id) || [];
            const totalHours = employeeShifts.reduce((sum, shift) => sum + parseFloat(shift.hours || 0), 0);
            const totalDays = new Set(employeeShifts.map(s => s.shift_date)).size;

            if (totalHours === 0) return null;

            return (
              <div key={employee.id} className="border border-gray-200 rounded p-3">
                <div className="font-medium text-gray-900">{employee.full_name}</div>
                <div className="text-sm text-gray-600 mt-1">
                  <div>Horas: {totalHours.toFixed(1)}h</div>
                  <div>Días: {totalDays}</div>
                  <div>Turnos: {employeeShifts.length}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Estilos para impresión */}
      <style jsx>{`
        @media print {
          @page {
            size: landscape;
            margin: 1cm;
          }
          
          body {
            print-color-adjust: exact;
            -webkit-print-color-adjust: exact;
          }
        }
      `}</style>
    </div>
  );
};

export default ScheduleCalendarView;
