import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

/**
 * ProtectedLayout ensures child routes are only accessible to authenticated users.
 * Unauthenticated users are redirected to /login with original location stored in state.
 */
export const ProtectedLayout: React.FC = () => {
  const { isAuthenticated, isLoggingOut } = useAuthStore();
  const location = useLocation();

  if (isLoggingOut) {
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
};
