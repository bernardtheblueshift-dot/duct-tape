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
  addWeeks,
  subWeeks,
  parseISO,
  startOfDay,
  getHours,
  getMinutes,
  differenceInMinutes,
  min,
  max,
} from 'date-fns';
import { useCalendarEvents, useWeekCalendarEvents } from '@/hooks/useCalendar';
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
    const { data: weekData, isLoading: weekLoading } = useWeekCalendarEvents(currentDate);
    const weekEvents = weekData?.events || [];

    const weekStart = startOfWeek(currentDate);
    const weekEnd = endOfWeek(currentDate);
    const weekDays = eachDayOfInterval({ start: weekStart, end: weekEnd });

    const handlePrevWeek = () => setCurrentDate(subWeeks(currentDate, 1));
    const handleNextWeek = () => setCurrentDate(addWeeks(currentDate, 1));

    const getEventsForDay = (day: Date): CalendarEvent[] => {
      const dayStart = startOfDay(day);
      const dayEnd = new Date(day);
      dayEnd.setHours(23, 59, 59, 999);

      return weekEvents.filter((event) => {
        const eventStart = parseISO(event.start);
        const eventEnd = parseISO(event.end);
        return eventStart <= dayEnd && eventEnd >= dayStart;
      });
    };

    const calculateEventPosition = (event: CalendarEvent, day: Date) => {
      const eventStart = parseISO(event.start);
      const eventEnd = parseISO(event.end);

      const dayStart = startOfDay(day);
      const dayEnd = new Date(day);
      dayEnd.setHours(23, 59, 59, 999);

      const clampedStart = max([eventStart, dayStart]);
      const clampedEnd = min([eventEnd, dayEnd]);

      const startHour = getHours(clampedStart);
      const startMinute = getMinutes(clampedStart);
      const top = startHour * 3 + (startMinute / 60) * 3;

      const durationMinutes = differenceInMinutes(clampedEnd, clampedStart);
      const height = Math.max(1.5, (durationMinutes / 60) * 3);

      return { top, height };
    };

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

        {/* Week navigation */}
        <div className="flex items-center justify-between">
          <button
            onClick={handlePrevWeek}
            className="flex items-center gap-1 px-3 py-2 rounded border border-border hover:bg-accent"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </button>
          <div className="text-lg font-semibold">
            {format(weekStart, 'MMM d')} - {format(weekEnd, 'MMM d, yyyy')}
          </div>
          <button
            onClick={handleNextWeek}
            className="flex items-center gap-1 px-3 py-2 rounded border border-border hover:bg-accent"
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>

        {weekLoading ? (
          <div className="text-center text-muted font-mono text-sm py-8">
            Loading calendar...
          </div>
        ) : (
          <>
            {/* Desktop week grid */}
            <div className="hidden md:block bg-surface rounded-lg overflow-hidden">
              <div className="overflow-y-auto" style={{ maxHeight: '70vh' }}>
                <div className="grid grid-cols-8 gap-0">
                  {/* Header row */}
                  <div className="sticky top-0 bg-background border-b border-border p-2 text-xs font-mono text-muted">
                    Time
                  </div>
                  {weekDays.map((day, i) => (
                    <div
                      key={i}
                      className={cn(
                        'sticky top-0 bg-background border-b border-border p-2 text-center text-sm font-semibold',
                        isToday(day) && 'bg-accent/5 border-t-2 border-accent'
                      )}
                    >
                      {format(day, 'EEE d')}
                    </div>
                  ))}

                  {/* Time grid */}
                  {Array.from({ length: 24 }, (_, hour) => (
                    <div key={hour} className="contents">
                      {/* Time gutter */}
                      <div className="border-b border-border p-2 text-xs font-mono text-muted">
                        {String(hour).padStart(2, '0')}:00
                      </div>

                      {/* Day columns */}
                      {weekDays.map((day, dayIndex) => (
                        <div
                          key={dayIndex}
                          className={cn(
                            'relative border-b border-r border-border bg-background',
                            isToday(day) && 'bg-accent/5'
                          )}
                          style={{ height: '3rem' }}
                        >
                          {/* Events for this hour slot - only render on first hour to avoid duplication */}
                          {hour === 0 &&
                            getEventsForDay(day).map((event) => {
                              const { top, height } = calculateEventPosition(event, day);
                              return (
                                <div
                                  key={event.id}
                                  className="absolute left-0 right-0 mx-0.5 rounded px-1 py-0.5 text-xs truncate cursor-pointer overflow-hidden z-10"
                                  style={{
                                    top: `${top}rem`,
                                    height: `${height}rem`,
                                    backgroundColor: event.color + '33',
                                    color: event.color,
                                  }}
                                  title={event.title}
                                  onClick={() => handleEventClick(event)}
                                >
                                  {event.title}
                                </div>
                              );
                            })}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Mobile: day list */}
            <div className="md:hidden space-y-4">
              {weekDays.map((day) => {
                const dayEvents = getEventsForDay(day);
                return (
                  <div key={day.toISOString()} className="bg-surface rounded-lg border border-border overflow-hidden">
                    <div
                      className={cn(
                        'p-3 border-b border-border font-semibold',
                        isToday(day) && 'bg-accent/10 border-accent'
                      )}
                    >
                      {format(day, 'EEEE, MMM d')}
                    </div>
                    <div className="p-3 space-y-2">
                      {dayEvents.length === 0 ? (
                        <div className="text-muted text-sm font-mono">No events</div>
                      ) : (
                        dayEvents.map((event) => (
                          <div
                            key={event.id}
                            className="rounded px-2 py-1.5 cursor-pointer"
                            style={{
                              backgroundColor: event.color + '33',
                              color: event.color,
                            }}
                            onClick={() => handleEventClick(event)}
                          >
                            <div className="text-sm font-semibold">{event.title}</div>
                            <div className="text-xs opacity-75">
                              {format(parseISO(event.start), 'h:mm a')} -{' '}
                              {format(parseISO(event.end), 'h:mm a')}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
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
