import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
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

export default function App() {
  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
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
              <Route path="jobs" element={<JobsPage />} />
              <Route path="jobs/:jobId" element={<JobDetailPage />} />
              <Route path="crew" element={<CrewPage />} />
              <Route path="crew/:crewId" element={<CrewDetailPage />} />
              <Route path="equipment" element={<EquipmentPage />} />
              <Route path="calendar" element={<CalendarPage />} />
              {/* Portal routes (crew role) */}
              <Route path="portal" element={<PortalPage />} />
              <Route path="portal/jobs/:jobId" element={<PortalJobDetailPage />} />
            </Route>
          </Routes>
        </AuthProvider>
      </QueryClientProvider>
    </BrowserRouter>
  );
}
