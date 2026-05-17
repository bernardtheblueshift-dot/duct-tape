import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import {
  usePortalDashboard,
  usePortalProfile,
  usePortalAvailability,
  useConfirmAssignment,
  useDeclineAssignment,
  useUpdatePortalProfile,
  useUpdatePortalAvailability,
} from '@/hooks/usePortal';
import type { AvailabilityPatternCreate } from '@/types/api';

export function PortalPage() {
  const navigate = useNavigate();
  const { data: dashboard, isLoading: dashLoading } = usePortalDashboard();
  const { data: profile, isLoading: profileLoading } = usePortalProfile();
  const { data: availability, isLoading: availLoading } = usePortalAvailability();
  const confirmMut = useConfirmAssignment();
  const declineMut = useDeclineAssignment();
  const updateProfileMut = useUpdatePortalProfile();
  const updateAvailMut = useUpdatePortalAvailability();

  const [declineModalId, setDeclineModalId] = useState<string | null>(null);
  const [declineReason, setDeclineReason] = useState('');
  const [phone, setPhone] = useState('');
  const [bio, setBio] = useState('');
  const [profileEdited, setProfileEdited] = useState(false);

  // Initialize profile fields when data loads
  useState(() => {
    if (profile && !profileEdited) {
      setPhone(profile.phone || '');
      setBio(profile.bio || '');
    }
  });

  const handleConfirm = async (id: string) => {
    await confirmMut.mutateAsync(id);
  };

  const handleDeclineClick = (id: string) => {
    setDeclineModalId(id);
    setDeclineReason('');
  };

  const handleDeclineSubmit = async () => {
    if (!declineModalId) return;
    await declineMut.mutateAsync({ id: declineModalId, reason: declineReason || undefined });
    setDeclineModalId(null);
    setDeclineReason('');
  };

  const handleProfileSave = async () => {
    await updateProfileMut.mutateAsync({ phone: phone || null, bio: bio || null });
    setProfileEdited(false);
  };

  const handleAvailabilityToggle = (dayOfWeek: number) => {
    const current = availability || [];
    const existing = current.find((p) => p.day_of_week === dayOfWeek);
    const newAvail = existing ? !existing.is_available : true;

    const patterns: AvailabilityPatternCreate[] = [];
    for (let d = 0; d < 7; d++) {
      const dayPattern = current.find((p) => p.day_of_week === d);
      patterns.push({
        day_of_week: d,
        is_available: d === dayOfWeek ? newAvail : (dayPattern?.is_available || false),
      });
    }

    updateAvailMut.mutate(patterns);
  };

  const getAvailabilityForDay = (dayOfWeek: number): boolean => {
    return availability?.find((p) => p.day_of_week === dayOfWeek)?.is_available || false;
  };

  if (dashLoading || profileLoading || availLoading) {
    return <div className="p-6">Loading portal...</div>;
  }

  const counts = dashboard?.counts || { pending_assignments: 0, unread_messages: 0 };
  const upcoming = dashboard?.upcoming || [];
  const recent = dashboard?.recent || [];

  return (
    <div className="p-4 sm:p-6 space-y-6 max-w-3xl mx-auto">
      {/* Notification banner */}
      {(counts.pending_assignments > 0 || counts.unread_messages > 0) && (
        <div className="rounded-lg border border-yellow-400 bg-yellow-400/10 p-4">
          <p className="text-yellow-300 text-sm">
            {counts.pending_assignments > 0 && (
              <span>You have {counts.pending_assignments} pending assignment(s)</span>
            )}
            {counts.pending_assignments > 0 && counts.unread_messages > 0 && ' and '}
            {counts.unread_messages > 0 && (
              <span>{counts.unread_messages} unread message(s)</span>
            )}
          </p>
        </div>
      )}

      {/* Upcoming assignments */}
      <section>
        <h2 className="text-xl font-semibold mb-3">
          Upcoming <span className="text-muted text-base ml-2">({upcoming.length})</span>
        </h2>
        <div className="space-y-3">
          {upcoming.length === 0 && (
            <p className="text-muted text-sm">No upcoming assignments</p>
          )}
          {upcoming.map((item) => (
            <div
              key={item.assignment_id}
              className="rounded-lg border border-border bg-surface p-4 space-y-2 cursor-pointer hover:border-accent transition-colors"
              onClick={(e) => {
                // Don't navigate if clicking buttons
                if ((e.target as HTMLElement).closest('button')) return;
                navigate(`/portal/jobs/${item.job_id}`);
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold">{item.job_title}</h3>
                  {item.job_venue && (
                    <p className="text-muted text-sm">{item.job_venue}</p>
                  )}
                </div>
                <AssignmentStatusBadge status={item.status} />
              </div>

              {item.scheduled_start && (
                <p className="font-mono text-sm text-muted">
                  {format(new Date(item.scheduled_start), 'EEE dd MMM, HH:mm')}
                </p>
              )}

              {item.role && (
                <div className="inline-block px-2 py-1 rounded bg-accent/20 text-accent text-xs">
                  {item.role}
                </div>
              )}

              {item.status === 'pending' && (
                <div className="flex gap-2 pt-2 border-t border-dashed border-border">
                  <button
                    onClick={() => handleConfirm(item.assignment_id)}
                    disabled={confirmMut.isPending}
                    className="px-3 py-1.5 rounded bg-green-600 text-white text-sm hover:bg-green-700 disabled:opacity-50"
                  >
                    Confirm
                  </button>
                  <button
                    onClick={() => handleDeclineClick(item.assignment_id)}
                    disabled={declineMut.isPending}
                    className="px-3 py-1.5 rounded bg-surface border border-border text-muted text-sm hover:bg-surface-hover disabled:opacity-50"
                  >
                    Decline
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Recent assignments */}
      <section>
        <h2 className="text-xl font-semibold mb-3">Recent</h2>
        <div className="space-y-3">
          {recent.length === 0 && (
            <p className="text-muted text-sm">No recent assignments</p>
          )}
          {recent.map((item) => (
            <div
              key={item.assignment_id}
              className="rounded-lg border border-border/50 bg-surface/50 p-4 space-y-2 opacity-70 cursor-pointer hover:opacity-100 transition-opacity"
              onClick={() => navigate(`/portal/jobs/${item.job_id}`)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold">{item.job_title}</h3>
                  {item.job_venue && (
                    <p className="text-muted text-sm">{item.job_venue}</p>
                  )}
                </div>
                <AssignmentStatusBadge status={item.status} />
              </div>

              {item.scheduled_start && (
                <p className="font-mono text-sm text-muted">
                  {format(new Date(item.scheduled_start), 'EEE dd MMM, HH:mm')}
                </p>
              )}

              {item.role && (
                <div className="inline-block px-2 py-1 rounded bg-accent/20 text-accent text-xs">
                  {item.role}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Profile section */}
      <section>
        <h2 className="text-xl font-semibold mb-3">Profile</h2>
        <div className="rounded-lg border border-border bg-surface p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Phone</label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => { setPhone(e.target.value); setProfileEdited(true); }}
              className="w-full px-3 py-2 rounded border border-border bg-surface text-primary focus:outline-none focus:ring-1 focus:ring-accent"
              placeholder="Your phone number"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Bio</label>
            <textarea
              value={bio}
              onChange={(e) => { setBio(e.target.value); setProfileEdited(true); }}
              rows={3}
              className="w-full px-3 py-2 rounded border border-border bg-surface text-primary focus:outline-none focus:ring-1 focus:ring-accent resize-none"
              placeholder="Tell us about yourself"
            />
          </div>

          {profileEdited && (
            <button
              onClick={handleProfileSave}
              disabled={updateProfileMut.isPending}
              className="px-4 py-2 rounded bg-accent text-white hover:bg-accent-hover disabled:opacity-50"
            >
              {updateProfileMut.isPending ? 'Saving...' : 'Save Profile'}
            </button>
          )}
        </div>
      </section>

      {/* Availability section */}
      <section>
        <h2 className="text-xl font-semibold mb-3">Weekly Availability</h2>
        <div className="grid grid-cols-7 gap-2">
          {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((label, idx) => {
            const isAvailable = getAvailabilityForDay(idx);
            return (
              <button
                key={idx}
                onClick={() => handleAvailabilityToggle(idx)}
                disabled={updateAvailMut.isPending}
                className={`p-3 rounded text-xs font-mono font-semibold transition-colors disabled:opacity-50 ${
                  isAvailable
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-surface border border-border text-muted hover:bg-surface-hover'
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>
      </section>

      {/* Decline modal */}
      {declineModalId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-surface rounded-lg border border-border p-6 max-w-md w-full space-y-4">
            <h3 className="text-lg font-semibold">Decline Assignment</h3>
            <p className="text-sm text-muted">Optional: Provide a reason for declining</p>
            <textarea
              value={declineReason}
              onChange={(e) => setDeclineReason(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 rounded border border-border bg-surface text-primary focus:outline-none focus:ring-1 focus:ring-accent resize-none"
              placeholder="Reason (optional)"
            />
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setDeclineModalId(null)}
                className="px-4 py-2 rounded bg-surface border border-border text-muted hover:bg-surface-hover"
              >
                Cancel
              </button>
              <button
                onClick={handleDeclineSubmit}
                disabled={declineMut.isPending}
                className="px-4 py-2 rounded bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
              >
                {declineMut.isPending ? 'Declining...' : 'Decline'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function AssignmentStatusBadge({ status }: { status: string }) {
  const colors = {
    pending: 'bg-yellow-400/20 text-yellow-300 border-yellow-400',
    confirmed: 'bg-green-600/20 text-green-300 border-green-600',
    declined: 'bg-muted/20 text-muted border-muted',
  };

  const color = colors[status as keyof typeof colors] || 'bg-muted/20 text-muted border-muted';

  return (
    <span className={`px-2 py-1 rounded text-xs border ${color}`}>
      {status}
    </span>
  );
}
