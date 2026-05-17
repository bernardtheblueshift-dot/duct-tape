import { Link } from 'react-router-dom';
import { format, isAfter, isBefore, addDays } from 'date-fns';
import { JobStateBadge } from './JobStateBadge';
import type { JobResponse } from '@/types/api';

interface UpcomingJobsListProps {
  jobs: JobResponse[];
}

export function UpcomingJobsList({ jobs }: UpcomingJobsListProps) {
  const now = new Date();
  const nextWeek = addDays(now, 7);

  // Filter to jobs with scheduled_start in next 7 days that are not complete
  const upcomingJobs = jobs
    .filter(job => {
      if (!job.scheduled_start || job.state === 'complete') return false;
      const start = new Date(job.scheduled_start);
      return isAfter(start, now) && isBefore(start, nextWeek);
    })
    .sort((a, b) => {
      if (!a.scheduled_start || !b.scheduled_start) return 0;
      return new Date(a.scheduled_start).getTime() - new Date(b.scheduled_start).getTime();
    })
    .slice(0, 10);

  if (upcomingJobs.length === 0) {
    return <p className="text-muted text-sm">No upcoming jobs</p>;
  }

  return (
    <div className="space-y-0">
      {upcomingJobs.map((job) => (
        <Link
          key={job.id}
          to={`/jobs/${job.id}`}
          className="block py-3 hover:bg-surface-hover transition-colors -mx-6 px-6 border-b border-dashed border-border last:border-0"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <JobStateBadge state={job.state} />
                <h3 className="font-medium truncate">
                  {job.title}
                </h3>
              </div>
              {job.venue && (
                <p className="text-sm text-muted truncate">{job.venue}</p>
              )}
            </div>
            <div className="flex flex-col items-end gap-1 shrink-0">
              {job.scheduled_start && (
                <p className="text-sm font-mono">
                  {format(new Date(job.scheduled_start), 'EEE dd MMM, HH:mm')}
                </p>
              )}
              <p className="text-xs text-muted font-mono">
                {job.assigned_crew.length} crew
              </p>
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
