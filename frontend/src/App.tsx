import { Component, type ErrorInfo, type ReactNode } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from '@/lib/auth';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { AppLayout } from '@/components/layout/AppLayout';
import { LoginPage } from '@/pages/Login';
import { RegisterPage } from '@/pages/Register';
import { DashboardPage } from '@/pages/Dashboard';
import { JobsPage } from '@/pages/Jobs';
import { JobDetailPage } from '@/pages/JobDetail';
import { CrewPage } from '@/pages/Crew';
import { CrewDetailPage } from '@/pages/CrewDetail';
import { EquipmentPage } from '@/pages/Equipment';
import { CalendarPage } from '@/pages/Calendar';
import { PortalPage } from '@/pages/Portal';
import { PortalJobDetailPage } from '@/pages/PortalJobDetail';

class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error('UI Error:', error, info); }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-background">
          <div className="text-center space-y-4">
            <h1 className="text-xl font-semibold">Something went wrong</h1>
            <button onClick={() => { this.setState({ hasError: false }); window.location.reload(); }}
              className="px-4 py-2 rounded bg-accent text-white hover:bg-accent-hover">
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

function RoleBasedDashboard() {
  const { user } = useAuth();
  if (user?.role === 'crew') return <PortalPage />;
  return <DashboardPage />;
}

function AdminOnly({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (!user) return null;
  if (user.role !== 'admin') return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <ErrorBoundary>
            <Toaster position="top-right" theme="dark" />
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Protected routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }>
                <Route index element={<RoleBasedDashboard />} />
                <Route path="jobs" element={<AdminOnly><JobsPage /></AdminOnly>} />
                <Route path="jobs/:jobId" element={<AdminOnly><JobDetailPage /></AdminOnly>} />
                <Route path="crew" element={<AdminOnly><CrewPage /></AdminOnly>} />
                <Route path="crew/:crewId" element={<AdminOnly><CrewDetailPage /></AdminOnly>} />
                <Route path="equipment" element={<AdminOnly><EquipmentPage /></AdminOnly>} />
                <Route path="calendar" element={<AdminOnly><CalendarPage /></AdminOnly>} />
                {/* Portal routes (crew role) */}
                <Route path="portal" element={<PortalPage />} />
                <Route path="portal/jobs/:jobId" element={<PortalJobDetailPage />} />
              </Route>
            </Routes>
          </ErrorBoundary>
        </AuthProvider>
      </QueryClientProvider>
    </BrowserRouter>
  );
}
