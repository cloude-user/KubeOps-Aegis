import React from 'react';

export default function HeroBanner() {
  return (
    <div className="hero-card glass">
      <div className="hero-content">
        <div className="badge-pill">
          <span>☁️ Azure Cloud Managed Infrastructure</span>
        </div>
        <h2>Enterprise 3-Tier E-Commerce Application</h2>
        <p>
          Running on Azure Kubernetes Service (AKS), connected to Azure Managed PostgreSQL Flexible Server & Azure Blob Storage. Monitored by Autonomous LangGraph SRE AI Agent.
        </p>
      </div>
    </div>
  );
}
