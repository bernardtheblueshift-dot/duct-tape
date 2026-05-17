import { useDashboard } from '@/hooks/useDashboard';
import { StatCard } from '@/components/features/StatCard';
import { UpcomingJobsList } from '@/components/features/UpcomingJobsList';
import { CrewAvailabilityCard } from '@/components/features/CrewAvailabilityCard';
import { Briefcase, UserCheck, Mail, Wrench } from 'lucide-react';

export function DashboardPage() {
  const { jobs, availability, notifications, activeJobCount, equipmentUtilization, loading } = useDashboard();

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted font-mono mt-1">// overview</p>
      </div>

      {/* Bento grid - 4 columns on lg, 2 on md, 1 on mobile */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Large card: Upcoming Jobs (spans 2 cols, 2 rows on lg) */}
        <div className="lg:col-span-2 lg:row-span-2 rounded-lg border border-border bg-surface p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Upcoming Jobs</h2>
            <span className="text-xs text-muted font-mono">next 7 days</span>
          </div>
          <UpcomingJobsList jobs={jobs} />
        </div>

        {/* Stat cards */}
        <StatCard label="Active Jobs" value={activeJobCount} icon={Briefcase} />
        <StatCard
          label="Pending Assignments"
          value={notifications.pending_assignments}
          icon={UserCheck}
        />

        {/* Medium card: Crew Availability (spans 2 cols on lg) */}
        <div className="lg:col-span-2 rounded-lg border border-border bg-surface p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Crew Availability</h2>
            <span className="text-xs text-muted font-mono">today</span>
          </div>
          <CrewAvailabilityCard availability={availability} loading={loading} />
        </div>

        {/* More stat cards */}
        <StatCard label="Unread Messages" value={notifications.unread_messages} icon={Mail} />
        <StatCard
          label="Equipment In Use"
          value={`${equipmentUtilization}%`}
          icon={Wrench}
        />
      </div>
    </div>
  );
}
