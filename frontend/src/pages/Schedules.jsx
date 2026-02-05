import { useState } from 'react'
import { Calendar, BarChart3 } from 'lucide-react'
import ScheduleList from '@/components/schedules/ScheduleList'
import ScheduleGrid from '@/components/schedules/ScheduleGrid'
import CreateScheduleModal from '@/components/schedules/CreateScheduleModal'
import CoverageCalendar from '@/components/schedules/CoverageCalendar'
import { format, startOfWeek, endOfWeek } from 'date-fns'

const Schedules = () => {
  const [selectedSchedule, setSelectedSchedule] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [activeTab, setActiveTab] = useState('schedules') // 'schedules' or 'coverage'
  const [coverageDates, setCoverageDates] = useState({
    start: format(startOfWeek(new Date(), { weekStartsOn: 1 }), 'yyyy-MM-dd'),
    end: format(endOfWeek(new Date(), { weekStartsOn: 1 }), 'yyyy-MM-dd')
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
    <div className="space-y-6">
      <div className="flex items-center space-x-4 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('schedules')}
          className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
            activeTab === 'schedules'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          <Calendar className="h-5 w-5" />
          <span>Grillas</span>
        </button>
        <button
          onClick={() => setActiveTab('coverage')}
          className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
            activeTab === 'coverage'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-gray-600 hover:text-gray-900'
          }`}
        >
          <BarChart3 className="h-5 w-5" />
          <span>Cobertura</span>
        </button>
      </div>

      {activeTab === 'schedules' ? (
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
      ) : (
        <div className="space-y-4">
          <div className="flex items-center space-x-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Desde
              </label>
              <input
                type="date"
                value={coverageDates.start}
                onChange={(e) => setCoverageDates({ ...coverageDates, start: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Hasta
              </label>
              <input
                type="date"
                value={coverageDates.end}
                onChange={(e) => setCoverageDates({ ...coverageDates, end: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
          
          <CoverageCalendar
            startDate={coverageDates.start}
            endDate={coverageDates.end}
          />
        </div>
      )}
    </div>
  )
}

export default Schedules
