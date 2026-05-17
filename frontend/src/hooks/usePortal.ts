import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { AvailabilityPatternCreate } from '@/types/api';

export function usePortalDashboard() {
  return useQuery({
    queryKey: ['portal-dashboard'],
    queryFn: () => api.portal.dashboard(),
  });
}

export function usePortalJobDetail(jobId: string) {
  return useQuery({
    queryKey: ['portal-job', jobId],
    queryFn: () => api.portal.jobDetail(jobId),
    enabled: !!jobId,
  });
}

export function usePortalProfile() {
  return useQuery({
    queryKey: ['portal-profile'],
    queryFn: () => api.portal.getProfile(),
  });
}

export function usePortalAvailability() {
  return useQuery({
    queryKey: ['portal-availability'],
    queryFn: () => api.portal.getAvailability(),
  });
}

export function useConfirmAssignment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.portal.confirmAssignment(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portal-dashboard'] });
      qc.invalidateQueries({ queryKey: ['portal-job'] });
    },
  });
}

export function useDeclineAssignment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => api.portal.declineAssignment(id, reason),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['portal-dashboard'] });
      qc.invalidateQueries({ queryKey: ['portal-job'] });
    },
  });
}

export function useUpdatePortalProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { phone?: string | null; bio?: string | null }) => api.portal.updateProfile(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['portal-profile'] }),
  });
}

export function useUpdatePortalAvailability() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patterns: AvailabilityPatternCreate[]) => api.portal.setAvailability(patterns),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['portal-availability'] }),
  });
}
