# KubeOps-Aegis: Enterprise Kubernetes Manifests & Cloud Networking Master Architecture Guide

**Author:** SRE & Cloud Engineering Team  
**Target Environment:** Azure AKS Production (`aks-kubeops-aegis-prd`)  
**Region:** Azure East Asia (`eastasia`)  
**Network Architecture:** Azure CNI Overlay + Cilium eBPF Data Plane + Azure NAT Gateway  
**Active Workload Namespace:** `aegis-apps`  
**Git Branch:** `main`  

---

## 1. Executive Master Architecture Diagram

```
═════════════════════════════════════════════════════════════════════════════════════════════════════════
                                            PUBLIC INTERNET
═════════════════════════════════════════════════════════════════════════════════════════════════════════
                                                   │
                  ┌────────────────────────────────┴────────────────────────────────┐
                  │ INBOUND TRAFFIC (Users / Browsers)                              │ OUTBOUND TRAFFIC
                  ▼ (TCP 80 / 443)                                                  ▲ (Docker pull, APIs)
  ┌──────────────────────────────────────────────┐                ┌─────────────────┴─────────────────┐
  │         Azure Public Load Balancer           │                │         Azure NAT Gateway         │
  │         (Public IPv4: 20.x.x.x)              │                │      (Dedicated Outbound IP)      │
  └───────────────────────┬──────────────────────┘                └─────────────────▲─────────────────┘
                          │ DNAT to NodePort (TCP 30000-32767)                      │ Outbound SNAT
                          │ Forwarded to Node Private IP                            │ Egress path
══════════════════════════╪═════════════════════════════════════════════════════════╪═════════════════════
  Azure Virtual Network (VNet): 10.100.0.0/16 Boundary (STRICTLY PRIVATE - ZERO DIRECT INTERNET INGRESS)
══════════════════════════╪═════════════════════════════════════════════════════════╪═════════════════════
                          ▼                                                         │
  ┌─────────────────────────────────────────────────────────────────────────────────┴───────────────────┐
  │ SUBNET 1: snet-aks-system (10.100.1.0/24) [ACTIVE]                                                  │
  │                                                                                                     │
  │  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐  │
  │  │ AKS Host Virtual Machine (Node Private IP: 10.100.1.4)                                         │  │
  │  │                                                                                               │  │
  │  │  ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │  │
  │  │  │ Linux Kernel: Cilium eBPF Socket & TC Layer (Replaces kube-proxy iptables)              │  │  │
  │  │  │  - Intercepts incoming NodePort TCP packets                                             │  │  │
  │  │  │  - Performs O(1) in-kernel DNAT lookup using BPF map (cilium_lb4_backends_v2)           │  │  │
  │  │  └─────────────────────────────────┬───────────────────────────────────────────────────────┘  │  │
  │  │                                    │                                                          │  │
  │  │  ┌─────────────────────────────────┴───────────────────────────────────────────────────────┐  │  │
  │  │  │ Pod Overlay Network: 10.244.0.0/16 (Virtual Container IPs - Zero VNet IP Exhaustion)   │  │  │
  │  │  │                                                                                         │  │  │
  │  │  │  [ Ingress Controller / Frontend Pod ] 10.244.0.12 (Port 80)                           │  │  │
  │  │  │   ├── React 18 Production Single Page Application                                       │  │  │
  │  │  │   └── Nginx Reverse Proxy (routes /api/* to http://backend-service:80)                  │  │  │
  │  │  │                                                                                         │  │  │
  │  │  │                                   │ Cilium eBPF Service Translation                     │  │  │
  │  │  │                                   │ Virtual IP: 10.0.x.x:80 -> Pod IP: 10.244.0.18:8000 │  │  │
  │  │  │                                   ▼                                                     │  │  │
  │  │  │  [ Backend FastAPI API Pod ] 10.244.0.18 (Port 8000)                                   │  │  │
  │  │  │   ├── Lifespan Singleton asyncpg Connection Pool                                        │  │  │
  │  │  │   ├── Pure SQL Data Layer (Zero ORM overhead)                                           │  │  │
  │  │  │   └── Prometheus RED Metrics & X-Request-ID Middleware                                  │  │  │
  │  │  │                                                                                         │  │  │
  │  │  │  [ Autonomous SRE AI Agent Pod ] 10.244.0.22 (Port 8000)                                │  │  │
  │  │  │   ├── Azure Workload Identity (Token exchange with Entra ID)                            │  │  │
  │  │  │   └── Continuous Prometheus Health Scraping & Incident Log Archival                    │  │  │
  │  │  └─────────────────────────────────┬───────────────────────────────────────────────────────┘  │  │
  │  └────────────────────────────────────┼──────────────────────────────────────────────────────────┘  │
  └───────────────────────────────────────┼─────────────────────────────────────────────────────────────┘
                                          │ Private VNet routing
                                          │ Source IP: 10.100.1.4 (Node VM SNAT)
                                          │ Destination IP: 10.100.3.4:5432
                                          ▼
  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ SUBNET 3: snet-database (10.100.3.0/24) [ACTIVE - DELEGATED TO POSTGRESQL]                         │
  │                                                                                                     │
  │  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐  │
  │  │ Network Security Group (nsg-database) Firewall Rules:                                         │  │
  │  │  - Rule 100: AllowPostgreSQLFromAKS (Source: 10.100.1.0/24, Port: 5432)   -> PERMIT           │  │
  │  │  - Rule 101: AllowPostgreSQLFromUserPool (Source: 10.100.2.0/24, Port: 5432) -> PERMIT           │  │
  │  │  - Rule 4096: DenyAllInbound (Source: *, Port: *)                        -> DROP & LOG        │  │
  │  └────────────────────────────────────┬───────────────────────────────────────────────────────────┘  │
  │                                       ▼                                                             │
  │  ┌───────────────────────────────────────────────────────────────────────────────────────────────┐  │
  │  │ Azure Database for PostgreSQL Flexible Server (kubeops-aegis-psql-prd)                        │  │
  │  │ Private Virtual IP: 10.100.3.4 : Port 5432 (ZERO PUBLIC ACCESS)                               │  │
  │  └───────────────────────────────────────────────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          │ Internal Azure Backbone (Zero Public Internet)
                                          ▼
  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │ SUBNET 5: snet-private-endpoints (10.100.5.0/24) [ACTIVE - PAAS PRIVATE LINK]                       │
  │                                                                                                     │
  │  - Azure Blob Storage Private Endpoint: kubeopsaegisstprd.privatelink.blob.core.windows.net        │
  │  - Azure Key Vault Private Endpoint:   kubeops-aegis-kv-prd.privatelink.vaultcore.azure.net         │
  │  - Azure Container Registry Endpoint:  kubeopsaegisacrprd.privatelink.azurecr.io                   │
  └─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Complete Subnet Inventory & Pod Placement Matrix

| Subnet Name | CIDR Block | Usage State | Host Physical Resources | Overlay Pods Running Inside | Public Access Allowed? | Isolation Security Controls |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`snet-aks-system`** | `10.100.1.0/24` | **ACTIVE** | AKS Node VM (`10.100.1.4`) | • `backend-api` (x2 pods)<br>• `frontend-ui` (x2 pods)<br>• `kubeops-aegis-agent` (x1 pod)<br>• Ingress Controller<br>• CoreDNS, Cilium, ArgoCD | **NO Direct Public Access.** Inbound only via Azure Load Balancer. Outbound via NAT Gateway. | Host VM NIC has no public IP. Accepts traffic only on high NodePorts dispatched by Azure Load Balancer. |
| **`snet-aks-user`** | `10.100.2.0/24` | *RESERVED* | Future User VM pool | None (Disabled via `deploy_user_node_pool = false` to save ~₹8,855/mo) | **NO.** | Reserved for enterprise horizontal scale-out. |
| **`snet-database`** | `10.100.3.0/24` | **ACTIVE** | PostgreSQL Flexible Server | None (Delegated to Azure PaaS database service) | **ZERO PUBLIC ACCESS.** Port 443 blocked. Port 5432 blocked to internet. | Delegated subnet + NSG `nsg-database`. Priority 100 permits TCP 5432 only from AKS node subnets. Rule 4096 drops all other inbound traffic. |
| **`snet-neo4j`** | `10.100.4.0/24` | *RESERVED* | Graph DB VM | None (Disabled via `deploy_neo4j = false` to avoid idle charges) | **NO.** | Fully private subnet. |
| **`snet-private-endpoints`** | `10.100.5.0/24` | **ACTIVE** | Private Link NICs | None (Hardware NICs for Blob Storage, Key Vault, ACR) | **NO PUBLIC ACCESS.** | NSG `nsg-private-endpoints` allows HTTPS (443) strictly from inside the VNet (`10.100.0.0/16`). Public internet drops. |
| **`snet-ingress`** | `10.100.6.0/24` | *RESERVED* | Azure Application Gateway / ALB (if using AGIC) | None (Reserved for App Gateway WAF instances) | **YES (Port 80/443 only).** | DMZ subnet terminating public SSL/TLS before forwarding to private AKS overlay. |

---

## 3. Why Pods Have `10.244.x.x` IPs While the Node Has `10.100.1.4` (Azure CNI Overlay)

Traditional **Azure CNI (Flat VNet Mode)** assigned a real private IP from `10.100.1.0/24` to *every single pod*. 
* **The Problem:** In a `/24` subnet with 251 usable IPs, if you deploy 2 nodes with 110 pods each, you burn 220 IPs and **exhaust the subnet immediately**.
* **The Solution (Azure CNI Overlay):**
  1. The node VM takes **just 1 real IP** from Azure VNet: `10.100.1.4`.
  2. Kubernetes assigns an internal **Overlay Pod CIDR (`10.244.0.0/16`)**.
  3. Pods receive virtual IPs: `10.244.0.12`, `10.244.0.18`, etc.
  4. When a pod talks to Azure PostgreSQL (`10.100.3.4`), the Linux kernel on node `10.100.1.4` automatically performs **SNAT (Source Network Address Translation)**, rewriting the source IP from `10.244.0.18` to `10.100.1.4`.
  5. The PostgreSQL Flexible Server sees a secure connection originating directly from the authorized AKS node subnet (`10.100.1.0/24`)!

---

## 4. Kubernetes Manifest-by-Manifest Specification

All workloads are consolidated inside [`k8s/workloads/`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/k8s/workloads/) and managed via ArgoCD GitOps:

### Manifest 1: [`00-namespace.yaml`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/k8s/workloads/00-namespace.yaml)
* **Namespace:** `aegis-apps`
* **Purpose:** Provides enterprise multi-tenant boundary, RBAC scoping, and isolated DNS discovery.

### Manifest 2: [`01-backend.yaml`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/k8s/workloads/01-backend.yaml)
* **Replicas:** 2 (High Availability)
* **Container Image:** `kubeopsaegisacrprd.azurecr.io/backend-api:latest`
* **Database Connection:** Connects via private VNet DNS to `kubeops-aegis-psql-prd.postgres.database.azure.com:5432/orderdb`
* **Health Probes:**
  * Liveness Probe: `GET /healthz` every 10s (restarts crashed pods).
  * Readiness Probe: `GET /healthz` every 5s (removes unready pods from the `EndpointSlice` IP set).
* **Single-Node Toleration:**
  ```yaml
  tolerations:
    - key: "CriticalAddonsOnly"
      operator: "Exists"
      effect: "NoSchedule"
  ```
* **Service:** `type: ClusterIP` on port 80 forwarding to container port 8000. Resolvable at `http://backend-service:80` inside `aegis-apps`.

