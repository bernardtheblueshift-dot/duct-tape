import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { ArrowLeft, Trash2, Edit2, X } from 'lucide-react';
import { api } from '@/lib/api';
import { useJob, useTransitionJob, useUpdateJob, useDeleteJob } from '@/hooks/useJobs';
import { JobStateBadge } from '@/components/features/JobStateBadge';
import { JobForm } from '@/components/features/JobForm';
import { useCrewList } from '@/hooks/useCrew';
import { useEquipmentList } from '@/hooks/useEquipment';
import type { JobState, MessageCreate, TaskCreate, TaskPriority, CrewAssignmentCreate, EquipmentAssignmentCreate, FileResponse } from '@/types/api';

const STATE_TRANSITIONS: Record<JobState, JobState | null> = {
  intake: 'simmer',
  simmer: 'active',
  active: 'complete',
  complete: null,
};

const STATE_COLORS: Record<JobState, string> = {
  intake: 'bg-job-intake hover:bg-job-intake/90',
  simmer: 'bg-job-simmer hover:bg-job-simmer/90',
  active: 'bg-job-active hover:bg-job-active/90',
  complete: 'bg-job-complete hover:bg-job-complete/90',
};

export function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'crew' | 'equipment' | 'messages' | 'tasks' | 'files'>('crew');
  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const { data: job, isLoading } = useJob(jobId!);
  const transitionMutation = useTransitionJob();
  const updateMutation = useUpdateJob();
  const deleteMutation = useDeleteJob();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 bg-surface animate-pulse rounded" />
        <div className="h-32 bg-surface animate-pulse rounded-lg" />
      </div>
    );
  }

  if (!job) {
    return (
      <div className="text-center py-12">
        <p className="text-muted">Job not found</p>
      </div>
    );
  }

  const nextState = STATE_TRANSITIONS[job.state];

  const handleTransition = () => {
    if (!nextState) return;
    transitionMutation.mutate({
      id: job.id,
      data: { new_state: nextState }
    });
  };

  const handleUpdate = (data: any) => {
    updateMutation.mutate(
      { id: job.id, data },
      {
        onSuccess: () => {
          setIsEditing(false);
        }
      }
    );
  };

  const handleDelete = () => {
    deleteMutation.mutate(job.id, {
      onSuccess: () => {
        navigate('/jobs');
      }
    });
  };

  if (isEditing) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/jobs')}
            className="p-2 hover:bg-surface rounded-md transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-2xl font-semibold">Edit Job</h1>
        </div>
        <div className="bg-surface border border-border rounded-lg p-6">
          <JobForm
            initialData={job}
            onSubmit={handleUpdate}
            onCancel={() => setIsEditing(false)}
            loading={updateMutation.isPending}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1">
          <button
            onClick={() => navigate('/jobs')}
            className="p-2 hover:bg-surface rounded-md transition-colors mt-1"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-semibold">{job.title}</h1>
              <JobStateBadge state={job.state} />
            </div>
            <p className="text-muted font-mono text-sm">ID: {job.id}</p>
          </div>
        </div>
        <div className="flex gap-2">
          {nextState && (
            <button
              onClick={handleTransition}
              disabled={transitionMutation.isPending}
              className={`px-4 py-2 text-primary rounded-md transition-colors font-medium disabled:opacity-50 ${STATE_COLORS[nextState]}`}
            >
              Advance to {nextState.charAt(0).toUpperCase() + nextState.slice(1)}
            </button>
          )}
          <button
            onClick={() => setIsEditing(true)}
            className="p-2 hover:bg-surface rounded-md transition-colors"
          >
            <Edit2 className="w-5 h-5" />
          </button>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="p-2 hover:bg-surface rounded-md transition-colors text-red-500"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Info Section */}
      <div className="bg-surface border border-border rounded-lg p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-muted mb-1">Venue</div>
            <div className="text-base">{job.venue || '—'}</div>
          </div>
          <div>
            <div className="text-sm text-muted mb-1">State</div>
            <div className="text-base capitalize">{job.state}</div>
          </div>
          <div>
            <div className="text-sm text-muted mb-1">Scheduled Start</div>
            <div className="text-base font-mono">
              {job.scheduled_start ? format(new Date(job.scheduled_start), 'EEE dd MMM yyyy, HH:mm') : 'TBD'}
            </div>
          </div>
          <div>
            <div className="text-sm text-muted mb-1">Scheduled End</div>
            <div className="text-base font-mono">
              {job.scheduled_end ? format(new Date(job.scheduled_end), 'EEE dd MMM yyyy, HH:mm') : 'TBD'}
            </div>
          </div>
        </div>
        {job.description && (
          <div>
            <div className="text-sm text-muted mb-1">Description</div>
            <div className="text-base whitespace-pre-wrap">{job.description}</div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-border">
        <div className="flex gap-6">
          {[
            { key: 'crew' as const, label: 'Crew', count: job.assigned_crew.length },
            { key: 'equipment' as const, label: 'Equipment', count: job.assigned_gear.length },
            { key: 'messages' as const, label: 'Messages', count: job.coordination.message_count },
            { key: 'tasks' as const, label: 'Tasks', count: job.coordination.task_total },
            { key: 'files' as const, label: 'Files', count: job.coordination.file_count },
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`pb-3 px-1 text-sm font-medium transition-colors relative ${
                activeTab === tab.key
                  ? 'text-primary border-b-2 border-accent'
                  : 'text-muted hover:text-primary'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="pb-8">
        {activeTab === 'crew' && <CrewTab jobId={job.id} assignments={job.assigned_crew} />}
        {activeTab === 'equipment' && <EquipmentTab jobId={job.id} assignments={job.assigned_gear} />}
        {activeTab === 'messages' && <MessagesTab jobId={job.id} />}
        {activeTab === 'tasks' && <TasksTab jobId={job.id} />}
        {activeTab === 'files' && <FilesTab jobId={job.id} />}
      </div>

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-background rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-semibold mb-4">Delete Job?</h2>
            <p className="text-muted mb-6">
              Are you sure you want to delete "{job.title}"? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={handleDelete}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors disabled:opacity-50"
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 bg-surface border border-border rounded-md hover:bg-surface-hover transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Crew Tab
function CrewTab({ jobId, assignments }: { jobId: string; assignments: any[] }) {
  const [showAssignModal, setShowAssignModal] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Assigned Crew</h3>
        <button
          onClick={() => setShowAssignModal(true)}
          className="px-4 py-2 bg-accent text-primary rounded-md hover:bg-accent/90 transition-colors text-sm font-medium"
        >
          Assign Crew
        </button>
      </div>
      {assignments.length === 0 ? (
        <div className="text-center py-8 text-muted text-sm">No crew assigned yet</div>
      ) : (
        <div className="space-y-2">
          {assignments.map(assignment => (
            <div key={assignment.id} className="bg-surface border border-border rounded-lg p-4 flex items-center justify-between">
              <div className="space-y-1">
                <div className="font-medium">{assignment.crew_name || 'Unknown'}</div>
                <div className="text-sm text-muted">{assignment.role || '—'}</div>
              </div>
              <span className={`px-2.5 py-0.5 text-xs font-medium rounded-full ${
                assignment.status === 'confirmed' ? 'bg-green-500/20 text-green-500' :
                assignment.status === 'pending' ? 'bg-yellow-500/20 text-yellow-500' :
                'bg-red-500/20 text-red-500'
              }`}>
                {assignment.status}
              </span>
            </div>
          ))}
        </div>
      )}
      {showAssignModal && (
        <AssignCrewModal
          jobId={jobId}
          open={showAssignModal}
          onClose={() => setShowAssignModal(false)}
          onSuccess={() => setShowAssignModal(false)}
        />
      )}
    </div>
  );
}

// Equipment Tab
function EquipmentTab({ jobId, assignments }: { jobId: string; assignments: any[] }) {
  const [showAssignModal, setShowAssignModal] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Assigned Equipment</h3>
        <button
          onClick={() => setShowAssignModal(true)}
          className="px-4 py-2 bg-accent text-primary rounded-md hover:bg-accent/90 transition-colors text-sm font-medium"
        >
          Assign Equipment
        </button>
      </div>
      {assignments.length === 0 ? (
        <div className="text-center py-8 text-muted text-sm">No equipment assigned yet</div>
      ) : (
        <div className="space-y-2">
          {assignments.map(assignment => (
            <div key={assignment.id} className="bg-surface border border-border rounded-lg p-4 flex items-center justify-between">
              <div className="space-y-1">
                <div className="font-medium">{assignment.equipment_name}</div>
              </div>
              <div className="font-mono text-sm">Qty: {assignment.quantity_assigned}</div>
            </div>
          ))}
        </div>
      )}
      {showAssignModal && (
        <AssignEquipmentModal
          jobId={jobId}
          open={showAssignModal}
          onClose={() => setShowAssignModal(false)}
          onSuccess={() => setShowAssignModal(false)}
        />
      )}
    </div>
  );
}

// Messages Tab
function MessagesTab({ jobId }: { jobId: string }) {
  const qc = useQueryClient();
  const [newMessage, setNewMessage] = useState('');
  const { data: crewList = [] } = useCrewList();

  const { data: messages = [] } = useQuery({
    queryKey: ['messages', jobId],
    queryFn: () => api.messages.list(jobId),
  });

  const createMessage = useMutation({
    mutationFn: (data: MessageCreate) => api.messages.create(jobId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['messages', jobId] });
      setNewMessage('');
    },
  });

  const handleSend = () => {
    if (!newMessage.trim()) return;
    createMessage.mutate({ content: newMessage });
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Messages</h3>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="text-center py-8 text-muted text-sm">No messages yet</div>
        ) : (
          [...messages].reverse().map(msg => (
            <div key={msg.id} className="bg-surface border border-border rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="text-xs font-medium text-muted">
                  {crewList.find(c => c.user_id === msg.user_id)?.name || msg.user_id.substring(0, 8)}
                </div>
                <div className="font-mono text-xs text-muted">
                  {format(new Date(msg.created_at), 'dd MMM HH:mm')}
                </div>
              </div>
              <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
            </div>
          ))
        )}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type a message..."
          className="flex-1 rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
        />
        <button
          onClick={handleSend}
          disabled={!newMessage.trim() || createMessage.isPending}
          className="px-4 py-2 bg-accent text-primary rounded-md hover:bg-accent/90 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>
    </div>
  );
}

// Tasks Tab
function TasksTab({ jobId }: { jobId: string }) {
  const [showAddTaskModal, setShowAddTaskModal] = useState(false);
  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks', jobId],
    queryFn: () => api.tasks.list(jobId),
  });

  const statusColors = {
    todo: 'bg-yellow-500/20 text-yellow-500',
    in_progress: 'bg-blue-500/20 text-blue-500',
    done: 'bg-green-500/20 text-green-500',
  };

  const priorityColors = {
    low: 'bg-gray-500/20 text-gray-500',
    medium: 'bg-blue-500/20 text-blue-500',
    high: 'bg-orange-500/20 text-orange-500',
    urgent: 'bg-red-500/20 text-red-500',
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Tasks</h3>
        <button
          onClick={() => setShowAddTaskModal(true)}
          className="px-4 py-2 bg-accent text-primary rounded-md hover:bg-accent/90 transition-colors text-sm font-medium"
        >
          Add Task
        </button>
      </div>
      {tasks.length === 0 ? (
        <div className="text-center py-8 text-muted text-sm">No tasks yet</div>
      ) : (
        <div className="space-y-2">
          {tasks.map(task => (
            <div key={task.id} className="bg-surface border border-border rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="font-medium">{task.title}</div>
                <div className="flex gap-2">
                  <span className={`px-2.5 py-0.5 text-xs font-medium rounded-full ${statusColors[task.status]}`}>
                    {task.status.replace('_', ' ')}
                  </span>
                  <span className={`px-2.5 py-0.5 text-xs font-medium rounded-full ${priorityColors[task.priority]}`}>
                    {task.priority}
                  </span>
                </div>
              </div>
              {task.deadline && (
                <div className="text-xs text-muted font-mono">
                  Due: {format(new Date(task.deadline), 'dd MMM yyyy, HH:mm')}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      {showAddTaskModal && (
        <AddTaskModal
          jobId={jobId}
          open={showAddTaskModal}
          onClose={() => setShowAddTaskModal(false)}
          onSuccess={() => setShowAddTaskModal(false)}
        />
      )}
    </div>
  );
}

// AssignCrewModal
function AssignCrewModal({ jobId, open, onClose, onSuccess }: { jobId: string; open: boolean; onClose: () => void; onSuccess: () => void }) {
  const queryClient = useQueryClient();
  const [selectedCrewId, setSelectedCrewId] = useState('');
  const [role, setRole] = useState('');
  const [error, setError] = useState('');

  const { data: crewList = [] } = useCrewList();

  const createAssignment = useMutation({
    mutationFn: (data: CrewAssignmentCreate) => api.assignments.createCrew(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs', jobId] });
      onSuccess();
      onClose();
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to assign crew');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCrewId) return;
    setError('');
    createAssignment.mutate({
      crew_id: selectedCrewId,
      job_id: jobId,
      role: role.trim() || null,
    });
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-background rounded-lg p-6 max-w-md w-full">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Assign Crew</h2>
          <button onClick={onClose} className="p-1 hover:bg-surface rounded transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-muted mb-1 block">Crew Member</label>
            <select
              value={selectedCrewId}
              onChange={(e) => setSelectedCrewId(e.target.value)}
              required
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
            >
              <option value="">Select crew member...</option>
              {crewList.map(crew => (
                <option key={crew.id} value={crew.id}>
                  {crew.name || crew.email}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm text-muted mb-1 block">Role (optional)</label>
            <input
              type="text"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="e.g. Camera Operator"
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>
          {error && <div className="text-sm text-red-500">{error}</div>}
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={createAssignment.isPending || !selectedCrewId}
              className="px-4 py-2 bg-accent text-primary rounded-md hover:bg-accent/90 transition-colors text-sm font-medium disabled:opacity-50"
            >
              {createAssignment.isPending ? 'Assigning...' : 'Assign'}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={createAssignment.isPending}
              className="px-4 py-2 bg-surface border border-border rounded-md hover:bg-surface-hover transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// AssignEquipmentModal
function AssignEquipmentModal({ jobId, open, onClose, onSuccess }: { jobId: string; open: boolean; onClose: () => void; onSuccess: () => void }) {
  const queryClient = useQueryClient();
  const [selectedEquipmentId, setSelectedEquipmentId] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [error, setError] = useState('');

  const { data: equipmentList = [] } = useEquipmentList();

  const createAssignment = useMutation({
    mutationFn: (data: EquipmentAssignmentCreate) => api.assignments.createEquipment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs', jobId] });
      onSuccess();
      onClose();
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to assign equipment');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEquipmentId) return;
    setError('');
    createAssignment.mutate({
      equipment_id: selectedEquipmentId,
      job_id: jobId,
      quantity_assigned: quantity,
    });
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-background rounded-lg p-6 max-w-md w-full">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Assign Equipment</h2>
          <button onClick={onClose} className="p-1 hover:bg-surface rounded transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-muted mb-1 block">Equipment</label>
            <select
              value={selectedEquipmentId}
              onChange={(e) => setSelectedEquipmentId(e.target.value)}
              required
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
            >
              <option value="">Select equipment...</option>
              {equipmentList.map(equipment => (
                <option key={equipment.id} value={equipment.id}>
                  {equipment.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm text-muted mb-1 block">Quantity</label>
            <input
              type="number"
              min={1}
              value={quantity}
              onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
              required
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>
          {error && <div className="text-sm text-red-500">{error}</div>}
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={createAssignment.isPending || !selectedEquipmentId}
              className="px-4 py-2 bg-accent text-primary rounded-md hover:bg-accent/90 transition-colors text-sm font-medium disabled:opacity-50"
            >
              {createAssignment.isPending ? 'Assigning...' : 'Assign'}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={createAssignment.isPending}
              className="px-4 py-2 bg-surface border border-border rounded-md hover:bg-surface-hover transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// AddTaskModal
function AddTaskModal({ jobId, open, onClose, onSuccess }: { jobId: string; open: boolean; onClose: () => void; onSuccess: () => void }) {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<TaskPriority>('medium');
  const [deadline, setDeadline] = useState('');
  const [error, setError] = useState('');

  const createTask = useMutation({
    mutationFn: (data: TaskCreate) => api.tasks.create(jobId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', jobId] });
      queryClient.invalidateQueries({ queryKey: ['jobs', jobId] });
      onSuccess();
      onClose();
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to create task');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setError('');
    createTask.mutate({
      title: title.trim(),
      description: description.trim() || null,
      priority,
      deadline: deadline || null,
    });
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-background rounded-lg p-6 max-w-md w-full">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Add Task</h2>
          <button onClick={onClose} className="p-1 hover:bg-surface rounded transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-muted mb-1 block">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>
          <div>
            <label className="text-sm text-muted mb-1 block">Description (optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>
          <div>
            <label className="text-sm text-muted mb-1 block">Priority</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as TaskPriority)}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-muted mb-1 block">Deadline (optional)</label>
            <input
              type="datetime-local"
              value={deadline}
              onChange={(e) => setDeadline(e.target.value)}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>
          {error && <div className="text-sm text-red-500">{error}</div>}
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={createTask.isPending || !title.trim()}
              className="px-4 py-2 bg-accent text-primary rounded-md hover:bg-accent/90 transition-colors text-sm font-medium disabled:opacity-50"
            >
              {createTask.isPending ? 'Creating...' : 'Create Task'}
            </button>
            <button
              type="button"
              onClick={onClose}
              disabled={createTask.isPending}
              className="px-4 py-2 bg-surface border border-border rounded-md hover:bg-surface-hover transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// FilePreviewModal
function FilePreviewModal({ file, open, onClose }: { file: FileResponse; open: boolean; onClose: () => void }) {
  if (!open) return null;

  const isImage = file.mime_type.startsWith('image/');
  const isPDF = file.mime_type === 'application/pdf';
  const canPreview = isImage || isPDF;

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-background rounded-lg p-4 max-w-4xl w-full max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium">{file.original_filename}</h2>
          <button onClick={onClose} className="p-1 hover:bg-surface rounded transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="flex-1 overflow-auto mb-4">
          {isImage && (
            <div className="bg-black/20 rounded p-4 flex items-center justify-center">
              <img
                src={api.files.downloadUrl(file.id)}
                alt={file.original_filename}
                className="max-w-full max-h-[70vh] object-contain mx-auto rounded"
              />
            </div>
          )}
          {isPDF && (
            <iframe
              src={api.files.downloadUrl(file.id)}
              className="w-full h-[70vh] rounded border border-border"
              title={file.original_filename}
            />
          )}
          {!canPreview && (
            <div className="text-center py-12 text-muted">
              <p className="mb-4">Preview not available for this file type</p>
              <a
                href={api.files.downloadUrl(file.id)}
                download
                className="px-4 py-2 bg-accent text-primary rounded-md hover:bg-accent/90 transition-colors text-sm font-medium inline-block"
              >
                Download File
              </a>
            </div>
          )}
        </div>
        <div className="flex items-center justify-between border-t border-border pt-4">
          <div className="flex gap-4 text-xs text-muted font-mono">
            <span>{file.mime_type}</span>
            <span>{formatFileSize(file.file_size)}</span>
            <span>{format(new Date(file.created_at), 'dd MMM yyyy')}</span>
          </div>
          <a
            href={api.files.downloadUrl(file.id)}
            download
            className="px-4 py-2 bg-accent text-primary rounded-md hover:bg-accent/90 transition-colors text-sm font-medium"
          >
            Download
          </a>
        </div>
      </div>
    </div>
  );
}

// Files Tab
function FilesTab({ jobId }: { jobId: string }) {
  const qc = useQueryClient();
  const [previewFile, setPreviewFile] = useState<FileResponse | null>(null);
  const { data: files = [] } = useQuery({
    queryKey: ['files', jobId],
    queryFn: () => api.files.list(jobId),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.files.upload(jobId, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['files', jobId] });
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadMutation.mutate(file);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Files</h3>
        <label className="px-4 py-2 bg-accent text-primary rounded-md hover:bg-accent/90 transition-colors text-sm font-medium cursor-pointer">
          Upload File
          <input
            type="file"
            onChange={handleFileSelect}
            className="hidden"
            disabled={uploadMutation.isPending}
          />
        </label>
      </div>
      {uploadMutation.isPending && (
        <div className="bg-surface border border-border rounded-lg p-4 text-center text-sm text-muted">
          Uploading...
        </div>
      )}
      {files.length === 0 ? (
        <div className="text-center py-8 text-muted text-sm">No files uploaded yet</div>
      ) : (
        <div className="space-y-2">
          {files.map(file => (
            <div key={file.id} className="bg-surface border border-border rounded-lg p-4 flex items-center justify-between">
              <div className="space-y-1 flex-1">
                <div className="font-medium">{file.original_filename}</div>
                <div className="flex gap-3 text-xs text-muted">
                  <span className="font-mono">{file.mime_type}</span>
                  <span className="font-mono">{formatFileSize(file.file_size)}</span>
                  <span className="font-mono">{format(new Date(file.created_at), 'dd MMM yyyy')}</span>
                </div>
              </div>
              <div className="flex gap-2">
                {(file.mime_type.startsWith('image/') || file.mime_type === 'application/pdf') && (
                  <button
                    onClick={() => setPreviewFile(file)}
                    className="px-3 py-1.5 bg-accent/20 text-accent border border-accent/30 rounded-md hover:bg-accent/30 text-sm font-medium transition-colors"
                  >
                    Preview
                  </button>
                )}
                <a
                  href={api.files.downloadUrl(file.id)}
                  download
                  className="px-3 py-1.5 bg-surface-hover border border-border rounded-md hover:bg-surface text-sm font-medium transition-colors"
                >
                  Download
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
      {previewFile && (
        <FilePreviewModal
          file={previewFile}
          open={!!previewFile}
          onClose={() => setPreviewFile(null)}
        />
      )}
    </div>
  );
}
