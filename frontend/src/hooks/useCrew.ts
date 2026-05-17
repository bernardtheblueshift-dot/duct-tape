import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { CrewProfileCreate, CrewProfileUpdate } from '@/types/api';

export function useCrewList(params?: { search?: string; skill?: string }) {
  return useQuery({
    queryKey: ['crew', params],
    queryFn: () => api.crew.list(params),
  });
}

export function useCrew(id: string) {
  return useQuery({
    queryKey: ['crew', id],
    queryFn: () => api.crew.get(id),
    enabled: !!id,
  });
}

export function useCrewRatings(id: string) {
  return useQuery({
    queryKey: ['crew', id, 'ratings'],
    queryFn: () => api.crew.ratings(id),
    enabled: !!id,
  });
}

export function useCrewAvailability(id: string) {
  return useQuery({
    queryKey: ['crew', id, 'availability'],
    queryFn: () => api.crew.getAvailability(id),
    enabled: !!id,
  });
}

export function useCreateCrew() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CrewProfileCreate) => api.crew.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['crew'] }),
  });
}

export function useUpdateCrew() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CrewProfileUpdate }) => api.crew.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['crew'] }),
  });
}

export function useArchiveCrew() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.crew.archive(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['crew'] }),
  });
}

export function useUnarchiveCrew() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.crew.unarchive(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['crew'] }),
  });
}
