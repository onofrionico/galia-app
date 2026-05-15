import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/layout/Layout'
import PosLayout from './components/layout/PosLayout'
import CamareroLayout from './components/layout/CamareroLayout'
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

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Admin POS — fullscreen layout */}
          <Route element={<ProtectedRoute><PosLayout /></ProtectedRoute>}>
            <Route path="/pos" element={<Pos />} />
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
            <Route path="/schedules" element={<Schedules />} />
            <Route path="/my-schedule" element={<MySchedule />} />
            <Route path="/time-tracking" element={<TimeTracking />} />
            <Route path="/admin-time-tracking" element={<AdminTimeTracking />} />
            <Route path="/import-time-tracking" element={<ImportTimeTracking />} />
            <Route path="/sales" element={<Sales />} />
            <Route path="/expenses" element={<Expenses />} />
            <Route path="/expense-categories" element={<ExpenseCategories />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/employees" element={<Employees />} />
            <Route path="/employees/new" element={<EmployeeForm />} />
            <Route path="/employees/:id" element={<EmployeeDetail />} />
            <Route path="/employees/:id/edit" element={<EmployeeForm />} />
            <Route path="/job-positions" element={<JobPositions />} />
            <Route path="/ml-dashboard" element={<MLDashboard />} />
            <Route path="/payroll" element={<Payroll />} />
            <Route path="/payroll/:id" element={<PayrollDetail />} />
            <Route path="/payroll-claims" element={<PayrollClaims />} />
            <Route path="/my-payrolls" element={<MyPayrolls />} />
            <Route path="/my-payrolls/:id" element={<MyPayrollDetail />} />
            <Route path="/my-documents" element={<MyDocuments />} />
            <Route path="/my-absence-requests" element={<MyAbsenceRequests />} />
            <Route path="/absence-requests" element={<AbsenceRequestsAdmin />} />
            <Route path="/holidays" element={<HolidaysPage />} />
            <Route path="/store-hours" element={<StoreHours />} />
            <Route path="/vacation-periods" element={<VacationPeriods />} />
            <Route path="/suppliers" element={<Suppliers />} />
            <Route path="/suppliers/:id" element={<SupplierDetail />} />
            <Route path="/products" element={<Products />} />
            <Route path="/products/:id" element={<ProductDetail />} />
            <Route path="/product-categories" element={<ProductCategories />} />
            <Route path="/stock" element={<Stock />} />
            <Route path="/supplies" element={<Supplies />} />
            <Route path="/pos-configuration" element={<POSConfiguration />} />
            <Route path="/profile" element={<Profile />} />
          </Route>
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
