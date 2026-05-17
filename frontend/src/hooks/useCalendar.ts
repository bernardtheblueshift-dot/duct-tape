import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek } from 'date-fns';

export function useCalendarEvents(currentDate: Date) {
  const start = format(startOfMonth(currentDate), 'yyyy-MM-dd');
  const end = format(endOfMonth(currentDate), 'yyyy-MM-dd');

  return useQuery({
    queryKey: ['calendar-events', start, end],
    queryFn: () => api.calendar.events({ start, end }),
  });
}

export function useWeekCalendarEvents(currentDate: Date) {
  const start = format(startOfWeek(currentDate), 'yyyy-MM-dd');
  const end = format(endOfWeek(currentDate), 'yyyy-MM-dd');

  return useQuery({
    queryKey: ['calendar-events-week', start, end],
    queryFn: () => api.calendar.events({ start, end }),
  });
}
