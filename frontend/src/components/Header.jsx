import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function Header() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!isAuthenticated()) {
    return (
      <header className="header">
        <div className="header-content">
          <h1>Notes to Material</h1>
          <nav>
            <a href="/login">Login</a>
            <a href="/signup">Sign Up</a>
          </nav>
        </div>
      </header>
    );
  }

  return (
    <header className="header">
      <div className="header-content">
        <h1>Notes to Material</h1>
        <nav>
          <span>Welcome, {user?.email} ({user?.role})</span>
          <a href="/dashboard">Dashboard</a>
          <a href="/uploads">Uploads</a>
          <a href="/jobs">Jobs</a>
          {user?.role === 'admin' && <a href="/settings">Settings</a>}
          <button onClick={handleLogout}>Logout</button>
        </nav>
      </div>
    </header>
  );
}
