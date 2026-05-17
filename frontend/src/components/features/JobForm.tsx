import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { JobResponse } from '@/types/api';

const jobSchema = z.object({
  title: z.string().min(1, 'Title required').max(200),
  description: z.string().optional().nullable(),
  venue: z.string().optional().nullable(),
  scheduled_start: z.string().optional().nullable(),
  scheduled_end: z.string().optional().nullable(),
});

type JobFormData = z.infer<typeof jobSchema>;

interface JobFormProps {
  initialData?: JobResponse;
  onSubmit: (data: JobFormData) => void;
  onCancel: () => void;
  loading?: boolean;
}

export function JobForm({ initialData, onSubmit, onCancel, loading }: JobFormProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<JobFormData>({
    resolver: zodResolver(jobSchema),
    defaultValues: initialData ? {
      title: initialData.title,
      description: initialData.description || '',
      venue: initialData.venue || '',
      scheduled_start: initialData.scheduled_start || '',
      scheduled_end: initialData.scheduled_end || '',
    } : undefined,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Title */}
      <div>
        <label htmlFor="title" className="block text-sm font-medium mb-1.5">
          Title <span className="text-red-500">*</span>
        </label>
        <input
          id="title"
          type="text"
          {...register('title')}
          className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
          placeholder="Enter job title"
        />
        {errors.title && (
          <p className="text-red-500 text-xs mt-1">{errors.title.message}</p>
        )}
      </div>

      {/* Description */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium mb-1.5">
          Description
        </label>
        <textarea
          id="description"
          {...register('description')}
          rows={4}
          className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent resize-none"
          placeholder="Job description"
        />
      </div>

      {/* Venue */}
      <div>
        <label htmlFor="venue" className="block text-sm font-medium mb-1.5">
          Venue
        </label>
        <input
          id="venue"
          type="text"
          {...register('venue')}
          className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
          placeholder="Event venue"
        />
      </div>

      {/* Scheduled Start */}
      <div>
        <label htmlFor="scheduled_start" className="block text-sm font-medium mb-1.5">
          Scheduled Start
        </label>
        <input
          id="scheduled_start"
          type="datetime-local"
          {...register('scheduled_start')}
          className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary focus:outline-none focus:ring-1 focus:ring-accent"
        />
      </div>

      {/* Scheduled End */}
      <div>
        <label htmlFor="scheduled_end" className="block text-sm font-medium mb-1.5">
          Scheduled End
        </label>
        <input
          id="scheduled_end"
          type="datetime-local"
          {...register('scheduled_end')}
          className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary focus:outline-none focus:ring-1 focus:ring-accent"
        />
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-accent text-primary rounded-md hover:bg-accent/90 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Saving...' : (initialData ? 'Save Changes' : 'Create Job')}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={loading}
          className="px-4 py-2 bg-surface border border-border rounded-md hover:bg-surface-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
