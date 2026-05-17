import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { format, startOfMonth, endOfMonth } from 'date-fns';

export function useCalendarEvents(currentDate: Date) {
  const start = format(startOfMonth(currentDate), 'yyyy-MM-dd');
  const end = format(endOfMonth(currentDate), 'yyyy-MM-dd');

  return useQuery({
    queryKey: ['calendar-events', start, end],
    queryFn: () => api.calendar.events({ start_date: start, end_date: end }),
  });
}
