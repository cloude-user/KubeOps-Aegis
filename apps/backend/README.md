# 🛍️ Aegis E-Commerce 3-Tier Backend API

> **Enterprise FastAPI Microservice for Azure AKS with Microsoft Entra ID Authentication, Azure Managed PostgreSQL, Azure Blob Storage & SRE Chaos Simulation**

---

## 📌 Architecture Overview

The **Aegis E-Commerce Backend** is a cloud-native 3-tier microservice built for **Azure Kubernetes Service (AKS)**. It connects directly to managed Azure cloud infrastructure:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             CLIENT / FRONTEND UI                            │
│           Sends HTTP Requests with Microsoft Entra ID OAuth2 JWT            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FastAPI ASGI Application Server                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ 🔑 Microsoft Entra ID Auth ──► Validates JWT tokens against Azure AD  │  │
│  │ 📦 Product & Order Engine  ──► Manages catalog & cart checkout       │  │
│  │ 📄 Document Upload Engine ──► Uploads PDF receipts to Azure Blob      │  │
│  │ 💥 SRE Chaos Engine        ──► Simulates DB Query Timeout & OOM      │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
└──────────────────────────────────────┼──────────────────────────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
┌───────────────────────────────┐             ┌───────────────────────────────┐
│ Azure Managed PostgreSQL      │             │ Azure Blob Storage Container  │
│ (Users, Products, Orders DB)  │             │ (Customer Receipts & Images)  │
└───────────────────────────────┘             └───────────────────────────────┘
```

---

## 🔐 Authentication: Microsoft Entra ID (Azure AD) + Local OAuth2

This application supports enterprise **Microsoft Entra ID (OIDC)** authentication:

1. The Frontend UI prompts the user to log in via **Microsoft Entra ID**.
2. Entra ID returns an OpenID Connect `id_token` / `access_token` signed by Microsoft.
3. The Backend API validates the JWT token against Microsoft's public JWKS endpoint:
   `https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys`

---

## 🛠️ API Endpoint Directory

### 🔑 1. User Authentication (`/api/v1/auth`)
* `POST /api/v1/auth/register`: Register a new customer user profile.
* `POST /api/v1/auth/login`: Authenticate and issue a Bearer JWT access token.

### 📦 2. Product Catalog (`/api/v1/products`)
* `GET /api/v1/products`: List all catalog products (supports `?category=` filter and `?search=` query).
* `GET /api/v1/products/{id}`: Fetch detailed metadata for a single product.

### 🛒 3. Order Checkout (`/api/v1/orders`)
* `POST /api/v1/orders`: Process a new order checkout.
* `GET /api/v1/orders`: List order history for a customer.

### 📄 4. Document & Media Uploads (`/api/v1/uploads`)
* `POST /api/v1/uploads/receipt`: Upload payment receipt PDF/images directly to **Azure Blob Storage**.

### 💥 5. SRE Chaos & Failure Simulation (`/api/v1/chaos`)
* `GET /api/v1/chaos/db-query-timeout`: Simulates PostgreSQL connection pool deadlock & 15s Query Timeout (`504 Gateway Timeout`).
* `GET /api/v1/chaos/http-request-timeout`: Simulates downstream payment HTTP socket read timeout (`504 Gateway Timeout`).
* `POST /api/v1/chaos/oom-leak`: Allocates 150MB buffer chunks per request to trigger `OOMKilled` (exit code 137).
* `POST /api/v1/chaos/cpu-burn`: Executes prime number loops to trigger CPU Throttling & HPA scaling.

---

## 🚀 Quick Start: Local Running

```bash
# 1. Create and activate a Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the server
uvicorn apps.backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at `http://localhost:8000/docs`.

---

## 🐳 Docker Container Execution

```bash
# Build Docker image
docker build -f apps/backend/Dockerfile -t backend-api:v1.0.0 .

# Run container locally
docker run -p 8000:8000 backend-api:v1.0.0
```
