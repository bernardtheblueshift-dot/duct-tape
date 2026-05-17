import { cn } from '@/lib/utils';
import type { JobState } from '@/types/api';

const stateConfig: Record<JobState, { bg: string; text: string; label: string }> = {
  intake: { bg: 'bg-job-intake/20', text: 'text-job-intake', label: 'Intake' },
  simmer: { bg: 'bg-job-simmer/20', text: 'text-job-simmer', label: 'Simmer' },
  active: { bg: 'bg-job-active/20', text: 'text-job-active', label: 'Active' },
  complete: { bg: 'bg-job-complete/20', text: 'text-job-complete', label: 'Complete' },
};

export function JobStateBadge({ state, className }: { state: JobState; className?: string }) {
  const config = stateConfig[state];
  return (
    <span className={cn(
      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium font-mono uppercase tracking-wider',
      config.bg, config.text,
      className
    )}>
      {config.label}
    </span>
  );
}
