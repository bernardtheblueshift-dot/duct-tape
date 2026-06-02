import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { JobResponse } from '@/types/api';

const JOB_SOURCES = ['direct', 'email', 'phone', 'referral', 'website', 'other'] as const;

const jobSchema = z.object({
  title: z.string().min(1, 'Title required').max(200),
  description: z.string().optional().nullable(),
  venue: z.string().optional().nullable(),
  scheduled_start: z.string().optional().nullable(),
  scheduled_end: z.string().optional().nullable(),
  source: z.enum(JOB_SOURCES).optional().nullable(),
  contact_name: z.string().optional().nullable(),
  contact_email: z.string().optional().nullable(),
  contact_phone: z.string().optional().nullable(),
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
      source: initialData.source || undefined,
      contact_name: initialData.contact_name || '',
      contact_email: initialData.contact_email || '',
      contact_phone: initialData.contact_phone || '',
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

      {/* Intake Source */}
      <div className="border-t border-dashed border-border pt-4 mt-4">
        <p className="text-xs text-muted font-mono mb-3">// intake info</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="source" className="block text-sm font-medium mb-1.5">Source</label>
            <select
              id="source"
              {...register('source')}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary focus:outline-none focus:ring-1 focus:ring-accent"
            >
              <option value="">No source</option>
              <option value="direct">Direct</option>
              <option value="email">Email</option>
              <option value="phone">Phone</option>
              <option value="referral">Referral</option>
              <option value="website">Website</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label htmlFor="contact_name" className="block text-sm font-medium mb-1.5">Contact Name</label>
            <input id="contact_name" type="text" {...register('contact_name')} placeholder="Client contact" className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent" />
          </div>
          <div>
            <label htmlFor="contact_email" className="block text-sm font-medium mb-1.5">Contact Email</label>
            <input id="contact_email" type="email" {...register('contact_email')} placeholder="contact@client.com" className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent" />
          </div>
          <div>
            <label htmlFor="contact_phone" className="block text-sm font-medium mb-1.5">Contact Phone</label>
            <input id="contact_phone" type="tel" {...register('contact_phone')} placeholder="+81-90-..." className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent" />
          </div>
        </div>
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
