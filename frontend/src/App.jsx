import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { NotificationProvider } from './context/NotificationContext'
import ProtectedRoute from './components/ProtectedRoute'
import { RoleProtectedRoute } from './components/RoleProtectedRoute'
import Layout from './components/layout/Layout'
import PosLayout from './components/layout/PosLayout'
import CamareroLayout from './components/layout/CamareroLayout'
import NotificationToast from './components/notifications/NotificationToast'
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
import Suppliers from './pages/Suppliers'
import SupplierDetail from './pages/SupplierDetail'
import Pos from './pages/Pos'
import Camarero from './pages/Camarero'
import CamareroMesa from './pages/CamareroMesa'
import ProductCategories from './pages/ProductCategories'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import Stock from './pages/Stock'
import Supplies from './pages/Supplies'
import POSConfiguration from './pages/POSConfiguration'
import Permissions from './pages/Permissions'
import BrandingConfig from './pages/admin/BrandingConfig'
import BiometricCheckIn from './pages/BiometricCheckIn'

function App() {
  return (
    <Router>
      <AuthProvider>
        <NotificationProvider>
          <NotificationToast />
          <Routes>
          <Route path="/login" element={<Login />} />

          {/* Admin POS — fullscreen layout */}
          <Route element={<ProtectedRoute><PosLayout /></ProtectedRoute>}>
            <Route path="/pos" element={<RoleProtectedRoute moduleName="POS"><Pos /></RoleProtectedRoute>} />
          </Route>

          {/* Camarero — mobile layout */}
          <Route element={<ProtectedRoute><CamareroLayout /></ProtectedRoute>}>
            <Route path="/camarero" element={<Camarero />} />
            <Route path="/camarero/mesa/:mesaId" element={<CamareroMesa />} />
          </Route>

          {/* Regular layout (existing routes) */}
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/schedules" element={<RoleProtectedRoute moduleName="Schedules"><Schedules /></RoleProtectedRoute>} />
            <Route path="/my-schedule" element={<MySchedule />} />
            <Route path="/time-tracking" element={<TimeTracking />} />
            <Route path="/biometric-check-in" element={<BiometricCheckIn />} />
            <Route path="/admin-time-tracking" element={<RoleProtectedRoute moduleName="Schedules"><AdminTimeTracking /></RoleProtectedRoute>} />
            <Route path="/import-time-tracking" element={<RoleProtectedRoute moduleName="Schedules"><ImportTimeTracking /></RoleProtectedRoute>} />
            <Route path="/sales" element={<RoleProtectedRoute moduleName="POS"><Sales /></RoleProtectedRoute>} />
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
            <Route path="/absence-requests" element={<RoleProtectedRoute moduleName="Schedules"><AbsenceRequestsAdmin /></RoleProtectedRoute>} />
            <Route path="/holidays" element={<RoleProtectedRoute moduleName="Employees"><HolidaysPage /></RoleProtectedRoute>} />
            <Route path="/store-hours" element={<StoreHours />} />
            <Route path="/vacation-periods" element={<VacationPeriods />} />
            <Route path="/suppliers" element={<RoleProtectedRoute moduleName="Supplies"><Suppliers /></RoleProtectedRoute>} />
            <Route path="/suppliers/:id" element={<RoleProtectedRoute moduleName="Supplies"><SupplierDetail /></RoleProtectedRoute>} />
            <Route path="/products" element={<RoleProtectedRoute moduleName="Configuration"><Products /></RoleProtectedRoute>} />
            <Route path="/products/:id" element={<RoleProtectedRoute moduleName="Configuration"><ProductDetail /></RoleProtectedRoute>} />
            <Route path="/product-categories" element={<RoleProtectedRoute moduleName="Configuration"><ProductCategories /></RoleProtectedRoute>} />
            <Route path="/stock" element={<RoleProtectedRoute moduleName="Configuration"><Stock /></RoleProtectedRoute>} />
            <Route path="/supplies" element={<RoleProtectedRoute moduleName="Supplies"><Supplies /></RoleProtectedRoute>} />
            <Route path="/pos-configuration" element={<RoleProtectedRoute moduleName="Configuration"><POSConfiguration /></RoleProtectedRoute>} />
            <Route path="/permissions" element={<RoleProtectedRoute moduleName="Configuration"><Permissions /></RoleProtectedRoute>} />
            <Route path="/admin/branding" element={<RoleProtectedRoute moduleName="Configuration"><BrandingConfig /></RoleProtectedRoute>} />
            <Route path="/profile" element={<Profile />} />
          </Route>
        </Routes>
        </NotificationProvider>
      </AuthProvider>
    </Router>
  )
}

export default App
