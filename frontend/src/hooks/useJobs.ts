import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { JobCreate, JobUpdate, JobTransitionRequest } from '@/types/api';

export function useJobs(params?: { search?: string; state?: string }) {
  return useQuery({
    queryKey: ['jobs', params],
    queryFn: () => api.jobs.list(params),
  });
}

export function useJob(id: string) {
  return useQuery({
    queryKey: ['jobs', id],
    queryFn: () => api.jobs.get(id),
    enabled: !!id,
  });
}

export function useCreateJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: JobCreate) => api.jobs.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  });
}

export function useUpdateJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: JobUpdate }) => api.jobs.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  });
}

export function useDeleteJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.jobs.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  });
}

export function useTransitionJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: JobTransitionRequest }) => api.jobs.transition(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  });
}
