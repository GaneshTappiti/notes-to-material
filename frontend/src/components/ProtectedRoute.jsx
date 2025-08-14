import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function ProtectedRoute({ children, requiredRole = null }) {
  const { isAuthenticated, hasRole, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated()) {
    return <Navigate to="/login" />;
  }

  if (requiredRole && !hasRole(requiredRole)) {
    return <div>Access denied. You need {requiredRole} role to access this page.</div>;
  }

  return children;
}
