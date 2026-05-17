import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCrewList } from '@/hooks/useCrew';
import { DataTable } from '@/components/features/DataTable';

export function CrewPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [skill, setSkill] = useState<string | undefined>(undefined);
  const [showArchived, setShowArchived] = useState(false);

  const { data: crew, isLoading } = useCrewList({ search: search || undefined, skill });

  // Filter out archived unless toggle is on
  const filteredCrew = crew?.filter(c => showArchived || !c.archived_at) || [];

  // Collect unique skills for filter dropdown
  const allSkills = Array.from(
    new Set(crew?.flatMap(c => c.skills) || [])
  ).sort();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Crew</h1>
          <p className="text-muted font-mono text-sm">// crew directory</p>
        </div>
        <button className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors">
          Add Crew
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <input
          type="text"
          placeholder="Search crew..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 px-3 py-2 rounded-lg border border-border bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
        <select
          value={skill || ''}
          onChange={(e) => setSkill(e.target.value || undefined)}
          className="px-3 py-2 rounded-lg border border-border bg-surface text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          <option value="">All Skills</option>
          {allSkills.map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <label className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-surface text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
            className="rounded"
          />
          Show Archived
        </label>
      </div>

      {/* Data table */}
      <DataTable
        data={filteredCrew}
        columns={[
          {
            key: 'name',
            header: 'Name',
            render: (crew) => {
              // For v1, we don't have User name lookup, so show truncated user_id
              const shortId = crew.user_id.substring(0, 8);
              return <span className="font-medium">Crew {shortId}</span>;
            },
          },
          {
            key: 'skills',
            header: 'Skills',
            render: (crew) => {
              if (crew.skills.length === 0) return <span className="text-muted">—</span>;
              const visible = crew.skills.slice(0, 3);
              const remaining = crew.skills.length - 3;
              return (
                <div className="flex flex-wrap gap-1">
                  {visible.map(skill => (
                    <span key={skill} className="rounded-full bg-secondary px-2 py-0.5 text-xs font-mono">
                      {skill}
                    </span>
                  ))}
                  {remaining > 0 && (
                    <span className="text-xs text-muted font-mono">+{remaining} more</span>
                  )}
                </div>
              );
            },
          },
          {
            key: 'rating',
            header: 'Rating',
            render: (crew) => {
              if (crew.rating_average === null) return <span className="text-muted font-mono">—</span>;
              return (
                <span className="font-mono text-sm">
                  {crew.rating_average.toFixed(1)} ({crew.rating_count})
                </span>
              );
            },
            className: 'hidden sm:table-cell',
            hideOnMobile: true,
          },
          {
            key: 'rate',
            header: 'Rate',
            render: (crew) => {
              if (crew.hourly_rate === null) return <span className="text-muted font-mono">—</span>;
              return <span className="font-mono text-sm">${crew.hourly_rate.toFixed(0)}</span>;
            },
            className: 'hidden sm:table-cell',
            hideOnMobile: true,
          },
          {
            key: 'status',
            header: 'Status',
            render: (crew) => (
              <span className={crew.archived_at ? "text-muted" : "text-green-500"}>
                {crew.archived_at ? 'Archived' : 'Active'}
              </span>
            ),
            className: 'hidden sm:table-cell',
            hideOnMobile: true,
          },
        ]}
        onRowClick={(crew) => navigate(`/crew/${crew.id}`)}
        renderMobileCard={(crew) => {
          const shortId = crew.user_id.substring(0, 8);
          return (
            <div className="space-y-2">
              <div className="font-medium">Crew {shortId}</div>
              <div className="flex flex-wrap gap-1">
                {crew.skills.slice(0, 3).map(skill => (
                  <span key={skill} className="rounded-full bg-secondary px-2 py-0.5 text-xs font-mono">
                    {skill}
                  </span>
                ))}
                {crew.skills.length > 3 && (
                  <span className="text-xs text-muted font-mono">+{crew.skills.length - 3} more</span>
                )}
              </div>
              <div className="flex justify-between text-sm">
                <span className="font-mono">
                  {crew.rating_average !== null ? `${crew.rating_average.toFixed(1)} (${crew.rating_count})` : '—'}
                </span>
                <span className="font-mono">
                  {crew.hourly_rate !== null ? `$${crew.hourly_rate.toFixed(0)}` : '—'}
                </span>
              </div>
            </div>
          );
        }}
        emptyMessage="No crew found"
        loading={isLoading}
      />
    </div>
  );
}