### Manifest 3: [`02-frontend.yaml`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/k8s/workloads/02-frontend.yaml)
* **Replicas:** 2
* **Container Image:** `kubeopsaegisacrprd.azurecr.io/frontend-ui:latest`
* **In-Cluster Reverse Proxy:** Configured in `nginx.conf`:
  ```nginx
  location /api/ {
      proxy_pass http://backend-service:80/api/;
  }
  ```
* **Service:** `type: LoadBalancer` (provisioning an Azure Public IP) or `type: ClusterIP` when routed via Ingress.

### Manifest 4: [`03-hpa.yaml`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/k8s/workloads/03-hpa.yaml)
* **Kind:** HorizontalPodAutoscaler (HPA v2)
* **Target:** `Deployment/backend-api`
* **Scaling Range:** Min 1 Pod, Max 4 Pods
* **Trigger:** CPU Utilization > 75%
* **Chaos Testing:** Tested via `POST /api/v1/chaos/cpu-burn`.

### Manifest 5: [`04-ingress.yaml`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/k8s/workloads/04-ingress.yaml)
* **Kind:** Ingress (Layer-7 Reverse Proxy)
* **Ingress Class:** `nginx`
* **Routing Table:**
  * `/api/(.*)` -> Forwarded to `backend-service:80`
  * `/(.*)`     -> Forwarded to `frontend-service:80`
