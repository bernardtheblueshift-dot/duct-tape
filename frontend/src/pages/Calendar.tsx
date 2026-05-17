import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  isSameMonth,
  isToday,
  format,
  addMonths,
  subMonths,
  parseISO,
  startOfDay,
} from 'date-fns';
import { useCalendarEvents } from '@/hooks/useCalendar';
import { type CalendarEvent } from '@/types/api';
import { cn } from '@/lib/utils';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export function CalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState<'month' | 'week'>('month');
  const navigate = useNavigate();

  const { data, isLoading } = useCalendarEvents(currentDate);
  const events = data?.events || [];

  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  const calStart = startOfWeek(monthStart);
  const calEnd = endOfWeek(monthEnd);
  const days = eachDayOfInterval({ start: calStart, end: calEnd });

  const getEventsForDay = (day: Date): CalendarEvent[] => {
    const dayStart = startOfDay(day);
    return events.filter((event) => {
      const eventStart = startOfDay(parseISO(event.start));
      const eventEnd = startOfDay(parseISO(event.end));
      return dayStart >= eventStart && dayStart <= eventEnd;
    });
  };

  const handlePrevMonth = () => setCurrentDate(subMonths(currentDate, 1));
  const handleNextMonth = () => setCurrentDate(addMonths(currentDate, 1));

  const handleEventClick = (event: CalendarEvent) => {
    if (event.job_id) {
      navigate(`/jobs/${event.job_id}`);
    }
  };

  if (view === 'week') {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Calendar</h1>
            <p className="text-muted font-mono text-sm">// schedule overview</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setView('month')}
              className="px-3 py-1 rounded border border-border bg-background hover:bg-accent"
            >
              Month
            </button>
            <button className="px-3 py-1 rounded border border-accent bg-accent">
              Week
            </button>
          </div>
        </div>
        <div className="text-muted font-mono text-sm">Week view coming soon</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Calendar</h1>
          <p className="text-muted font-mono text-sm">// schedule overview</p>
        </div>
        <div className="flex gap-2">
          <button
            className="px-3 py-1 rounded border border-accent bg-accent"
            onClick={() => setView('month')}
          >
            Month
          </button>
          <button
            onClick={() => setView('week')}
            className="px-3 py-1 rounded border border-border bg-background hover:bg-accent"
          >
            Week
          </button>
        </div>
      </div>

      {/* Month navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={handlePrevMonth}
          className="flex items-center gap-1 px-3 py-2 rounded border border-border hover:bg-accent"
        >
          <ChevronLeft className="h-4 w-4" />
          Previous
        </button>
        <div className="text-lg font-semibold">
          {format(currentDate, 'MMMM yyyy')}
        </div>
        <button
          onClick={handleNextMonth}
          className="flex items-center gap-1 px-3 py-2 rounded border border-border hover:bg-accent"
        >
          Next
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

      {/* Day headers */}
      <div className="grid grid-cols-7 gap-px bg-border">
        {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, i) => (
          <div
            key={i}
            className="bg-background p-2 text-center text-xs font-mono uppercase text-muted"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      {isLoading ? (
        <div className="text-center text-muted font-mono text-sm py-8">Loading calendar...</div>
      ) : (
        <div className="grid grid-cols-7 gap-px bg-border">
          {days.map((day, i) => {
            const eventsForDay = getEventsForDay(day);
            const visibleEvents = eventsForDay.slice(0, 3);
            const remainingCount = eventsForDay.length - 3;

            return (
              <div
                key={i}
                className={cn(
                  'min-h-16 md:min-h-24 lg:min-h-32 border border-border p-1 text-xs bg-background',
                  !isSameMonth(day, currentDate) && 'bg-background/50 text-muted-foreground',
                  isToday(day) && 'border-accent border-2'
                )}
              >
                <div className="font-mono text-xs mb-1">{format(day, 'd')}</div>

                {/* Mobile: colored dots */}
                <div className="md:hidden flex gap-0.5 flex-wrap">
                  {visibleEvents.map((e) => (
                    <div
                      key={e.id}
                      className="h-1.5 w-1.5 rounded-full cursor-pointer"
                      style={{ backgroundColor: e.color }}
                      onClick={() => handleEventClick(e)}
                      title={e.title}
                    />
                  ))}
                </div>

                {/* Desktop: event blocks */}
                <div className="hidden md:block space-y-0.5">
                  {visibleEvents.map((event) => (
                    <div
                      key={event.id}
                      className="rounded px-1 py-0.5 text-xs truncate cursor-pointer hover:opacity-80"
                      style={{
                        backgroundColor: event.color + '33',
                        color: event.color,
                      }}
                      title={event.title}
                      onClick={() => handleEventClick(event)}
                    >
                      {event.title}
                    </div>
                  ))}
                  {remainingCount > 0 && (
                    <div className="text-xs text-muted font-mono">+{remainingCount} more</div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
