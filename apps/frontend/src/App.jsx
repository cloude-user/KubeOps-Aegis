import React, { useState } from 'react';
import Navbar from './components/Navbar';
import HeroBanner from './components/HeroBanner';
import ProductCatalog from './components/ProductCatalog';
import CartDrawer from './components/CartDrawer';
import EntraAuthModal from './components/EntraAuthModal';
import ReceiptUploadModal from './components/ReceiptUploadModal';
import { API_BASE_URL } from './config';
import './App.css';

export default function App() {
  const [cart, setCart] = useState([]);
  const [user, setUser] = useState(null);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isReceiptOpen, setIsReceiptOpen] = useState(false);
  const [checkoutStatus, setCheckoutStatus] = useState(null);

  const handleAddToCart = (product) => {
    setCart(prevCart => {
      const existing = prevCart.find(item => item.id === product.id);
      if (existing) {
        return prevCart.map(item =>
          item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      }
      return [...prevCart, { ...product, quantity: 1 }];
    });
  };

  const handleCheckout = async () => {
    try {
      const orderPayload = {
        user_id: user ? user.id : "usr-guest-001",
        items: cart.map(item => ({
          product_id: item.id,
          quantity: item.quantity,
          unit_price: Number(item.price)
        })),
        shipping_address: "100 Cloud Architecture Blvd, Azure East Asia Region"
      };

      const res = await fetch(`${API_BASE_URL}/api/v1/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(orderPayload)
      });

      if (!res.ok) {
        throw new Error(`Checkout failed with status ${res.status}`);
      }

      const orderData = await res.json();
      setCart([]);
      setIsCartOpen(false);
      setCheckoutStatus(orderData);
    } catch (err) {
      console.error("Checkout error:", err);
      alert(`Checkout failed: ${err.message}. (Backend may be offline)`);
    }
  };

  return (
    <div>
      <div className="ambient-glow"></div>
      <div className="app-container">
        <Navbar 
          cartCount={cart.reduce((sum, item) => sum + item.quantity, 0)}
          user={user}
          onOpenCart={() => setIsCartOpen(true)}
          onOpenAuth={() => setIsAuthOpen(true)}
          onOpenReceipt={() => setIsReceiptOpen(true)}
        />

        {checkoutStatus && (
          <div style={{ margin: '20px auto', maxWidth: '800px', padding: '16px 20px', background: 'rgba(0, 230, 118, 0.1)', border: '1px solid rgba(0, 230, 118, 0.3)', borderRadius: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 800, color: 'var(--accent-green, #00e676)' }}>🎉 Order Confirmed: {checkoutStatus.id}</div>
              <div style={{ fontSize: '0.85rem', color: '#ccc', marginTop: '4px' }}>
                Total: <strong>${Number(checkoutStatus.total_amount).toFixed(2)}</strong> | Saved to PostgreSQL
              </div>
            </div>
            <button 
              onClick={() => setCheckoutStatus(null)} 
              style={{ background: 'none', border: 'none', color: '#fff', fontSize: '1.2rem', cursor: 'pointer' }}
            >
              &times;
            </button>
          </div>
        )}

        <main>
          <HeroBanner />
          <ProductCatalog onAddToCart={handleAddToCart} />
        </main>

        <CartDrawer 
          isOpen={isCartOpen}
          cart={cart}
          onClose={() => setIsCartOpen(false)}
          onCheckout={handleCheckout}
        />

        <EntraAuthModal 
          isOpen={isAuthOpen}
          onClose={() => setIsAuthOpen(false)}
          onLoginSuccess={(userData) => setUser(userData)}
        />

        <ReceiptUploadModal 
          isOpen={isReceiptOpen}
          onClose={() => setIsReceiptOpen(false)}
        />
      </div>
    </div>
  );
}
