import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import {
  LoginRequest,
  TokenResponse,
  User,
  UserProfile,
  CreateUserRequest,
  UpdateUserRequest,
  PasswordChangeRequest,
  PaginatedResponse,
  UserFilters,
  Face,
  FaceEnrollmentResponse,
  Log,
  LogFilters,
  Camera,
  CreateCameraRequest,
  DashboardStats,
  EmployeePresenceStatus,
  AttendanceReport,
  UserPermissions,
  ErrorResponse,
  ApiResponse,
} from '../types';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';
const API_TIMEOUT = 30000; // 30 seconds

// Token management
class TokenManager {
  private static readonly ACCESS_TOKEN_KEY = 'access_token';
  private static readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private static readonly USER_KEY = 'user';

  static getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  static getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  static getUser(): UserProfile | null {
    const userJson = localStorage.getItem(this.USER_KEY);
    return userJson ? JSON.parse(userJson) : null;
  }

  static setTokens(response: TokenResponse): void {
    localStorage.setItem(this.ACCESS_TOKEN_KEY, response.access_token);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, response.refresh_token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(response.user));
  }

  static clearTokens(): void {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  static isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }
}

// Create axios instance
const createApiInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor for adding auth token
  instance.interceptors.request.use(
    (config) => {
      const token = TokenManager.getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor for handling token refresh
  instance.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as any;

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshToken = TokenManager.getRefreshToken();
          if (refreshToken) {
            const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
              refresh_token: refreshToken,
            });

            TokenManager.setTokens(response.data);
            
            // Retry original request with new token
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
            }
            
            return instance(originalRequest);
          }
        } catch (refreshError) {
          TokenManager.clearTokens();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );

  return instance;
};

// API instance
const api = createApiInstance();

// Error handler
const handleApiError = (error: AxiosError): never => {
  if (error.response?.data) {
    const errorData = error.response.data as ErrorResponse;
    throw new Error(errorData.message || 'An error occurred');
  }
  throw new Error(error.message || 'Network error');
};

// Generic API wrapper
const apiRequest = async <T>(request: Promise<AxiosResponse<T>>): Promise<T> => {
  try {
    const response = await request;
    return response.data;
  } catch (error) {
    handleApiError(error as AxiosError);
  }
};

// Authentication API
export const authApi = {
  login: (credentials: LoginRequest): Promise<TokenResponse> =>
    apiRequest(api.post('/auth/login', credentials)),

  logout: (): Promise<{ message: string }> =>
    apiRequest(api.post('/auth/logout')),

  refreshToken: (refreshToken: string): Promise<TokenResponse> =>
    apiRequest(api.post('/auth/refresh', { refresh_token: refreshToken })),

  getCurrentUser: (): Promise<UserProfile> =>
    apiRequest(api.get('/auth/me')),

  changePassword: (data: PasswordChangeRequest): Promise<{ message: string }> =>
    apiRequest(api.post('/auth/change-password', data)),

  verifyToken: (): Promise<{ valid: boolean; employee_id: string; role: string }> =>
    apiRequest(api.get('/auth/verify')),

  getPermissions: (): Promise<{ employee_id: string; role: string; permissions: UserPermissions }> =>
    apiRequest(api.get('/auth/permissions')),
};

// Users API
export const usersApi = {
  getUsers: (params: {
    page?: number;
    size?: number;
    search?: string;
    department?: string;
    role?: string;
    is_active?: boolean;
  }): Promise<PaginatedResponse<User>> =>
    apiRequest(api.get('/users/', { params })),

  createUser: (data: CreateUserRequest): Promise<User> =>
    apiRequest(api.post('/users/', data)),

  getUser: (employeeId: string): Promise<User> =>
    apiRequest(api.get(`/users/${employeeId}`)),

  updateUser: (employeeId: string, data: UpdateUserRequest): Promise<User> =>
    apiRequest(api.put(`/users/${employeeId}`, data)),

  deleteUser: (employeeId: string): Promise<{ message: string }> =>
    apiRequest(api.delete(`/users/${employeeId}`)),

  getUserSummary: (employeeId: string): Promise<{
    user: UserProfile;
    statistics: {
      face_count: number;
      total_logs: number;
      recent_logs_30d: number;
      last_checkin?: string;
      last_checkout?: string;
    };
  }> =>
    apiRequest(api.get(`/users/${employeeId}/summary`)),
};

