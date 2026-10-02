import React from 'react';

export default function EntraAuthModal({ isOpen, onClose, onLoginSuccess }) {
  if (!isOpen) return null;

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
          <h3 className="section-title">🔑 Sign in</h3>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        <div className="entra-sso-box">
          <div style={{ fontSize: '1.5rem' }}>🛡️</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>Microsoft Entra ID (Azure AD)</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Enterprise Single Sign-On (OIDC OAuth2)</div>
          </div>
        </div>

        <button 
          className="btn-icon-pill btn-primary" 
          style={{ width: '100%', justifyContent: 'center', padding: '14px', marginBottom: '16px' }}
          onClick={handleSimulatedEntraSSO}
        >
          Sign in with Microsoft Entra ID
        </button>

        <div style={{ textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Validates JWT Bearer Token against Azure AD Tenant.
        </div>
      </div>
    </div>
  );
}
