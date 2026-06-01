import React, { useState } from 'react';
import { supabase } from './supabaseClient';
import './index.css';

export default function Auth({ onLogin }) {
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState(null);

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      let data, authError;
      if (isRegister) {
        const res = await supabase.auth.signUp({ email, password });
        data = res.data; authError = res.error;
      } else {
        const res = await supabase.auth.signInWithPassword({ email, password });
        data = res.data; authError = res.error;
      }

      if (authError) throw authError;

      if (data.user) {
          const res = await fetch(`http://localhost:8000/users/sync`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email: data.user.email, auth_id: data.user.id })
          });
          const userData = await res.json();
          onLogin(userData.user_id); 
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card" style={{ maxWidth: '400px', margin: '4rem auto', textAlign: 'center' }}>
      <h2 style={{ marginBottom: '1.5rem', color: 'var(--accent)' }}>
        {isRegister ? 'Create an Account' : 'Welcome Back'}
      </h2>
      {error && <div style={{ color: '#fca5a5', marginBottom: '1rem', padding: '10px', background: 'rgba(239,68,68,0.1)', borderRadius: '8px' }}>{error}</div>}
      <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <input 
          type="email" 
          placeholder="Email" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{ padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.2)', color: 'white', fontFamily: 'inherit' }}
        />
        <input 
          type="password" 
          placeholder="Password" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)}
          required
          style={{ padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.2)', color: 'white', fontFamily: 'inherit' }}
        />
        <button className="btn" type="submit" disabled={loading}>
          {loading ? 'Processing...' : (isRegister ? 'Sign Up' : 'Log In')}
        </button>
      </form>
      <p style={{ marginTop: '1.5rem', color: 'var(--text-muted)' }}>
        {isRegister ? 'Already have an account? ' : "Don't have an account? "}
        <span style={{ color: 'var(--accent)', cursor: 'pointer', fontWeight: 'bold' }} onClick={() => setIsRegister(!isRegister)}>
          {isRegister ? 'Log In' : 'Sign Up'}
        </span>
      </p>
    </div>
  );
}
