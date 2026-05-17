import { format } from 'date-fns';
import type { CrewAvailabilitySummary } from '@/types/api';

interface CrewAvailabilityCardProps {
  availability: CrewAvailabilitySummary[];
  loading: boolean;
}

export function CrewAvailabilityCard({ availability, loading }: CrewAvailabilityCardProps) {
  if (loading) {
    return (
      <div className="animate-pulse space-y-3">
        <div className="h-6 bg-surface-hover rounded w-full"></div>
        <div className="h-2 bg-surface-hover rounded w-full"></div>
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="h-4 bg-surface-hover rounded w-2/3"></div>
          ))}
        </div>
      </div>
    );
  }

  // Get today's date string
  const today = format(new Date(), 'yyyy-MM-dd');

  // Calculate counts from today's data
  let free = 0;
  let booked = 0;
  let unavailable = 0;

  availability.forEach(crew => {
    const todayData = crew.days.find(d => d.date === today);
    if (todayData) {
      if (todayData.status === 'free') free++;
      else if (todayData.status === 'booked') booked++;
      else if (todayData.status === 'unavailable') unavailable++;
    }
  });

  const total = free + booked + unavailable;
  const freePercent = total > 0 ? (free / total) * 100 : 0;
  const bookedPercent = total > 0 ? (booked / total) * 100 : 0;
  const unavailablePercent = total > 0 ? (unavailable / total) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Counts */}
      <div className="flex items-center gap-6 text-sm">
        <div>
          <span className="text-muted">Free: </span>
          <span className="font-mono text-job-active">{free}</span>
        </div>
        <div>
          <span className="text-muted">Booked: </span>
          <span className="font-mono text-job-intake">{booked}</span>
        </div>
        <div>
          <span className="text-muted">Unavailable: </span>
          <span className="font-mono text-muted-foreground">{unavailable}</span>
        </div>
      </div>

      {/* Visual bar */}
      <div className="h-2 rounded-full overflow-hidden flex bg-surface-hover">
        {freePercent > 0 && (
          <div
            className="bg-job-active h-full"
            style={{ width: `${freePercent}%` }}
          />
        )}
        {bookedPercent > 0 && (
          <div
            className="bg-job-intake h-full"
            style={{ width: `${bookedPercent}%` }}
          />
        )}
        {unavailablePercent > 0 && (
          <div
            className="bg-muted-foreground h-full"
            style={{ width: `${unavailablePercent}%` }}
          />
        )}
      </div>

      {/* First 5 crew with status dots */}
      <div className="space-y-2">
        {availability.slice(0, 5).map(crew => {
          const todayData = crew.days.find(d => d.date === today);
          const status = todayData?.status || 'free';

          const dotColor = status === 'free'
            ? 'bg-job-active'
            : status === 'booked'
              ? 'bg-job-intake'
              : 'bg-muted-foreground';

          return (
            <div key={crew.crew_id} className="flex items-center gap-2 text-sm">
              <span className={`h-2 w-2 rounded-full ${dotColor} inline-block`} />
              <span className="text-muted">{crew.crew_name}</span>
            </div>
          );
        })}
        {availability.length > 5 && (
          <p className="text-xs text-muted-foreground font-mono">
            +{availability.length - 5} more
          </p>
        )}
      </div>
    </div>
  );
}
