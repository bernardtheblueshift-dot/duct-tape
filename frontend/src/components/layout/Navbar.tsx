import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Bell } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';

export function Navbar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const { data: counts } = useQuery({
    queryKey: ['notification-counts'],
    queryFn: () => api.notifications.counts(),
    refetchInterval: 30000,
    enabled: !!user,
  });

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const totalNotifications = (counts?.unread_messages || 0) + (counts?.pending_assignments || 0);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-14 border-b border-border bg-background/95 backdrop-blur">
      <div className="flex items-center justify-between h-full px-4">
        <div className="flex items-center">
          <span className="text-xl font-bold tracking-tight border-l-2 border-dashed border-accent pl-3">
            GT
          </span>
        </div>

        <div className="flex items-center gap-4">
          {/* Notification badge */}
          <button className="relative p-2 hover:bg-surface rounded-md transition-colors">
            <Bell className="w-5 h-5 text-muted-foreground" />
            {totalNotifications > 0 && (
              <span className="absolute top-0.5 right-0.5 flex items-center justify-center min-w-[18px] h-[18px] text-[10px] font-bold bg-destructive text-destructive-foreground rounded-full px-1">
                {totalNotifications}
              </span>
            )}
          </button>

          {/* User menu */}
          <div className="flex items-center gap-3">
            <span className="text-sm font-mono text-muted-foreground">
              {user?.name || user?.email}
            </span>
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-primary hover:bg-surface rounded-md transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
