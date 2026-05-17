// Enums
export type JobState = 'intake' | 'simmer' | 'active' | 'complete';
export type AssignmentState = 'pending' | 'confirmed' | 'declined';
export type EquipmentCondition = 'good' | 'fair' | 'poor' | 'maintenance';
export type TaskStatus = 'todo' | 'in_progress' | 'done';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';
export type UserRole = 'admin' | 'crew';
export type AvailabilityStatus = 'free' | 'booked' | 'unavailable';

// User
export interface User {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  timezone: string;
  created_at: string;
}

// Job
export interface CrewAssignmentSummary {
  id: string;
  crew_id: string;
  role: string | null;
  status: string;
}

export interface EquipmentAssignmentSummary {
  id: string;
  equipment_id: string;
  quantity_assigned: number;
}

export interface MessageSummary {
  id: string;
  user_id: string;
  content: string;
  created_at: string;
}

export interface TaskSummary {
  id: string;
  title: string;
  status: string;
  priority: string;
  assignee_id: string | null;
  deadline: string | null;
}

export interface FileSummary {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  created_at: string;
}

export interface CoordinationSummary {
  message_count: number;
  recent_messages: MessageSummary[];
  task_total: number;
  task_todo: number;
  task_in_progress: number;
  task_done: number;
  task_overdue: number;
  file_count: number;
  recent_files: FileSummary[];
}

export interface JobCreate {
  title: string;
  description?: string | null;
  venue?: string | null;
  scheduled_start?: string | null;
  scheduled_end?: string | null;
}

export interface JobUpdate {
  title?: string | null;
  description?: string | null;
  venue?: string | null;
  scheduled_start?: string | null;
  scheduled_end?: string | null;
}

export interface JobResponse {
  id: string;
  title: string;
  description: string | null;
  venue: string | null;
  scheduled_start: string | null;
  scheduled_end: string | null;
  state: JobState;
  created_at: string;
  updated_at: string;
  assigned_crew: CrewAssignmentSummary[];
  assigned_gear: EquipmentAssignmentSummary[];
  coordination: CoordinationSummary;
}

export interface JobTransitionRequest {
  new_state: JobState;
}

// Crew
export interface CrewProfileCreate {
  user_id: string;
  phone?: string | null;
  bio?: string | null;
  hourly_rate?: number | null;
  skills?: string[];
}

export interface CrewProfileUpdate {
  phone?: string | null;
  bio?: string | null;
  hourly_rate?: number | null;
  skills?: string[] | null;
}

export interface CrewProfileResponse {
  id: string;
  user_id: string;
  phone: string | null;
  bio: string | null;
  hourly_rate: number | null;
  skills: string[];
  archived_at: string | null;
  rating_average: number | null;
  rating_count: number;
  created_at: string;
  updated_at: string;
}

export interface AvailabilityPatternCreate {
  day_of_week: number;
  is_available: boolean;
}

export interface AvailabilityPatternResponse {
  id: string;
  crew_id: string;
  day_of_week: number;
  is_available: boolean;
}

export interface CrewRatingCreate {
  stars: number;
  notes?: string | null;
}

export interface CrewRatingResponse {
  id: string;
  crew_id: string;
  job_id: string;
  rated_by: string;
  stars: number;
  notes: string | null;
  created_at: string;
}

export interface SkillsMatrixEntry {
  id: string;
  email: string;
  skills: Record<string, boolean>;
}

export interface SkillsMatrixResponse {
  skills: string[];
  crew: SkillsMatrixEntry[];
}

// Equipment
export interface EquipmentCreate {
  name: string;
  category?: string | null;
  quantity?: number;
  condition?: EquipmentCondition;
  notes?: string | null;
  serial_number?: string | null;
}

export interface EquipmentUpdate {
  name?: string | null;
  category?: string | null;
  quantity?: number | null;
  condition?: EquipmentCondition | null;
  notes?: string | null;
  serial_number?: string | null;
}

