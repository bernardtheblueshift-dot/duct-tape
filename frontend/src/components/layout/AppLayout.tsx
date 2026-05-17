import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { cn } from '@/lib/utils';

export function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="flex pt-14">
        <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
        <main
          className={cn(
            'flex-1 min-h-[calc(100vh-3.5rem)] p-6 transition-all duration-200',
            sidebarCollapsed ? 'ml-16' : 'ml-56',
            'max-md:ml-0'
          )}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
