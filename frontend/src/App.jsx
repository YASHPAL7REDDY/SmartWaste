import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import { PageLoading } from './components/LoadingState'

// Public pages
import { Home } from './pages/Home'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { RegisterSuccess } from './pages/RegisterSuccess'
import { About } from './pages/About'

// User pages
import { UserDashboard } from './pages/UserDashboard'
import { CollectWaste } from './pages/CollectWaste'
import { SubmitSuccess } from './pages/SubmitSuccess'
import { MySubmissions } from './pages/MySubmissions'
import { Predictions } from './pages/Predictions'
import { Profile } from './pages/Profile'

// Admin pages
import { AdminDashboard } from './pages/AdminDashboard'
import { AdminMap } from './pages/AdminMap'
import { AdminExport } from './pages/AdminExport'
import { AdminAreaDetail } from './pages/AdminAreaDetail'
import { AdminAnalytics } from './pages/AdminAnalytics'
import { AdminFacilities } from './pages/AdminFacilities'
import { AdminCollectors } from './pages/AdminCollectors'
import { AdminMLPerformance } from './pages/AdminMLPerformance'

// Collector pages
import { CollectorDashboard } from './pages/CollectorDashboard'
import { CollectorCollections } from './pages/CollectorCollections'
import { CollectorMap } from './pages/CollectorMap'
import { CollectorFacilities } from './pages/CollectorFacilities'
import { CollectorVehicleDetails } from './pages/CollectorVehicleDetails'

function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, role, loading } = useAuth()
  
  if (loading) {
    return <PageLoading />
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  if (allowedRoles && !allowedRoles.includes(role)) {
    return <Navigate to="/" replace />
  }
  
  return children
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/register-success" element={<RegisterSuccess />} />
      <Route path="/about" element={<About />} />
      
      {/* User routes */}
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute allowedRoles={['user']}>
            <UserDashboard />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/collect" 
        element={
          <ProtectedRoute allowedRoles={['user']}>
            <CollectWaste />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/submit-success" 
        element={
          <ProtectedRoute allowedRoles={['user']}>
            <SubmitSuccess />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/my-data" 
        element={
          <ProtectedRoute allowedRoles={['user']}>
            <MySubmissions />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/predictions" 
        element={
          <ProtectedRoute allowedRoles={['user']}>
            <Predictions />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/profile" 
        element={
          <ProtectedRoute allowedRoles={['user']}>
            <Profile />
          </ProtectedRoute>
        } 
      />
      
      {/* Collector routes */}
      <Route 
        path="/collector" 
        element={
          <ProtectedRoute allowedRoles={['collector']}>
            <CollectorDashboard />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/collector/collections" 
        element={
          <ProtectedRoute allowedRoles={['collector']}>
            <CollectorCollections />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/collector/map" 
        element={
          <ProtectedRoute allowedRoles={['collector']}>
            <CollectorMap />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/collector/vehicle" 
        element={
          <ProtectedRoute allowedRoles={['collector']}>
            <CollectorVehicleDetails />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/collector/facilities" 
        element={
          <ProtectedRoute allowedRoles={['collector']}>
            <CollectorFacilities />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/collector/*" 
        element={
          <ProtectedRoute allowedRoles={['collector']}>
            <CollectorDashboard />
          </ProtectedRoute>
        } 
      />
      
      {/* Admin routes */}
      <Route 
        path="/admin" 
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminDashboard />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/admin/analytics" 
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminAnalytics />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/admin/facilities" 
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminFacilities />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/admin/collectors" 
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminCollectors />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/admin/map" 
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminMap />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/admin/export" 
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminExport />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/admin/area/:area" 
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminAreaDetail />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/admin/ml-performance" 
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminMLPerformance />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/admin/*" 
        element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AdminDashboard />
          </ProtectedRoute>
        } 
      />
      
      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return <AppRoutes />
}