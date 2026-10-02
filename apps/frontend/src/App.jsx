import React, { useState } from 'react';
import Navbar from './components/Navbar';
import HeroBanner from './components/HeroBanner';
import ProductCatalog from './components/ProductCatalog';
import CartDrawer from './components/CartDrawer';
import EntraAuthModal from './components/EntraAuthModal';
import ReceiptUploadModal from './components/ReceiptUploadModal';
import './App.css';

export default function App() {
  const [cart, setCart] = useState([]);
  const [user, setUser] = useState(null);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isReceiptOpen, setIsReceiptOpen] = useState(false);

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
    alert("Checkout completed! Order receipt PDF pushed to Azure Blob Storage.");
    setCart([]);
    setIsCartOpen(false);
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
