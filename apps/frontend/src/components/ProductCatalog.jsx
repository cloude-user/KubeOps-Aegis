import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';

const FALLBACK_PRODUCTS = [
  {
    id: "prod-101",
    title: "Azure AKS Masterclass Handbook",
    category: "Cloud & DevOps",
    price: 49.99,
    description: "Production guide for Azure Kubernetes Service, Workload Identity & Azure CNI networking.",
    image_url: "https://images.unsplash.com/photo-1667372393119-3d4c48d07fc9?w=500&auto=format&fit=crop"
  },
  {
    id: "prod-102",
    title: "Terraform Enterprise IaC Guide",
    category: "Cloud & DevOps",
    price: 59.99,
    description: "Production-grade Terraform modules, Azure Blob state backend & OIDC automation.",
    image_url: "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=500&auto=format&fit=crop"
  },
  {
    id: "prod-103",
    title: "Autonomous SRE AI Agent Toolkit",
    category: "Cloud & DevOps",
    price: 89.99,
    description: "LangGraph StateGraph workflow engine for K8s self-healing & Prometheus alert triage.",
    image_url: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop"
  },
  {
    id: "prod-104",
    title: "Mechanical K8s Keycaps",
    category: "Developer Gear",
    price: 29.99,
    description: "Custom CNC anodized aluminum keycaps with Kubernetes & Azure helm icons.",
    image_url: "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=500&auto=format&fit=crop"
  }
];

export default function ProductCatalog({ onAddToCart }) {
  const [products, setProducts] = useState(FALLBACK_PRODUCTS);
  const [activeCategory, setActiveCategory] = useState("All");
  const [loading, setLoading] = useState(true);
  const [isLiveDB, setIsLiveDB] = useState(false);

  useEffect(() => {
    async function fetchProducts() {
      try {
        setLoading(true);
        const res = await fetch(`${API_BASE_URL}/api/v1/products`);
        if (res.ok) {
          const data = await res.json();
          if (data && data.length > 0) {
            setProducts(data);
            setIsLiveDB(true);
          }
        }
      } catch (err) {
        console.warn("Could not connect to live backend API, displaying fallback catalog:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchProducts();
  }, []);

  const categories = ["All", ...Array.from(new Set(products.map(p => p.category)))];

  const filteredProducts = activeCategory === "All"
    ? products
    : products.filter(p => p.category.toLowerCase() === activeCategory.toLowerCase());

  return (
    <section>
      <div className="section-header">
        <div>
          <h3 className="section-title">Featured Products</h3>
          <span style={{ fontSize: '0.8rem', color: isLiveDB ? 'var(--accent-green, #00e676)' : 'var(--text-muted)' }}>
            {isLiveDB ? '● Live Azure PostgreSQL Feed' : '○ Offline Mode'}
          </span>
        </div>
        <div className="category-tabs">
          {categories.map(cat => (
            <button
              key={cat}
              className={`tab-btn ${activeCategory === cat ? 'active' : ''}`}
              onClick={() => setActiveCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          Loading live catalog from Azure...
        </div>
      ) : (
        <div className="product-grid">
          {filteredProducts.map(product => (
            <div key={product.id} className="product-card glass">
              <img 
                src={product.image_url || "https://images.unsplash.com/photo-1667372393119-3d4c48d07fc9?w=500&auto=format&fit=crop"} 
                alt={product.title} 
                className="product-img" 
                onError={(e) => {
                  e.target.src = "https://images.unsplash.com/photo-1667372393119-3d4c48d07fc9?w=500&auto=format&fit=crop";
                }}
              />
              <div className="product-category">{product.category}</div>
              <h4 className="product-title">{product.title}</h4>
              <p className="product-desc">{product.description || "Enterprise cloud microservice component."}</p>
              <div className="product-footer">
                <span className="product-price">${Number(product.price).toFixed(2)}</span>
                <button 
                  className="btn-icon-pill btn-primary"
                  onClick={() => onAddToCart(product)}
                >
                  Add to Cart
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
