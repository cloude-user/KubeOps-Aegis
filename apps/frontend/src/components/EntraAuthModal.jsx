import React, { useState } from 'react';
import { API_BASE_URL } from '../config';

export default function EntraAuthModal({ isOpen, onClose, onLoginSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    const endpoint = isRegister ? '/api/v1/auth/register' : '/api/v1/auth/login';
    const body = isRegister 
      ? { email, password, full_name: fullName }
      : { email, password };

    try {
      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      const userProfile = data.user || data;
      onLoginSuccess(userProfile);
      onClose();
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulatedEntraSSO = () => {
    onLoginSuccess({
      id: "entra-oid-admin-001",
      email: "sre-admin@aegiscloud.onmicrosoft.com",
      full_name: "SRE Lead Architect",
      role: "sre_admin"
    });
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card glass" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="section-title">🔑 {isRegister ? "Create Customer Account" : "Customer Sign In"}</h3>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        {errorMsg && (
          <div style={{ padding: '8px 12px', marginBottom: '14px', background: 'rgba(255, 77, 77, 0.1)', border: '1px solid rgba(255, 77, 77, 0.3)', borderRadius: '6px', color: '#ff6b6b', fontSize: '0.85rem' }}>
            ⚠️ {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {isRegister && (
            <div className="form-group" style={{ marginBottom: '12px' }}>
              <label className="form-label" style={{ display: 'block', marginBottom: '4px', fontSize: '0.85rem' }}>Full Name:</label>
              <input 
                type="text" 
                required 
                className="form-input" 
                placeholder="Jane Doe" 
                value={fullName} 
                onChange={e => setFullName(e.target.value)} 
                style={{ width: '100%', padding: '10px', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', color: '#fff', border: '1px solid var(--border-glass, rgba(255,255,255,0.1))' }}
              />
            </div>
          )}

          <div className="form-group" style={{ marginBottom: '12px' }}>
            <label className="form-label" style={{ display: 'block', marginBottom: '4px', fontSize: '0.85rem' }}>Email Address:</label>
            <input 
              type="email" 
              required 
              className="form-input" 
              placeholder="user@example.com" 
              value={email} 
              onChange={e => setEmail(e.target.value)} 
              style={{ width: '100%', padding: '10px', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', color: '#fff', border: '1px solid var(--border-glass, rgba(255,255,255,0.1))' }}
            />
          </div>

          <div className="form-group" style={{ marginBottom: '16px' }}>
            <label className="form-label" style={{ display: 'block', marginBottom: '4px', fontSize: '0.85rem' }}>Password:</label>
            <input 
              type="password" 
              required 
              className="form-input" 
              placeholder="••••••••" 
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              style={{ width: '100%', padding: '10px', borderRadius: '6px', background: 'rgba(255,255,255,0.05)', color: '#fff', border: '1px solid var(--border-glass, rgba(255,255,255,0.1))' }}
            />
          </div>

          <button 
            type="submit" 
            className="btn-icon-pill btn-primary" 
            style={{ width: '100%', justifyContent: 'center', padding: '12px', marginBottom: '12px' }}
            disabled={loading}
          >
            {loading ? "Processing..." : (isRegister ? "Register & Save to PostgreSQL" : "Sign In")}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginBottom: '16px', fontSize: '0.85rem' }}>
          <button 
            type="button"
            onClick={() => { setIsRegister(!isRegister); setErrorMsg(null); }}
            style={{ background: 'none', border: 'none', color: 'var(--accent-cyan, #00e5ff)', cursor: 'pointer', textDecoration: 'underline' }}
          >
            {isRegister ? "Already have an account? Sign In" : "Need an account? Register here"}
          </button>
        </div>

        <div style={{ textAlign: 'center', margin: '14px 0', borderTop: '1px solid rgba(255,255,255,0.1)', position: 'relative' }}>
          <span style={{ position: 'relative', top: '-10px', background: '#111827', padding: '0 10px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>OR</span>
        </div>

        <button 
          type="button"
          className="btn-icon-pill" 
          style={{ width: '100%', justifyContent: 'center', padding: '12px', background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff' }}
          onClick={handleSimulatedEntraSSO}
        >
          🛡️ Fast 1-Click Azure Entra ID SSO
        </button>
      </div>
    </div>
  );
}
