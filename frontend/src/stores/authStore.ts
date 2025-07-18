import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { UserProfile, UserPermissions, UserRole } from '../types';
import { TokenManager, authApi } from '../services/api';

interface AuthState {
  // State
  user: UserProfile | null;
  permissions: UserPermissions | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (employeeId: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  clearError: () => void;
  checkAuth: () => Promise<void>;
}

const defaultPermissions: UserPermissions = {
  can_view_all_users: false,
  can_create_users: false,
  can_update_users: false,
  can_delete_users: false,
  can_view_all_logs: false,
  can_create_logs: false,
  can_view_cameras: false,
  can_manage_cameras: false,
  can_view_live_feed: false,
  can_enroll_faces: false,
  can_delete_faces: false,
  can_view_dashboard: false,
  can_manage_system: false,
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: TokenManager.getUser(),
      permissions: null,
      isAuthenticated: TokenManager.isAuthenticated(),
      isLoading: false,
      error: null,

      // Actions
      login: async (employeeId: string, password: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await authApi.login({ employee_id: employeeId, password });
          
          // Store tokens
          TokenManager.setTokens(response);
          
          // Get permissions
          const permissionsResponse = await authApi.getPermissions();
          
          set({
            user: response.user,
            permissions: permissionsResponse.permissions,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          set({
            user: null,
            permissions: null,
            isAuthenticated: false,
            isLoading: false,
            error: error instanceof Error ? error.message : 'Login failed',
          });
          throw error;
        }
      },

      logout: () => {
        // Clear tokens
        TokenManager.clearTokens();
        
        // Clear state
        set({
          user: null,
          permissions: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
        
        // Call logout API (optional, for server-side cleanup)
        authApi.logout().catch(() => {
          // Ignore errors on logout
        });
      },

      refreshUser: async () => {
        if (!get().isAuthenticated) return;
        
        set({ isLoading: true, error: null });
        
        try {
          const [user, permissionsResponse] = await Promise.all([
            authApi.getCurrentUser(),
            authApi.getPermissions(),
          ]);
          
          set({
            user,
            permissions: permissionsResponse.permissions,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          // If user fetch fails, user might be logged out
          get().logout();
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Failed to refresh user data',
          });
        }
      },

      changePassword: async (currentPassword: string, newPassword: string) => {
        set({ isLoading: true, error: null });
        
        try {
          await authApi.changePassword({
            current_password: currentPassword,
            new_password: newPassword,
          });
          
          set({ isLoading: false, error: null });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Failed to change password',
          });
          throw error;
        }
      },

      clearError: () => {
        set({ error: null });
      },

      checkAuth: async () => {
        const token = TokenManager.getAccessToken();
        
        if (!token) {
          set({
            user: null,
            permissions: null,
            isAuthenticated: false,
          });
          return;
        }
        
        try {
          // Verify token and get fresh user data
          await authApi.verifyToken();
          await get().refreshUser();
        } catch (error) {
          // Token is invalid, logout
          get().logout();
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Selectors for easier access to specific parts of the state
export const useUser = () => useAuthStore((state) => state.user);
export const usePermissions = () => useAuthStore((state) => state.permissions);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useAuthLoading = () => useAuthStore((state) => state.isLoading);
export const useAuthError = () => useAuthStore((state) => state.error);

// Permission helpers
export const useHasPermission = (permission: keyof UserPermissions): boolean => {
  const permissions = usePermissions();
  return permissions?.[permission] ?? false;
};

export const useIsRole = (role: UserRole): boolean => {
  const user = useUser();
  return user?.role === role;
};

export const useIsAdmin = (): boolean => {
  const user = useUser();
  return user?.role === UserRole.ADMIN || user?.role === UserRole.SUPER_ADMIN;
};

export const useIsSuperAdmin = (): boolean => {
  const user = useUser();
  return user?.role === UserRole.SUPER_ADMIN;
};

export const useCanAccessUser = (employeeId: string): boolean => {
  const user = useUser();
  const isAdmin = useIsAdmin();
  const isSelf = user?.employee_id === employeeId;
  
  return isAdmin || isSelf;
};