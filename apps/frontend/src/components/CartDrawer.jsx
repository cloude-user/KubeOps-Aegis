import React from 'react';

export default function CartDrawer({ isOpen, cart, onClose, onCheckout }) {
  if (!isOpen) return null;

  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card glass" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="section-title">🛒 Shopping Cart</h3>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>

        {cart.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text-muted)' }}>
            Your cart is empty. Add products from the catalog.
          </div>
        ) : (
          <div>
            <div style={{ maxHeight: '250px', overflowY: 'auto', marginBottom: '20px' }}>
              {cart.map(item => (
                <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border-glass)' }}>
                  <div>
                    <div style={{ fontWeight: 700 }}>{item.title}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>${item.price} x {item.quantity}</div>
                  </div>
                  <div style={{ fontWeight: 800, color: 'var(--accent-cyan)' }}>${(item.price * item.quantity).toFixed(2)}</div>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.2rem', fontWeight: 800, marginBottom: '20px' }}>
              <span>Total:</span>
              <span className="gradient-text">${total.toFixed(2)}</span>
            </div>

            <button className="btn-icon-pill btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '14px' }} onClick={onCheckout}>
              ⚡ Checkout & Generate Receipt
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
