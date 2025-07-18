import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuthStore, useIsAuthenticated } from './stores/authStore';
import LoadingSpinner from './components/ui/LoadingSpinner';
import ErrorBoundary from './components/ui/ErrorBoundary';
import NotificationContainer from './components/ui/NotificationContainer';

// Layout components
import AuthLayout from './components/layout/AuthLayout';
import DashboardLayout from './components/layout/DashboardLayout';

// Auth pages
import LoginPage from './pages/auth/LoginPage';

// Dashboard pages
import DashboardPage from './pages/dashboard/DashboardPage';
import UsersPage from './pages/users/UsersPage';
import UserDetailPage from './pages/users/UserDetailPage';
import CreateUserPage from './pages/users/CreateUserPage';
import ProfilePage from './pages/profile/ProfilePage';
import FacesPage from './pages/faces/FacesPage';
import LogsPage from './pages/logs/LogsPage';
import CamerasPage from './pages/cameras/CamerasPage';
import LiveFeedPage from './pages/live/LiveFeedPage';

// Error pages
import NotFoundPage from './pages/error/NotFoundPage';
import UnauthorizedPage from './pages/error/UnauthorizedPage';

import './App.css';

// Route guard component
interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  requireRole?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAuth = true,
  requireRole,
}) => {
  const isAuthenticated = useIsAuthenticated();
  const user = useAuthStore((state) => state.user);
  const location = useLocation();

  // If authentication is required and user is not authenticated
  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If specific roles are required
  if (requireRole && user && !requireRole.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
};

// Auth guard component
const AuthGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useIsAuthenticated();
  const location = useLocation();

  // If user is authenticated and trying to access auth pages, redirect to dashboard
  if (isAuthenticated && location.pathname.startsWith('/login')) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// App initialization component
const AppInitializer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const checkAuth = useAuthStore((state) => state.checkAuth);
  const isLoading = useAuthStore((state) => state.isLoading);
  const [isInitialized, setIsInitialized] = React.useState(false);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        await checkAuth();
      } catch (error) {
        console.error('Auth initialization failed:', error);
      } finally {
        setIsInitialized(true);
      }
    };

    initializeAuth();
  }, [checkAuth]);

  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <Router>
        <AppInitializer>
          <div className="App min-h-screen bg-gray-50">
            <Routes>
              {/* Public routes */}
              <Route
                path="/login"
                element={
                  <AuthGuard>
                    <AuthLayout>
                      <LoginPage />
                    </AuthLayout>
                  </AuthGuard>
                }
              />

              {/* Protected routes */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <DashboardLayout>
                      <DashboardPage />
                    </DashboardLayout>
                  </ProtectedRoute>
                }
              />

              {/* User management routes */}
              <Route
                path="/users"
                element={
                  <ProtectedRoute requireRole={['admin', 'super_admin']}>
                    <DashboardLayout>
                      <UsersPage />
                    </DashboardLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/users/create"
                element={
                  <ProtectedRoute requireRole={['admin', 'super_admin']}>
                    <DashboardLayout>
                      <CreateUserPage />
                    </DashboardLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path="/users/:employeeId"
                element={
                  <ProtectedRoute>
                    <DashboardLayout>
                      <UserDetailPage />
                    </DashboardLayout>
                  </ProtectedRoute>
                }
              />

              {/* Profile route */}
              <Route
                path="/profile"
                element={
                  <ProtectedRoute>
                    <DashboardLayout>
                      <ProfilePage />
                    </DashboardLayout>
                  </ProtectedRoute>
                }
              />

              {/* Face management routes */}
              <Route
                path="/faces"
                element={
                  <ProtectedRoute requireRole={['admin', 'super_admin']}>
                    <DashboardLayout>
                      <FacesPage />
                    </DashboardLayout>
                  </ProtectedRoute>
                }
              />

              {/* Logs routes */}
              <Route
                path="/logs"
                element={
                  <ProtectedRoute>
                    <DashboardLayout>
                      <LogsPage />
                    </DashboardLayout>
                  </ProtectedRoute>
                }
              />

              {/* Camera management routes */}
              <Route
                path="/cameras"
                element={
                  <ProtectedRoute requireRole={['admin', 'super_admin']}>
                    <DashboardLayout>
                      <CamerasPage />
                    </DashboardLayout>
                  </ProtectedRoute>
                }
              />

              {/* Live feed routes */}
              <Route
                path="/live"
                element={
                  <ProtectedRoute requireRole={['admin', 'super_admin']}>
                    <DashboardLayout>
                      <LiveFeedPage />
                    </DashboardLayout>
                  </ProtectedRoute>
                }
              />

              {/* Error routes */}
              <Route path="/unauthorized" element={<UnauthorizedPage />} />
              <Route path="/404" element={<NotFoundPage />} />

              {/* Root redirect */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />

              {/* Catch all route */}
              <Route path="*" element={<Navigate to="/404" replace />} />
            </Routes>

            {/* Global notification container */}
            <NotificationContainer />
          </div>
        </AppInitializer>
      </Router>
    </ErrorBoundary>
  );
};

export default App;