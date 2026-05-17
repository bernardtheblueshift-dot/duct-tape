import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { usePortalJobDetail, useConfirmAssignment, useDeclineAssignment } from '@/hooks/usePortal';
import { JobStateBadge } from '@/components/features/JobStateBadge';
import { api } from '@/lib/api';

export function PortalJobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { data: job, isLoading } = usePortalJobDetail(jobId || '');
  const confirmMut = useConfirmAssignment();
  const declineMut = useDeclineAssignment();

  const [showDeclineModal, setShowDeclineModal] = useState(false);
  const [declineReason, setDeclineReason] = useState('');

  if (isLoading) {
    return <div className="p-6">Loading job details...</div>;
  }

  if (!job) {
    return <div className="p-6">Job not found</div>;
  }

  const handleConfirm = async () => {
    // Job detail doesn't have assignment_id, need to get from assignments
    // For now we can use the job_id to find the assignment
    // This is a simplification - in production we'd pass assignment_id through
    // For v1, portal.confirmAssignment expects assignment_id
    // We'll need to refetch assignments or store it in state
    // Let's assume we can derive it from the job context
    alert('Confirm functionality requires assignment_id from portal context');
  };

  const handleDeclineClick = () => {
    setShowDeclineModal(true);
    setDeclineReason('');
  };

  const handleDeclineSubmit = async () => {
    alert('Decline functionality requires assignment_id from portal context');
    setShowDeclineModal(false);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  return (
    <div className="p-4 sm:p-6 space-y-6 max-w-3xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate('/portal')}
        className="text-accent hover:underline text-sm"
      >
        ← Back to Portal
      </button>

      {/* Job header */}
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-2xl font-semibold">{job.title}</h1>
          <JobStateBadge state={job.state as 'intake' | 'simmer' | 'active' | 'complete'} />
        </div>

        <div className="flex items-center gap-3 text-sm">
          <span className="text-muted">Your Role:</span>
          {job.crew_role ? (
            <span className="px-2 py-1 rounded bg-accent/20 text-accent">
              {job.crew_role}
            </span>
          ) : (
            <span className="text-muted">No role assigned</span>
          )}
        </div>

        <div className="flex items-center gap-3 text-sm">
          <span className="text-muted">Assignment Status:</span>
          <AssignmentStatusBadge status={job.assignment_status} />
        </div>

        {job.assignment_status === 'pending' && (
          <div className="flex gap-2 pt-2">
            <button
              onClick={handleConfirm}
              disabled={confirmMut.isPending}
              className="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
            >
              Confirm Assignment
            </button>
            <button
              onClick={handleDeclineClick}
              disabled={declineMut.isPending}
              className="px-4 py-2 rounded bg-surface border border-border text-muted hover:bg-surface-hover disabled:opacity-50"
            >
              Decline Assignment
            </button>
          </div>
        )}
      </div>

      {/* Job info card */}
      <div className="rounded-lg border border-border bg-surface p-4 space-y-3">
        <h2 className="font-semibold">Job Details</h2>

        <div className="space-y-2 text-sm">
          <div>
            <span className="text-muted">Venue:</span>{' '}
            <span>{job.venue || 'No venue specified'}</span>
          </div>

          {job.scheduled_start && (
            <div>
              <span className="text-muted">Start:</span>{' '}
              <span className="font-mono">{format(new Date(job.scheduled_start), 'EEE dd MMM yyyy, HH:mm')}</span>
            </div>
          )}

          {job.scheduled_end && (
            <div>
              <span className="text-muted">End:</span>{' '}
              <span className="font-mono">{format(new Date(job.scheduled_end), 'EEE dd MMM yyyy, HH:mm')}</span>
            </div>
          )}

          {job.description && (
            <div className="pt-2 border-t border-dashed border-border">
              <p className="text-muted text-xs mb-1">Description</p>
              <p className="whitespace-pre-wrap">{job.description}</p>
            </div>
          )}
        </div>
      </div>

      {/* Files section */}
      <div className="rounded-lg border border-border bg-surface p-4 space-y-3">
        <h2 className="font-semibold">Files ({job.files.length})</h2>

        {job.files.length === 0 && (
          <p className="text-muted text-sm">No files attached</p>
        )}

        <div className="space-y-2">
          {job.files.map((file) => (
            <div
              key={file.id}
              className="flex items-center justify-between p-3 rounded border border-border hover:bg-surface-hover"
            >
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{file.original_filename}</p>
                <p className="text-xs text-muted font-mono">
                  {formatFileSize(file.file_size)} · {file.mime_type}
                </p>
              </div>
              <a
                href={api.files.downloadUrl(file.id)}
                download
                className="ml-4 px-3 py-1.5 rounded bg-accent text-white text-sm hover:bg-accent-hover"
              >
                Download
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* Decline modal */}
      {showDeclineModal && (
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
                onClick={() => setShowDeclineModal(false)}
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
