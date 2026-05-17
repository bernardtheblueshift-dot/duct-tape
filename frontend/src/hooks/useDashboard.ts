import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { format, addDays } from 'date-fns';

export function useDashboard() {
  const today = format(new Date(), 'yyyy-MM-dd');
  const nextWeek = format(addDays(new Date(), 7), 'yyyy-MM-dd');

  const jobsQuery = useQuery({
    queryKey: ['jobs'],
    queryFn: () => api.jobs.list(),
  });

  const availabilityQuery = useQuery({
    queryKey: ['crew-availability', today, nextWeek],
    queryFn: () => api.calendar.bulkAvailability({ start_date: today, end_date: nextWeek }),
  });

  const notificationsQuery = useQuery({
    queryKey: ['notification-counts'],
    queryFn: () => api.notifications.counts(),
    refetchInterval: 30_000,
  });

  const equipmentQuery = useQuery({
    queryKey: ['equipment'],
    queryFn: () => api.equipment.list(),
  });

  // Derived stats
  const jobs = jobsQuery.data ?? [];
  const activeJobCount = jobs.filter(j => j.state === 'active').length;
  const equipment = equipmentQuery.data ?? [];
  const totalEquipmentQty = equipment.reduce((sum, e) => sum + e.quantity, 0);
  const assignedEquipmentQty = jobs.reduce((sum, j) => sum + j.assigned_gear.reduce((s, g) => s + g.quantity_assigned, 0), 0);
  const equipmentUtilization = totalEquipmentQty > 0 ? Math.round((assignedEquipmentQty / totalEquipmentQty) * 100) : 0;

  return {
    jobs,
    availability: availabilityQuery.data ?? [],
    notifications: notificationsQuery.data ?? { unread_messages: 0, pending_assignments: 0 },
    activeJobCount,
    equipmentUtilization,
    loading: jobsQuery.isLoading || availabilityQuery.isLoading,
  };
}
