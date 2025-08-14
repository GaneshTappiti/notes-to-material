import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const roles = ['student', 'faculty', 'admin'];

export default function Signup() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('student');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      const res = await axios.post('/api/auth/register', { email, password, role });
      if (res.data && res.data.success) {
        setSuccess('Signup successful! Redirecting to login...');
        setTimeout(() => navigate('/login'), 2000);
      } else {
        setError(res.data?.message || 'Signup failed');
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Signup error');
    }
  };

  return (
    <div className="auth-form">
      <h2>Sign Up</h2>
      <form onSubmit={handleSubmit}>
        <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
        <select value={role} onChange={e => setRole(e.target.value)}>
          {roles.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <button type="submit">Sign Up</button>
      </form>
      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}
      <p>
        Already have an account? <a href="/login">Login</a>
      </p>
    </div>
  );
}
