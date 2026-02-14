import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Calendar, BarChart3, Clock } from 'lucide-react'
import ScheduleList from '@/components/schedules/ScheduleList'
import ScheduleGrid from '@/components/schedules/ScheduleGrid'
import CreateScheduleModal from '@/components/schedules/CreateScheduleModal'
import CoverageCalendar from '@/components/schedules/CoverageCalendar'
import WorkedHoursCalendar from '@/components/schedules/WorkedHoursCalendar'
import { format, startOfWeek, endOfWeek } from 'date-fns'
import api from '@/services/api'

const Schedules = () => {
  const [selectedSchedule, setSelectedSchedule] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [activeTab, setActiveTab] = useState('schedules') // 'schedules', 'coverage', or 'worked-hours'
  const [coverageDates, setCoverageDates] = useState({
    start: format(startOfWeek(new Date(), { weekStartsOn: 1 }), 'yyyy-MM-dd'),
    end: format(endOfWeek(new Date(), { weekStartsOn: 1 }), 'yyyy-MM-dd')
  })

  const { data: employees = [] } = useQuery({
    queryKey: ['employees-list'],
    queryFn: async () => {
      const response = await api.get('/employees', { params: { limit: 1000 } })
      return response.data.employees || []
    }
  })

  const { data: schedules = [] } = useQuery({
    queryKey: ['schedules-list'],
    queryFn: async () => {
      const response = await api.get('/schedules')
      return response.data
    }
  })

  if (selectedSchedule) {
    return (
      <ScheduleGrid
        schedule={selectedSchedule}
        onBack={() => setSelectedSchedule(null)}
      />
    )
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex items-center space-x-2 md:space-x-4 border-b border-gray-200 overflow-x-auto">
        <button
          onClick={() => setActiveTab('schedules')}
          className={`flex items-center space-x-1 md:space-x-2 px-3 md:px-4 py-2 md:py-3 border-b-2 transition-colors whitespace-nowrap text-sm md:text-base ${
            activeTab === 'schedules'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          <Calendar className="h-4 md:h-5 w-4 md:w-5" />
          <span>Grillas</span>
        </button>
        <button
          onClick={() => setActiveTab('coverage')}
          className={`flex items-center space-x-1 md:space-x-2 px-3 md:px-4 py-2 md:py-3 border-b-2 transition-colors whitespace-nowrap text-sm md:text-base ${
            activeTab === 'coverage'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          <BarChart3 className="h-4 md:h-5 w-4 md:w-5" />
          <span>Cobertura</span>
        </button>
        <button
          onClick={() => setActiveTab('worked-hours')}
          className={`flex items-center space-x-1 md:space-x-2 px-3 md:px-4 py-2 md:py-3 border-b-2 transition-colors whitespace-nowrap text-sm md:text-base ${
            activeTab === 'worked-hours'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          <Clock className="h-4 md:h-5 w-4 md:w-5" />
          <span>Horas Trabajadas</span>
        </button>
      </div>

      {activeTab === 'schedules' && (
        <>
          <ScheduleList
            onSelectSchedule={setSelectedSchedule}
            onCreateNew={() => setShowCreateModal(true)}
          />
          
          <CreateScheduleModal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
          />
        </>
      )}

      {activeTab === 'coverage' && (
        <div className="space-y-3 md:space-y-4">
          <div className="grid grid-cols-2 gap-3 md:gap-4">
            <div>
              <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                Desde
              </label>
              <input
                type="date"
                value={coverageDates.start}
                onChange={(e) => setCoverageDates({ ...coverageDates, start: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-sm"
              />
            </div>
            <div>
              <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                Hasta
              </label>
              <input
                type="date"
                value={coverageDates.end}
                onChange={(e) => setCoverageDates({ ...coverageDates, end: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary text-sm"
              />
            </div>
          </div>
          
          <CoverageCalendar
            startDate={coverageDates.start}
            endDate={coverageDates.end}
          />
        </div>
      )}

      {activeTab === 'worked-hours' && (
        <WorkedHoursCalendar
          employees={employees}
          schedules={schedules}
        />
      )}
    </div>
  )
}

export default Schedules
