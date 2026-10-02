import React, { useState } from 'react';

const INITIAL_PRODUCTS = [
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
  const [activeCategory, setActiveCategory] = useState("All");

  const filteredProducts = activeCategory === "All"
    ? INITIAL_PRODUCTS
    : INITIAL_PRODUCTS.filter(p => p.category === activeCategory);

  return (
    <section>
      <div className="section-header">
        <h3 className="section-title">Featured Products</h3>
        <div className="category-tabs">
          {["All", "Cloud & DevOps", "Developer Gear"].map(cat => (
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

      <div className="products-grid">
        {filteredProducts.map(product => (
          <div key={product.id} className="product-card glass">
            <img src={product.image_url} alt={product.title} className="product-img" />
            <div>
              <h4 className="product-title">{product.title}</h4>
              <p className="product-desc">{product.description}</p>
            </div>
            <div className="product-footer">
              <span className="product-price">${product.price.toFixed(2)}</span>
              <button className="btn-icon-pill btn-primary" onClick={() => onAddToCart(product)}>
                + Add to Cart
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