* **Single IP Benefit:** All routes multiplexed over one public IP address.

---

## 5. How ClusterIP, Ports, and the Dynamic "IP Sets" Work

1. **No Process Listens on the ClusterIP Port:**
   * When you create `backend-service` with `ClusterIP: 10.0.142.85:80`, no daemon listens on that IP.
   * CoreDNS registers `backend-service.aegis-apps.svc.cluster.local -> 10.0.142.85`.
2. **The "IP Set" is the Kubernetes `EndpointSlice`:**
   * The Endpoints Controller continuously tracks Pods matching `app: backend-api`.
   * When their `/healthz` probe returns 200 OK, their IPs are added to the `EndpointSlice`:
     `endpoints: [10.244.0.12, 10.244.0.18]`
3. **Cilium eBPF Kernel Hash Map:**
   * Cilium reads the `EndpointSlice` and populates an in-kernel BPF hash map (`cilium_lb4_backends_v2`).
   * When Frontend Nginx sends a packet to `10.0.142.85:80`, Cilium intercepts it at the Linux kernel socket layer.
   * In constant $O(1)$ time, it rewrites the destination IP (DNAT) to `10.244.0.18:8000` with **zero iptables overhead**.

---

## 6. How Ingress, Load Balancers, and Domains Work

```
           [ Client Browser ]
                   │
                   ▼ (HTTP / HTTPS : 80 / 443)
        [ Azure Public IP (Load Balancer) ]
                   │
                   ▼
     [ Ingress Controller Pod (NGINX) ]
        │                            │
        │ Path: /                    │ Path: /api/*
        ▼                            ▼
 [ frontend-service ]         [ backend-service ]
   (ClusterIP: 80)              (ClusterIP: 80)
        │                            │
        ▼                            ▼
  [ Frontend Pods ]            [ Backend Pods ]
```

