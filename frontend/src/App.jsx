import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/layout/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Schedules from './pages/Schedules'
import MySchedule from './pages/MySchedule'
import TimeTracking from './pages/TimeTracking'
import Sales from './pages/Sales'
import Expenses from './pages/Expenses'
import Reports from './pages/Reports'
import Employees from './pages/Employees'
import EmployeeForm from './pages/EmployeeForm'
import EmployeeDetail from './pages/EmployeeDetail'
import JobPositions from './pages/JobPositions'
import MLDashboard from './pages/MLDashboard'
import Payroll from './pages/Payroll'
import PayrollDetail from './pages/PayrollDetail'
import PayrollClaims from './pages/PayrollClaims'
import MyPayrolls from './pages/MyPayrolls'
import MyPayrollDetail from './pages/MyPayrollDetail'
import ImportTimeTracking from './pages/ImportTimeTracking'
import Profile from './pages/Profile'
import HolidaysPage from './pages/HolidaysPage'
import ExpenseCategories from './pages/ExpenseCategories'
import StoreHours from './pages/StoreHours'
import VacationPeriods from './pages/VacationPeriods'
import MyAbsenceRequests from './pages/MyAbsenceRequests'
import AbsenceRequestsAdmin from './pages/AbsenceRequestsAdmin'
import AdminTimeTracking from './pages/AdminTimeTracking'
import MyDocuments from './pages/MyDocuments'
import Menu from './pages/Menu'
import MenuInbox from './pages/MenuInbox'
import { RoleProtectedRoute } from './components/RoleProtectedRoute'
import Permissions from './pages/Permissions'

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/schedules" element={<RoleProtectedRoute moduleName="Schedules"><Schedules /></RoleProtectedRoute>} />
            <Route path="/my-schedule" element={<MySchedule />} />
            <Route path="/time-tracking" element={<TimeTracking />} />
            <Route path="/admin-time-tracking" element={<RoleProtectedRoute moduleName="Schedules"><AdminTimeTracking /></RoleProtectedRoute>} />
            <Route path="/import-time-tracking" element={<RoleProtectedRoute moduleName="Schedules"><ImportTimeTracking /></RoleProtectedRoute>} />
            <Route path="/sales" element={<RoleProtectedRoute moduleName="Sales"><Sales /></RoleProtectedRoute>} />
            <Route path="/expenses" element={<RoleProtectedRoute moduleName="Expenses"><Expenses /></RoleProtectedRoute>} />
            <Route path="/expense-categories" element={<RoleProtectedRoute moduleName="Expenses"><ExpenseCategories /></RoleProtectedRoute>} />
            <Route path="/reports" element={<RoleProtectedRoute moduleName="Reports"><Reports /></RoleProtectedRoute>} />
            <Route path="/employees" element={<RoleProtectedRoute moduleName="Employees"><Employees /></RoleProtectedRoute>} />
            <Route path="/employees/new" element={<RoleProtectedRoute moduleName="Employees"><EmployeeForm /></RoleProtectedRoute>} />
            <Route path="/employees/:id" element={<RoleProtectedRoute moduleName="Employees"><EmployeeDetail /></RoleProtectedRoute>} />
            <Route path="/employees/:id/edit" element={<RoleProtectedRoute moduleName="Employees"><EmployeeForm /></RoleProtectedRoute>} />
            <Route path="/job-positions" element={<RoleProtectedRoute moduleName="Employees"><JobPositions /></RoleProtectedRoute>} />
            <Route path="/ml-dashboard" element={<RoleProtectedRoute moduleName="Reports"><MLDashboard /></RoleProtectedRoute>} />
            <Route path="/payroll" element={<RoleProtectedRoute moduleName="Payroll"><Payroll /></RoleProtectedRoute>} />
            <Route path="/payroll/:id" element={<RoleProtectedRoute moduleName="Payroll"><PayrollDetail /></RoleProtectedRoute>} />
            <Route path="/payroll-claims" element={<RoleProtectedRoute moduleName="Payroll"><PayrollClaims /></RoleProtectedRoute>} />
            <Route path="/my-payrolls" element={<MyPayrolls />} />
            <Route path="/my-payrolls/:id" element={<MyPayrollDetail />} />
            <Route path="/my-documents" element={<MyDocuments />} />
            <Route path="/my-absence-requests" element={<MyAbsenceRequests />} />
            <Route path="/absence-requests" element={<RoleProtectedRoute adminOnly><AbsenceRequestsAdmin /></RoleProtectedRoute>} />
            <Route path="/holidays" element={<RoleProtectedRoute moduleName="Schedules"><HolidaysPage /></RoleProtectedRoute>} />
            <Route path="/store-hours" element={<RoleProtectedRoute moduleName="Schedules"><StoreHours /></RoleProtectedRoute>} />
            <Route path="/vacation-periods" element={<RoleProtectedRoute moduleName="Schedules"><VacationPeriods /></RoleProtectedRoute>} />
            <Route path="/menu" element={<RoleProtectedRoute moduleName="Menu"><Menu /></RoleProtectedRoute>} />
            <Route path="/menu/inbox" element={<RoleProtectedRoute moduleName="Menu"><MenuInbox /></RoleProtectedRoute>} />
            <Route path="/permissions" element={<RoleProtectedRoute adminOnly><Permissions /></RoleProtectedRoute>} />
            <Route path="/profile" element={<Profile />} />
          </Route>
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
