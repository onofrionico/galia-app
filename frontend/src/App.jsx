import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
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
import MyPayrolls from './pages/MyPayrolls'
import MyPayrollDetail from './pages/MyPayrollDetail'
import ImportTimeTracking from './pages/ImportTimeTracking'
import Profile from './pages/Profile'
import Settings from './pages/Settings'

function App() {
  return (
    <Router>
      <AuthProvider>
        <ThemeProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            
            <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/schedules" element={<Schedules />} />
              <Route path="/my-schedule" element={<MySchedule />} />
              <Route path="/time-tracking" element={<TimeTracking />} />
              <Route path="/import-time-tracking" element={<ImportTimeTracking />} />
              <Route path="/sales" element={<Sales />} />
              <Route path="/expenses" element={<Expenses />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/employees" element={<Employees />} />
              <Route path="/employees/new" element={<EmployeeForm />} />
              <Route path="/employees/:id" element={<EmployeeDetail />} />
              <Route path="/employees/:id/edit" element={<EmployeeForm />} />
              <Route path="/job-positions" element={<JobPositions />} />
              <Route path="/ml-dashboard" element={<MLDashboard />} />
              <Route path="/payroll" element={<Payroll />} />
              <Route path="/payroll/:id" element={<PayrollDetail />} />
              <Route path="/my-payrolls" element={<MyPayrolls />} />
              <Route path="/my-payrolls/:id" element={<MyPayrollDetail />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
          </Routes>
        </ThemeProvider>
      </AuthProvider>
    </Router>
  )
}

export default App
