import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { EquipmentCreate, EquipmentUpdate, EquipmentCondition } from '@/types/api';

export function useEquipmentList(params?: { search?: string; category?: string; condition?: string }) {
  return useQuery({
    queryKey: ['equipment', params],
    queryFn: () => api.equipment.list(params),
  });
}

export function useEquipment(id: string) {
  return useQuery({
    queryKey: ['equipment', id],
    queryFn: () => api.equipment.get(id),
    enabled: !!id,
  });
}

export function useCreateEquipment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: EquipmentCreate) => api.equipment.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['equipment'] }),
  });
}

export function useUpdateEquipment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: EquipmentUpdate }) => api.equipment.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['equipment'] }),
  });
}

export function useDeleteEquipment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.equipment.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['equipment'] }),
  });
}

export function useUpdateCondition() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, condition }: { id: string; condition: EquipmentCondition }) =>
      api.equipment.updateCondition(id, condition),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['equipment'] }),
  });
}
