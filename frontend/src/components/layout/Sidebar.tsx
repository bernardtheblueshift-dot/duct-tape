import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Briefcase, Users, Wrench, CalendarDays, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { cn } from '@/lib/utils';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navigationItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard, adminOnly: false },
  { path: '/jobs', label: 'Jobs', icon: Briefcase, adminOnly: true },
  { path: '/crew', label: 'Crew', icon: Users, adminOnly: true },
  { path: '/equipment', label: 'Equipment', icon: Wrench, adminOnly: true },
  { path: '/calendar', label: 'Calendar', icon: CalendarDays, adminOnly: true },
];

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const visibleItems = navigationItems.filter(item => !item.adminOnly || isAdmin);

  return (
    <aside
      className={cn(
        'fixed top-14 left-0 bottom-0 bg-surface border-r border-border transition-all duration-200 z-40',
        'max-md:hidden',
        collapsed ? 'w-16' : 'w-56'
      )}
    >
      <nav className="flex flex-col h-full">
        <div className="flex-1 py-4 space-y-1">
          {visibleItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-4 py-2.5 text-sm font-medium transition-colors',
                    isActive
                      ? 'text-primary bg-surface border-l-2 border-accent'
                      : 'text-muted hover:text-primary hover:bg-surface/50',
                    collapsed && 'justify-center px-0'
                  )
                }
              >
                <Icon className="w-5 h-5 shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            );
          })}
        </div>

        {/* Toggle button */}
        <div className="p-4 border-t border-border">
          <button
            onClick={onToggle}
            className={cn(
              'flex items-center gap-2 w-full px-3 py-2 text-sm font-medium text-muted hover:text-primary hover:bg-surface/50 rounded-md transition-colors',
              collapsed && 'justify-center'
            )}
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <>
                <ChevronLeft className="w-4 h-4" />
                <span>Collapse</span>
              </>
            )}
          </button>
        </div>
      </nav>
    </aside>
  );
}
