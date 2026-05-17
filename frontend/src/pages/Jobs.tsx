import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { Search } from 'lucide-react';
import { useJobs } from '@/hooks/useJobs';
import { DataTable } from '@/components/features/DataTable';
import { JobStateBadge } from '@/components/features/JobStateBadge';
import type { JobResponse } from '@/types/api';

export function JobsPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [stateFilter, setStateFilter] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data: jobs, isLoading } = useJobs({
    search: search || undefined,
    state: stateFilter || undefined
  });

  const columns = [
    {
      key: 'title',
      header: 'Title',
      render: (job: JobResponse) => (
        <div className="font-medium truncate max-w-md">{job.title}</div>
      ),
    },
    {
      key: 'venue',
      header: 'Venue',
      render: (job: JobResponse) => (
        <div className="text-muted">{job.venue || '—'}</div>
      ),
      hideOnMobile: true,
    },
    {
      key: 'state',
      header: 'State',
      render: (job: JobResponse) => <JobStateBadge state={job.state} />,
    },
    {
      key: 'date',
      header: 'Date',
      render: (job: JobResponse) => (
        <div className="font-mono text-sm">
          {job.scheduled_start ? format(new Date(job.scheduled_start), 'dd MMM yyyy') : 'TBD'}
        </div>
      ),
      hideOnMobile: true,
    },
    {
      key: 'crew',
      header: 'Crew',
      render: (job: JobResponse) => (
        <div className="font-mono text-sm">{job.assigned_crew.length}</div>
      ),
    },
  ];

  const renderMobileCard = (job: JobResponse) => (
    <div className="space-y-2">
      <div className="flex items-start justify-between gap-2">
        <div className="font-semibold text-base">{job.title}</div>
        <JobStateBadge state={job.state} />
      </div>
      <div className="text-sm text-muted space-y-1">
        <div>{job.venue || '—'}</div>
        <div className="font-mono">
          {job.scheduled_start ? format(new Date(job.scheduled_start), 'dd MMM yyyy') : 'TBD'}
        </div>
        <div className="font-mono">{job.assigned_crew.length} crew</div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Jobs</h1>
          <p className="text-muted font-mono text-sm mt-1">// job management</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-accent text-primary rounded-md hover:bg-accent/90 transition-colors font-medium"
        >
          New Job
        </button>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
          <input
            type="text"
            placeholder="Search jobs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-md border border-border bg-surface px-3 py-2 pl-9 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>
        <select
          value={stateFilter}
          onChange={(e) => setStateFilter(e.target.value)}
          className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary"
        >
          <option value="">All States</option>
          <option value="intake">Intake</option>
          <option value="simmer">Simmer</option>
          <option value="active">Active</option>
          <option value="complete">Complete</option>
        </select>
      </div>

      {/* Jobs Table */}
      <DataTable
        data={jobs || []}
        columns={columns}
        onRowClick={(job) => navigate(`/jobs/${job.id}`)}
        renderMobileCard={renderMobileCard}
        loading={isLoading}
        emptyMessage={search || stateFilter ? 'No jobs found' : 'No jobs yet. Create your first job to get started.'}
      />

      {/* TODO: Create Job Modal - will be implemented in Task 2 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-background rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-semibold mb-4">Create Job</h2>
            <p className="text-muted text-sm mb-4">Job form will be implemented in Task 2</p>
            <button
              onClick={() => setShowCreateModal(false)}
              className="px-4 py-2 bg-surface border border-border rounded-md hover:bg-surface-hover transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