### Domain Name Resolution Options
1. **Option 1: Free Azure FQDN (Zero Cost, Instant)**
   * Azure Public IPs allow assigning a free DNS name label:
     `aegis-commerce.eastasia.cloudapp.azure.com`
2. **Option 2: Catch-All Ingress Rule (Raw Public IP)**
   * Our [`04-ingress.yaml`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/k8s/workloads/04-ingress.yaml) omits `host:` to match any incoming IP or domain.
3. **Option 3: Custom Domain (`store.yourdomain.com`)**
   * Point an `A Record` in Cloudflare / GoDaddy to the Azure Ingress Public IP.

---

## 7. 11:00 AM Provisioning Playbook (Ready to Execute)

When you return from breakfast at 11:00 AM, we will execute the provisioning sequence in order:

### Phase 1: Push All Verified Code & Manifests to GitHub
```powershell
# In PowerShell (d:\Sundeep\projects\azure\KubeOps-Aegis):
git add k8s/ charts/ apps/ .github/
git commit -m "feat: complete microservices manifests, aegis-apps namespace, and networking architecture"
git push origin feature/networking
```

### Phase 2: Build & Push Microservices to ACR
* GitHub Actions pipeline `.github/workflows/app-ci.yaml` automatically triggers:
  1. Runs Pytest unit tests (5/5 passing).
  2. Builds `backend-api` and pushes to `kubeopsaegisacrprd.azurecr.io/backend-api:latest`.
  3. Builds `frontend-ui` and pushes to `kubeopsaegisacrprd.azurecr.io/frontend-ui:latest`.

### Phase 3: ArgoCD GitOps Automated Sync
* ArgoCD detects the commit on branch `feature/networking`:
  1. Creates namespace `aegis-apps`.
  2. Deploys `backend-api` (2 replicas) with DB pool connection.
  3. Deploys `frontend-ui` (2 replicas).
  4. Attaches HPA v2 autoscaler.
  5. Provisions Azure Public IP on the frontend service.

### Phase 4: Retrieve Public URL & Live Browser Test
```powershell
# Check pods and services in aegis-apps namespace:
kubectl get pods,svc -n aegis-apps

# Get the Public External IP:
kubectl get svc frontend-service -n aegis-apps -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```
Open `http://<EXTERNAL-IP>/` in your browser to test live product catalogs, user login, and order checkout!
