import {
  type User, type LoginRequest, type RegisterRequest, type InviteRequest,
  type JobResponse, type JobCreate, type JobUpdate, type JobTransitionRequest,
  type CrewProfileResponse, type CrewProfileCreate, type CrewProfileUpdate,
  type CrewRatingCreate, type CrewRatingResponse,
  type AvailabilityPatternCreate, type AvailabilityPatternResponse,
  type SkillsMatrixResponse,
  type EquipmentResponse, type EquipmentCreate, type EquipmentUpdate, type EquipmentCondition,
  type CrewAssignmentCreate, type CrewAssignmentResponse,
  type EquipmentAssignmentCreate, type EquipmentAssignmentResponse,
  type CalendarEventsResponse, type CrewAvailabilitySummary, type AvailabilityDay,
  type MessageResponse, type MessageCreate,
  type TaskResponse, type TaskCreate, type TaskUpdate, type TaskStatus,
  type FileResponse,
  type NotificationCounts,
  type PortalDashboardResponse, type PortalJobDetailResponse,
  type PortalAssignmentDetail,
  type ApiMessage,
} from '@/types/api';

class APIError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'APIError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(endpoint, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new APIError(response.status, error.detail || 'Unknown error');
  }

  if (response.status === 204) return undefined as T;
  return response.json();
}

