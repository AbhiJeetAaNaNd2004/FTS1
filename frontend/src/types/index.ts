// User types
export enum UserRole {
  EMPLOYEE = "employee",
  ADMIN = "admin",
  SUPER_ADMIN = "super_admin",
}

export interface User {
  employee_id: string;
  name: string;
  email?: string;
  department?: string;
  designation?: string;
  phone?: string;
  role: UserRole;
  is_active: boolean;
  last_login_time?: string;
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  employee_id: string;
  name: string;
  email?: string;
  department?: string;
  designation?: string;
  phone?: string;
  role: UserRole;
  last_login_time?: string;
  created_at: string;
}

export interface CreateUserRequest {
  employee_id: string;
  name: string;
  password: string;
  email?: string;
  department?: string;
  designation?: string;
  phone?: string;
  role: UserRole;
  is_active: boolean;
}

export interface UpdateUserRequest {
  name?: string;
  email?: string;
  department?: string;
  designation?: string;
  phone?: string;
  role?: UserRole;
  is_active?: boolean;
  password?: string;
}

// Authentication types
export interface LoginRequest {
  employee_id: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

// Face types
export enum EventType {
  CHECK_IN = "check-in",
  CHECK_OUT = "check-out",
}

export interface Face {
  id: number;
  employee_id: string;
  image_path: string;
  quality_score?: number;
  created_at: string;
}

export interface FaceEnrollmentResponse {
  success: boolean;
  message: string;
  face_count: number;
  quality_scores: number[];
  faces: Face[];
}

// Log types
export interface Log {
  id: number;
  employee_id: string;
  timestamp: string;
  event_type: EventType;
  camera_id: number;
  confidence_score?: number;
  metadata?: Record<string, any>;
  user?: UserProfile;
}

// Camera types
export enum CameraType {
  ENTRY = "entry",
  EXIT = "exit",
  MONITORING = "monitoring",
}

export interface Camera {
  id: number;
  location: string;
  stream_url?: string;
  camera_type: CameraType;
  resolution_width: number;
  resolution_height: number;
  fps: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateCameraRequest {
  location: string;
  stream_url?: string;
  camera_type: CameraType;
  resolution_width: number;
  resolution_height: number;
  fps: number;
  is_active: boolean;
}

// Dashboard types
export interface DashboardStats {
  total_employees: number;
  active_employees: number;
  total_faces_enrolled: number;
  total_logs_today: number;
  check_ins_today: number;
  check_outs_today: number;
  active_cameras: number;
}

export interface EmployeePresenceStatus {
  employee_id: string;
  name: string;
  status: "checked-in" | "checked-out" | "unknown";
  last_event_time?: string;
  last_event_type?: EventType;
}

export interface AttendanceReport {
  employee_id: string;
  name: string;
  date: string;
  check_in_time?: string;
  check_out_time?: string;
  total_hours?: number;
  status: "present" | "absent" | "partial";
}

// Pagination types
export interface PaginationParams {
  page: number;
  size: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// WebSocket types
export interface WebSocketMessage {
  type: string;
  data: Record<string, any>;
  timestamp: string;
}

export interface LiveDetectionEvent {
  employee_id: string;
  name: string;
  event_type: EventType;
  camera_id: number;
  camera_location: string;
  confidence_score: number;
  timestamp: string;
  image_data?: string;
}

// Error types
export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, any>;
}

export interface ValidationError {
  field: string;
  message: string;
  type: string;
}

export interface ValidationErrorResponse {
  error: string;
  message: string;
  details: ValidationError[];
}

// Permission types
export interface UserPermissions {
  can_view_all_users: boolean;
  can_create_users: boolean;
  can_update_users: boolean;
  can_delete_users: boolean;
  can_view_all_logs: boolean;
  can_create_logs: boolean;
  can_view_cameras: boolean;
  can_manage_cameras: boolean;
  can_view_live_feed: boolean;
  can_enroll_faces: boolean;
  can_delete_faces: boolean;
  can_view_dashboard: boolean;
  can_manage_system: boolean;
}

// Filter types
export interface UserFilters {
  search?: string;
  department?: string;
  role?: UserRole;
  is_active?: boolean;
}

export interface LogFilters {
  employee_id?: string;
  event_type?: EventType;
  camera_id?: number;
  start_date?: string;
  end_date?: string;
}

// API Response types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
}

// Form types
export interface FormField {
  name: string;
  label: string;
  type: "text" | "email" | "password" | "select" | "checkbox" | "file";
  required?: boolean;
  options?: { value: string; label: string }[];
  placeholder?: string;
  validation?: {
    minLength?: number;
    maxLength?: number;
    pattern?: string;
  };
}

// UI State types
export interface NotificationState {
  id: string;
  type: "success" | "error" | "warning" | "info";
  title: string;
  message: string;
  duration?: number;
}

export interface LoadingState {
  [key: string]: boolean;
}

// Chart data types
export interface ChartDataPoint {
  name: string;
  value: number;
  label?: string;
}

export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

// Modal types
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
}

// Table types
export interface TableColumn<T> {
  key: keyof T | string;
  label: string;
  sortable?: boolean;
  render?: (value: any, item: T) => React.ReactNode;
  width?: string;
}

export interface TableProps<T> {
  data: T[];
  columns: TableColumn<T>[];
  loading?: boolean;
  pagination?: PaginationParams;
  onPageChange?: (page: number) => void;
  onSort?: (column: string, direction: "asc" | "desc") => void;
}

// File upload types
export interface FileUploadProps {
  accept?: string;
  multiple?: boolean;
  maxSize?: number;
  onUpload: (files: File[]) => void;
  preview?: boolean;
}

export interface UploadedFile {
  file: File;
  preview?: string;
  status: "pending" | "uploading" | "success" | "error";
  progress?: number;
  error?: string;
}