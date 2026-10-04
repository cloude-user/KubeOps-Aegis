# 💻 Aegis E-Commerce & SRE Dashboard Frontend

> **Interactive Single Page Application (SPA) for Live Cluster Telemetry, Microservice Shopping, Microsoft Entra ID Authentication & Autonomous SRE Remediation**

---

## 📌 Features & Modules

1. **🔒 Microsoft Entra ID Authentication Modal**:
   * Enterprise OAuth2 Single Sign-On (SSO) login flow.

2. **📊 Real-time WebSocket Cluster Telemetry**:
   * Connects to `wss://<host>/ws/telemetry` to display live CPU utilization, memory pressure, active pod counts, and cluster health status.

3. **🚨 SRE Chaos Control Panel**:
   * One-click trigger buttons to inject **OOMKilled**, **PostgreSQL Query Timeout**, and **CPU Throttling** into the AKS cluster.

4. **🧠 LangGraph State Machine Visualizer**:
   * Step-by-step visual tracker showing agent progress (`Triage` -> `Diagnose` -> `Remediate` -> `ArgoCD GitOps`).

5. **📋 GitOps Pull Request & Human-in-the-Loop Approval**:
   * Displays manifest diffs and allows SRE leads to approve auto-remediation patches with one click.

---

## 🛠️ File Directory

* **`index.html`**: Semantic HTML5 dashboard layout with glassmorphism dark-mode UI.
* **`styles.css`**: Pure Vanilla CSS design system with custom HSL color tokens, responsive CSS Grid, and dynamic animations.
* **`app.js`**: Vanilla JavaScript controller handling WebSocket connections, REST API fetches, and DOM rendering.

---

## 🚀 How to Run

The frontend static assets are automatically served by the FastAPI backend at `http://localhost:8000/`.

To run standalone with any HTTP static web server:

```bash
# Using Python builtin HTTP server
cd web/
python -m http.server 3000
```

Open `http://localhost:3000` in your browser.
