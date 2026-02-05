import { useState } from 'react'
import ScheduleList from '@/components/schedules/ScheduleList'
import ScheduleGrid from '@/components/schedules/ScheduleGrid'
import CreateScheduleModal from '@/components/schedules/CreateScheduleModal'

const Schedules = () => {
  const [selectedSchedule, setSelectedSchedule] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)

  if (selectedSchedule) {
    return (
      <ScheduleGrid
        schedule={selectedSchedule}
        onBack={() => setSelectedSchedule(null)}
      />
    )
  }

  return (
    <div>
      <ScheduleList
        onSelectSchedule={setSelectedSchedule}
        onCreateNew={() => setShowCreateModal(true)}
      />
      
      <CreateScheduleModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
      />
    </div>
  )
}

export default Schedules
