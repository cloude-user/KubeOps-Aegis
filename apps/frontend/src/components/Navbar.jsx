import React from 'react';

export default function Navbar({ cartCount, user, onOpenCart, onOpenAuth, onOpenReceipt }) {
  return (
    <header className="navbar glass">
      <a href="#" className="brand-logo">
        <div className="brand-icon">⚡</div>
        <div>
          <div className="brand-title">Aegis <span className="gradient-text">Commerce</span></div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Azure AKS 3-Tier Enterprise</span>
        </div>
      </a>

      <div className="nav-actions">
        <button className="btn-icon-pill" onClick={onOpenReceipt}>
          📄 Upload Receipt
        </button>

        <button className="btn-icon-pill" onClick={onOpenCart}>
          🛒 Cart <span style={{ color: 'var(--accent-cyan)', fontWeight: 800 }}>({cartCount})</span>
        </button>

        {user ? (
          <div className="btn-icon-pill" style={{ borderColor: 'var(--accent-green)' }}>
            <span style={{ color: 'var(--accent-green)' }}>●</span> {user.full_name}
          </div>
        ) : (
          <button className="btn-icon-pill btn-primary" onClick={onOpenAuth}>
            🔑 Microsoft Entra ID
          </button>
        )}
      </div>
    </header>
  );
}