// Faces API
export const facesApi = {
  getUserFaces: (employeeId: string): Promise<Face[]> =>
    apiRequest(api.get(`/faces/user/${employeeId}`)),

  enrollFace: (employeeId: string, files: File[]): Promise<FaceEnrollmentResponse> => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    return apiRequest(
      api.post(`/faces/enroll/${employeeId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    );
  },

  deleteFace: (faceId: number): Promise<{ message: string }> =>
    apiRequest(api.delete(`/faces/${faceId}`)),

  getFaceImage: (faceId: number): Promise<Blob> =>
    apiRequest(
      api.get(`/faces/${faceId}/image`, {
        responseType: 'blob',
      })
    ),

  detectFaces: (file: File): Promise<{
    faces: Array<{
      bbox: number[];
      quality_score: number;
      confidence: number;
    }>;
  }> => {
    const formData = new FormData();
    formData.append('file', file);
    return apiRequest(
      api.post('/faces/detect', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    );
  },
};

// Logs API
export const logsApi = {
  getLogs: (params: {
    page?: number;
    size?: number;
    employee_id?: string;
    event_type?: string;
    camera_id?: number;
    start_date?: string;
    end_date?: string;
  }): Promise<PaginatedResponse<Log>> =>
    apiRequest(api.get('/logs/', { params })),

  getUserLogs: (
    employeeId: string,
    params: {
      page?: number;
      size?: number;
      event_type?: string;
      start_date?: string;
      end_date?: string;
    }
  ): Promise<PaginatedResponse<Log>> =>
    apiRequest(api.get(`/logs/user/${employeeId}`, { params })),

  createLog: (data: {
    employee_id: string;
    event_type: string;
    camera_id: number;
    confidence_score?: number;
    metadata?: Record<string, any>;
  }): Promise<Log> =>
    apiRequest(api.post('/logs/', data)),

  getAttendanceReport: (params: {
    start_date: string;
    end_date: string;
    employee_id?: string;
  }): Promise<AttendanceReport[]> =>
    apiRequest(api.get('/logs/attendance-report', { params })),

  getPresenceStatus: (): Promise<EmployeePresenceStatus[]> =>
    apiRequest(api.get('/logs/presence-status')),
};

// Cameras API
export const camerasApi = {
  getCameras: (): Promise<Camera[]> =>
    apiRequest(api.get('/cameras/')),

  createCamera: (data: CreateCameraRequest): Promise<Camera> =>
    apiRequest(api.post('/cameras/', data)),

  getCamera: (cameraId: number): Promise<Camera> =>
    apiRequest(api.get(`/cameras/${cameraId}`)),

  updateCamera: (cameraId: number, data: Partial<CreateCameraRequest>): Promise<Camera> =>
    apiRequest(api.put(`/cameras/${cameraId}`, data)),

  deleteCamera: (cameraId: number): Promise<{ message: string }> =>
    apiRequest(api.delete(`/cameras/${cameraId}`)),

  getCameraStream: (cameraId: number): string =>
    `${API_BASE_URL}/cameras/${cameraId}/stream`,
};

// Dashboard API
export const dashboardApi = {
  getStats: (): Promise<DashboardStats> =>
    apiRequest(api.get('/dashboard/stats')),

  getRecentActivity: (limit?: number): Promise<Log[]> =>
    apiRequest(api.get('/dashboard/recent-activity', { params: { limit } })),

  getAttendanceTrends: (days: number = 30): Promise<Array<{
    date: string;
    check_ins: number;
    check_outs: number;
  }>> =>
    apiRequest(api.get('/dashboard/attendance-trends', { params: { days } })),

  getDepartmentStats: (): Promise<Array<{
    department: string;
    employee_count: number;
    active_count: number;
  }>> =>
    apiRequest(api.get('/dashboard/department-stats')),
};

// Health API
export const healthApi = {
  checkHealth: (): Promise<{
    status: string;
    timestamp: number;
    services: {
      database: boolean;
      face_recognition: boolean;
    };
  }> =>
    apiRequest(api.get('/health')),
};

// File upload utility
export const uploadFile = async (
  url: string,
  file: File,
  onProgress?: (progress: number) => void
): Promise<any> => {
  const formData = new FormData();
  formData.append('file', file);

  return apiRequest(
    api.post(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = (progressEvent.loaded / progressEvent.total) * 100;
          onProgress(progress);
        }
      },
    })
  );
};

// Export token manager and API instance for external use
export { TokenManager, api as apiInstance };

// Default export
const apiService = {
  auth: authApi,
  users: usersApi,
  faces: facesApi,
  logs: logsApi,
  cameras: camerasApi,
  dashboard: dashboardApi,
  health: healthApi,
  uploadFile,
};

export default apiService;