export const api = {
  auth: {
    login: (data: LoginRequest) => request<ApiMessage>('/api/v1/auth/login', { method: 'POST', body: JSON.stringify(data) }),
    register: (data: RegisterRequest) => request<ApiMessage>('/api/v1/auth/register', { method: 'POST', body: JSON.stringify(data) }),
    logout: () => request<ApiMessage>('/api/v1/auth/logout', { method: 'POST' }),
    me: () => request<User>('/api/v1/auth/me'),
    refresh: () => request<ApiMessage>('/api/v1/auth/refresh', { method: 'POST' }),
    verifyEmail: (token: string) => request<ApiMessage>('/api/v1/auth/verify-email', { method: 'POST', body: JSON.stringify({ token }) }),
    resetPasswordRequest: (email: string) => request<ApiMessage>('/api/v1/auth/reset-password-request', { method: 'POST', body: JSON.stringify({ email }) }),
    resetPassword: (token: string, new_password: string) => request<ApiMessage>('/api/v1/auth/reset-password', { method: 'POST', body: JSON.stringify({ token, new_password }) }),
    wsToken: () => request<{ token: string }>('/api/v1/auth/ws-token'),
    invite: (data: InviteRequest) => request<ApiMessage>('/api/v1/invitations/', { method: 'POST', body: JSON.stringify(data) }),
  },
  invitations: {
    create: (data: InviteRequest) => request<ApiMessage>('/api/v1/invitations/', { method: 'POST', body: JSON.stringify(data) }),
  },
  jobs: {
    list: (params?: { search?: string; state?: string; venue?: string; start_date?: string; end_date?: string }) => {
      const query = new URLSearchParams();
      if (params) Object.entries(params).forEach(([k, v]) => { if (v) query.set(k, v); });
      return request<JobResponse[]>(`/api/v1/jobs?${query}`);
    },
    get: (id: string) => request<JobResponse>(`/api/v1/jobs/${id}`),
    create: (data: JobCreate) => request<JobResponse>('/api/v1/jobs', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: JobUpdate) => request<JobResponse>(`/api/v1/jobs/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    delete: (id: string) => request<void>(`/api/v1/jobs/${id}`, { method: 'DELETE' }),
    transition: (id: string, data: JobTransitionRequest) => request<JobResponse>(`/api/v1/jobs/${id}/transition`, { method: 'POST', body: JSON.stringify(data) }),
  },
  crew: {
    list: (params?: { search?: string; skill?: string; available_start?: string; available_end?: string; role?: string }) => {
      const query = new URLSearchParams();
      if (params) Object.entries(params).forEach(([k, v]) => { if (v) query.set(k, v); });
      return request<CrewProfileResponse[]>(`/api/v1/crew?${query}`);
    },
    get: (id: string) => request<CrewProfileResponse>(`/api/v1/crew/${id}`),
    create: (data: CrewProfileCreate) => request<CrewProfileResponse>('/api/v1/crew', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: CrewProfileUpdate) => request<CrewProfileResponse>(`/api/v1/crew/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    archive: (id: string) => request<CrewProfileResponse>(`/api/v1/crew/${id}/archive`, { method: 'POST' }),
    unarchive: (id: string) => request<CrewProfileResponse>(`/api/v1/crew/${id}/unarchive`, { method: 'POST' }),
    rate: (id: string, jobId: string, data: CrewRatingCreate) => request<CrewRatingResponse>(`/api/v1/crew/${id}/ratings/${jobId}`, { method: 'POST', body: JSON.stringify(data) }),
    ratings: (id: string) => request<CrewRatingResponse[]>(`/api/v1/crew/${id}/ratings`),
    skillsMatrix: () => request<SkillsMatrixResponse>('/api/v1/crew/skills-matrix'),
    setAvailability: (id: string, patterns: AvailabilityPatternCreate[]) => request<AvailabilityPatternResponse[]>(`/api/v1/crew/${id}/availability`, { method: 'PUT', body: JSON.stringify(patterns) }),
    getAvailability: (id: string) => request<AvailabilityPatternResponse[]>(`/api/v1/crew/${id}/availability`),
  },
  equipment: {
    list: (params?: { search?: string; category?: string; condition?: string }) => {
      const query = new URLSearchParams();
      if (params) Object.entries(params).forEach(([k, v]) => { if (v) query.set(k, v); });
      return request<EquipmentResponse[]>(`/api/v1/equipment?${query}`);
    },
    get: (id: string) => request<EquipmentResponse>(`/api/v1/equipment/${id}`),
    create: (data: EquipmentCreate) => request<EquipmentResponse>('/api/v1/equipment', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: EquipmentUpdate) => request<EquipmentResponse>(`/api/v1/equipment/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    delete: (id: string) => request<void>(`/api/v1/equipment/${id}`, { method: 'DELETE' }),
    updateCondition: (id: string, condition: EquipmentCondition) => request<EquipmentResponse>(`/api/v1/equipment/${id}/condition`, { method: 'PATCH', body: JSON.stringify({ condition }) }),
  },
  assignments: {
    createCrew: (data: CrewAssignmentCreate) => request<CrewAssignmentResponse>('/api/v1/assignments/crew', { method: 'POST', body: JSON.stringify(data) }),
    createEquipment: (data: EquipmentAssignmentCreate) => request<EquipmentAssignmentResponse>('/api/v1/assignments/equipment', { method: 'POST', body: JSON.stringify(data) }),
    transitionCrew: (id: string, new_status: string, declined_reason?: string) => request<CrewAssignmentResponse>(`/api/v1/assignments/crew/${id}/transition`, { method: 'POST', body: JSON.stringify({ new_status, declined_reason }) }),
    getJobCrew: (jobId: string) => request<CrewAssignmentResponse[]>(`/api/v1/assignments/job/${jobId}/crew`),
    getJobEquipment: (jobId: string) => request<EquipmentAssignmentResponse[]>(`/api/v1/assignments/job/${jobId}/equipment`),
    deleteCrew: (id: string) => request<void>(`/api/v1/assignments/crew/${id}`, { method: 'DELETE' }),
    deleteEquipment: (id: string) => request<void>(`/api/v1/assignments/equipment/${id}`, { method: 'DELETE' }),
  },
  calendar: {
    events: (params: { start_date: string; end_date: string; resource_type?: string }) => {
      const query = new URLSearchParams(params as Record<string, string>);
      return request<CalendarEventsResponse>(`/api/v1/calendar/events?${query}`);
    },
    crewEvents: (crewId: string, params: { start_date: string; end_date: string }) => {
      const query = new URLSearchParams(params);
      return request<CalendarEventsResponse>(`/api/v1/calendar/crew/${crewId}?${query}`);
    },
    equipmentEvents: (equipmentId: string, params: { start_date: string; end_date: string }) => {
      const query = new URLSearchParams(params);
      return request<CalendarEventsResponse>(`/api/v1/calendar/equipment/${equipmentId}?${query}`);
    },
    crewAvailability: (crewId: string, params: { start_date: string; end_date: string }) => {
      const query = new URLSearchParams(params);
      return request<AvailabilityDay[]>(`/api/v1/calendar/crew/${crewId}/availability?${query}`);
    },
    bulkAvailability: (params: { start_date: string; end_date: string }) => {
      const query = new URLSearchParams(params);
      return request<CrewAvailabilitySummary[]>(`/api/v1/calendar/availability?${query}`);
    },
  },
  messages: {
    list: (jobId: string, params?: { search?: string }) => {
      const query = new URLSearchParams();
      if (params?.search) query.set('search', params.search);
      return request<MessageResponse[]>(`/api/v1/jobs/${jobId}/messages?${query}`);
    },
    get: (jobId: string, messageId: string) => request<MessageResponse>(`/api/v1/jobs/${jobId}/messages/${messageId}`),
    create: (jobId: string, data: MessageCreate) => request<MessageResponse>(`/api/v1/jobs/${jobId}/messages`, { method: 'POST', body: JSON.stringify(data) }),
  },
  tasks: {
    list: (jobId: string, params?: { status?: string; assignee_id?: string; priority?: string }) => {
      const query = new URLSearchParams();
      if (params) Object.entries(params).forEach(([k, v]) => { if (v) query.set(k, v); });
      return request<TaskResponse[]>(`/api/v1/jobs/${jobId}/tasks?${query}`);
    },
    get: (jobId: string, taskId: string) => request<TaskResponse>(`/api/v1/jobs/${jobId}/tasks/${taskId}`),
    create: (jobId: string, data: TaskCreate) => request<TaskResponse>(`/api/v1/jobs/${jobId}/tasks`, { method: 'POST', body: JSON.stringify(data) }),
    update: (jobId: string, taskId: string, data: TaskUpdate) => request<TaskResponse>(`/api/v1/jobs/${jobId}/tasks/${taskId}`, { method: 'PATCH', body: JSON.stringify(data) }),
    updateStatus: (jobId: string, taskId: string, status: TaskStatus) => request<TaskResponse>(`/api/v1/jobs/${jobId}/tasks/${taskId}/status`, { method: 'POST', body: JSON.stringify({ status }) }),
    delete: (jobId: string, taskId: string) => request<void>(`/api/v1/jobs/${jobId}/tasks/${taskId}`, { method: 'DELETE' }),
  },
  files: {
    list: (jobId: string) => request<FileResponse[]>(`/api/v1/jobs/${jobId}/files`),
    upload: async (jobId: string, file: File): Promise<FileResponse> => {
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(`/api/v1/jobs/${jobId}/files`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new APIError(response.status, error.detail);
      }
      return response.json();
    },
    get: (fileId: string) => request<FileResponse>(`/api/v1/files/${fileId}`),
    downloadUrl: (fileId: string) => `/api/v1/files/${fileId}/download`,
    delete: (fileId: string) => request<void>(`/api/v1/files/${fileId}`, { method: 'DELETE' }),
  },
  notifications: {
    counts: () => request<NotificationCounts>('/api/v1/notifications/counts'),
  },
  portal: {
    dashboard: () => request<PortalDashboardResponse>('/api/v1/portal/dashboard'),
    jobDetail: (jobId: string) => request<PortalJobDetailResponse>(`/api/v1/portal/jobs/${jobId}`),
    assignments: () => request<PortalAssignmentDetail[]>('/api/v1/portal/assignments'),
    confirmAssignment: (id: string) => request<CrewAssignmentResponse>(`/api/v1/portal/assignments/${id}/confirm`, { method: 'POST' }),
    declineAssignment: (id: string, reason?: string) => request<CrewAssignmentResponse>(`/api/v1/portal/assignments/${id}/decline`, { method: 'POST', body: JSON.stringify({ declined_reason: reason }) }),
    getProfile: () => request<CrewProfileResponse>('/api/v1/portal/profile'),
    updateProfile: (data: { phone?: string | null; bio?: string | null }) => request<CrewProfileResponse>('/api/v1/portal/profile', { method: 'PATCH', body: JSON.stringify(data) }),
    setAvailability: (patterns: AvailabilityPatternCreate[]) => request<AvailabilityPatternResponse[]>('/api/v1/portal/availability', { method: 'PUT', body: JSON.stringify(patterns) }),
    getAvailability: () => request<AvailabilityPatternResponse[]>('/api/v1/portal/availability'),
  },
};

export { APIError };