export interface EquipmentResponse {
  id: string;
  name: string;
  category: string | null;
  quantity: number;
  condition: EquipmentCondition;
  notes: string | null;
  serial_number: string | null;
  created_at: string;
  updated_at: string;
}

// Assignments
export interface CrewAssignmentCreate {
  crew_id: string;
  job_id: string;
  role?: string | null;
  force?: boolean;
  override_reason?: string | null;
}

export interface CrewAssignmentResponse {
  id: string;
  crew_id: string;
  job_id: string;
  role: string | null;
  status: AssignmentState;
  override_reason: string | null;
  declined_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface EquipmentAssignmentCreate {
  equipment_id: string;
  job_id: string;
  quantity_assigned?: number;
}

export interface EquipmentAssignmentResponse {
  id: string;
  equipment_id: string;
  job_id: string;
  quantity_assigned: number;
  created_at: string;
  updated_at: string;
}

export interface ConflictDetail {
  job_id: string;
  job_title: string;
  scheduled_start: string | null;
  scheduled_end: string | null;
}

export interface ConflictWarning {
  message: string;
  conflicts: ConflictDetail[];
}

// Calendar
export interface CalendarEvent {
  id: string;
  event_type: string;
  title: string;
  start: string;
  end: string;
  color: string;
  status: string;
  job_id: string | null;
  resource_id: string | null;
  resource_name: string | null;
  job_title: string | null;
  role: string | null;
}

export interface CalendarEventsResponse {
  events: CalendarEvent[];
  count: number;
}

export interface AvailabilityDay {
  date: string;
  status: AvailabilityStatus;
}

export interface CrewAvailabilitySummary {
  crew_id: string;
  crew_name: string;
  days: AvailabilityDay[];
}

// Messages
export interface MessageCreate {
  content: string;
  reply_to_id?: string | null;
  file_ids?: string[];
}

export interface MessageResponse {
  id: string;
  job_id: string;
  user_id: string;
  content: string;
  reply_to_id: string | null;
  created_at: string;
  updated_at: string;
}

// Tasks
export interface TaskCreate {
  title: string;
  description?: string | null;
  assignee_id?: string | null;
  priority?: TaskPriority;
  deadline?: string | null;
  message_id?: string | null;
}

export interface TaskUpdate {
  title?: string | null;
  description?: string | null;
  assignee_id?: string | null;
  priority?: TaskPriority | null;
  deadline?: string | null;
}

export interface TaskResponse {
  id: string;
  job_id: string;
  title: string;
  description: string | null;
  assignee_id: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  deadline: string | null;
  message_id: string | null;
  created_at: string;
  updated_at: string;
}

// Files
export interface FileResponse {
  id: string;
  job_id: string;
  uploader_id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  created_at: string;
  updated_at: string;
}

// Notifications
export interface NotificationCounts {
  unread_messages: number;
  pending_assignments: number;
}

// Portal
export interface PortalAssignmentItem {
  assignment_id: string;
  job_id: string;
  job_title: string;
  job_venue: string | null;
  scheduled_start: string | null;
  scheduled_end: string | null;
  role: string | null;
  status: string;
}

export interface PortalDashboardResponse {
  upcoming: PortalAssignmentItem[];
  recent: PortalAssignmentItem[];
  counts: NotificationCounts;
}

export interface PortalFileItem {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  uploaded_at: string;
}

export interface PortalJobDetailResponse {
  id: string;
  title: string;
  description: string | null;
  venue: string | null;
  scheduled_start: string | null;
  scheduled_end: string | null;
  state: string;
  crew_role: string | null;
  assignment_status: string;
  files: PortalFileItem[];
}

export interface PortalAssignmentDetail {
  id: string;
  job_id: string;
  job_title: string;
  job_venue: string | null;
  scheduled_start: string | null;
  scheduled_end: string | null;
  role: string | null;
  status: string;
  created_at: string;
}

// Auth
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  company_name: string;
}

export interface InviteRequest {
  email: string;
  role: UserRole;
}

// API helpers
export interface ApiError {
  detail: string;
}

export interface ApiMessage {
  message: string;
}
