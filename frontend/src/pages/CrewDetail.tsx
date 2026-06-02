import { useParams, useNavigate } from 'react-router-dom';
import { useCrew, useCrewRatings, useCrewAvailability, useArchiveCrew, useUnarchiveCrew } from '@/hooks/useCrew';
import { ArrowLeft } from 'lucide-react';

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export function CrewDetailPage() {
  const { crewId } = useParams<{ crewId: string }>();
  const navigate = useNavigate();
  const { data: crew, isLoading } = useCrew(crewId!);
  const { data: ratings } = useCrewRatings(crewId!);
  const { data: availability } = useCrewAvailability(crewId!);
  const archiveMutation = useArchiveCrew();
  const unarchiveMutation = useUnarchiveCrew();

  if (isLoading) {
    return (
      <div className="space-y-3">
        <div className="h-8 rounded-lg bg-surface animate-pulse" />
        <div className="h-64 rounded-lg bg-surface animate-pulse" />
      </div>
    );
  }

  if (!crew) {
    return <div className="text-center py-12 text-muted font-mono text-sm">Crew not found</div>;
  }

  const handleArchive = () => {
    if (confirm(crew.archived_at ? 'Unarchive this crew member?' : 'Archive this crew member?')) {
      if (crew.archived_at) {
        unarchiveMutation.mutate(crew.id);
      } else {
        archiveMutation.mutate(crew.id);
      }
    }
  };

  // Build availability map
  const availabilityMap = new Map<number, boolean>();
  availability?.forEach(pattern => {
    availabilityMap.set(pattern.day_of_week, pattern.is_available);
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/crew')}
            className="p-2 rounded-lg hover:bg-surface transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-2xl font-semibold">{crew.name || crew.email}</h1>
            <p className="text-muted font-mono text-xs mt-1">{crew.email}</p>
          </div>
        </div>
        <button
          onClick={handleArchive}
          className="px-4 py-2 rounded-lg border border-border hover:bg-surface transition-colors"
        >
          {crew.archived_at ? 'Unarchive' : 'Archive'}
        </button>
      </div>

      {/* Profile Card */}
      <div className="rounded-lg border border-border bg-surface p-6 space-y-4">
        <h2 className="text-lg font-semibold">Profile</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-muted mb-1">Email</div>
            <div className="font-mono text-sm">{crew.email}</div>
          </div>
          <div>
            <div className="text-sm text-muted mb-1">Phone</div>
            <div className="font-mono text-sm">{crew.phone || 'Not set'}</div>
          </div>
          <div className="md:col-span-2">
            <div className="text-sm text-muted mb-1">Bio</div>
            <div className="text-sm">{crew.bio || 'No bio'}</div>
          </div>
          <div>
            <div className="text-sm text-muted mb-1">Hourly Rate</div>
            <div className="font-mono text-sm">
              {crew.hourly_rate !== null ? `$${crew.hourly_rate.toFixed(0)}/hr` : 'Not set'}
            </div>
          </div>
          <div>
            <div className="text-sm text-muted mb-1">Skills</div>
            <div className="flex flex-wrap gap-1">
              {crew.skills.length === 0 ? (
                <span className="text-sm text-muted">No skills</span>
              ) : (
                crew.skills.map(skill => (
                  <span key={skill} className="rounded-full bg-secondary px-2 py-0.5 text-xs font-mono">
                    {skill}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Ratings Section */}
      <div className="rounded-lg border border-border bg-surface p-6 space-y-4">
        <h2 className="text-lg font-semibold">Ratings</h2>
        <div className="flex items-baseline gap-4">
          <div className="text-3xl font-mono">
            {crew.rating_average !== null ? crew.rating_average.toFixed(1) : '—'}
          </div>
          <div className="text-sm text-muted">
            {crew.rating_count} {crew.rating_count === 1 ? 'rating' : 'ratings'}
          </div>
        </div>

        {ratings && ratings.length > 0 && (
          <div className="space-y-3 mt-4">
            {ratings.map(rating => (
              <div key={rating.id} className="border-t border-border pt-3">
                <div className="flex items-center justify-between mb-1">
                  <div className="font-mono text-sm">{'★'.repeat(rating.stars)}</div>
                  <div className="text-xs text-muted font-mono">
                    {new Date(rating.created_at).toLocaleDateString()}
                  </div>
                </div>
                {rating.notes && <div className="text-sm text-muted">{rating.notes}</div>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Availability Section */}
      <div className="rounded-lg border border-border bg-surface p-6 space-y-4">
        <h2 className="text-lg font-semibold">Availability</h2>
        <div className="grid grid-cols-7 gap-2">
          {DAY_LABELS.map((day, index) => {
            const isAvailable = availabilityMap.get(index) ?? true;
            return (
              <div key={day} className="text-center">
                <div className="text-xs text-muted mb-2">{day}</div>
                <div
                  className={`h-3 w-3 rounded-full mx-auto ${
                    isAvailable ? 'bg-job-active' : 'bg-muted'
                  }`}
                  title={isAvailable ? 'Available' : 'Unavailable'}
                />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
