import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './hooks/useAuth'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import TicketsPage from './pages/TicketsPage'
import NewTicketPage from './pages/NewTicketPage'
import TicketDetailPage from './pages/TicketDetailPage'
import DocumentsPage from './pages/DocumentsPage'
import AskPage from './pages/AskPage'
import AnalyticsPage from './pages/AnalyticsPage'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected */}
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/tickets" element={<TicketsPage />} />
              <Route path="/tickets/new" element={<NewTicketPage />} />
              <Route path="/tickets/:id" element={<TicketDetailPage />} />
              <Route path="/documents" element={<DocumentsPage />} />
              <Route path="/ask" element={<AskPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
            </Route>
          </Route>

          {/* Default redirect */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" toastOptions={{ duration: 4000 }} />
    </AuthProvider>
  )
}
