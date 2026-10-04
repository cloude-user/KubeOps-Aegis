# 🧱 KubeOps-Aegis: Terraform Infrastructure Architecture

> **Production-Grade Modular Azure Terraform Infrastructure for AKS 1.30+, Azure Managed PostgreSQL, Azure Key Vault, Azure Blob Storage & Container Registry**

---

## 📌 Phased Infrastructure Control Toggles (`prd.tfvars`)

To prevent unnecessary cloud spend while testing, the infrastructure deployment is divided into **4 Modular Phases** controlled by feature flags in [`env/prd.tfvars`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/terraform/env/prd.tfvars):

| Phase | Feature Flag | Azure Resources Deployed | Estimated Idle Cost |
| :--- | :--- | :--- | :--- |
| **Phase 1** | `deploy_networking = true` | 4 Resource Groups, VNet (`10.100.0.0/16`), 6 Subnets, Azure Standard NAT Gateway + Static Public IP | **~$1.20 / day** |
| **Phase 2** | `deploy_data_layer = true` | Azure Container Registry (ACR), Azure Key Vault + Private Endpoint, Azure Storage Account (4 Containers) + Private Endpoint, Azure Managed PostgreSQL Flexible Server (`Standard_B1ms`) | **~$0.50 / day** |
| **Phase 3** | `deploy_aks = true` | AKS 1.30+ Cluster (System Pool & User Workload Auto-scaling Node Pool), Azure CNI Overlay with Cilium eBPF, Workload Identity & OIDC | **~$3.50 – $5.00 / day** |
| **Phase 4** | `deploy_gitops_monitoring = true` | ArgoCD Helm Stack, Prometheus & AlertManager Helm Stack | Included in AKS |

---

## 🏛️ Comprehensive Resource-by-Resource Breakdown

### 1. Functional Resource Groups ([`main.tf`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/terraform/main.tf#L40-L64))
* **`rg_network`** (`kubeops-aegis-rg-network-prd`): Houses Virtual Network, Subnets, NAT Gateway & NSGs.
* **`rg_compute`** (`kubeops-aegis-rg-compute-prd`): Houses AKS Cluster, Node Pools, & Azure Container Registry (ACR).
* **`rg_data`** (`kubeops-aegis-rg-data-prd`): Houses Key Vault, Storage Account, & PostgreSQL Database.
* **`rg_ops`** (`kubeops-aegis-rg-ops-prd`): Houses Monitoring agents, User-Assigned Managed Identities, & OIDC Federated Credentials.

---

### 2. Virtual Network & Subnets Module ([`modules/vnet`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/terraform/modules/vnet/main.tf))
Creates 1 Virtual Network (`10.100.0.0/16`) with **6 dedicated `/24` subnets**:
* **`snet-aks-system`** (`10.100.1.0/24`): Isolated subnet for core K8s system pods (CoreDNS, Metrics-Server).
* **`snet-aks-user`** (`10.100.2.0/24`): Subnet for application microservices & AI SRE workloads.
* **`snet-database`** (`10.100.3.0/24`): Delegated subnet for Azure Database for PostgreSQL Flexible Server.
* **`snet-neo4j`** (`10.100.4.0/24`): Dedicated subnet for Neo4j graph database nodes.
* **`snet-private-endpoints`** (`10.100.5.0/24`): Subnet hosting Private Endpoints for Key Vault & Storage Account.
* **`snet-ingress`** (`10.100.6.0/24`): Public-facing subnet reserved for Application Gateway / NGINX Ingress Controller.

---

### 3. Azure Standard NAT Gateway ([`modules/nat_gateway`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/terraform/modules/nat_gateway/main.tf))
* **`azurerm_public_ip.nat_pip`**: Static, Standard Public IP assigned to NAT Gateway.
* **`azurerm_nat_gateway.nat_gw`**: Handles all outbound internet egress for AKS nodes without exposing node IP addresses to the public internet.
* **Subnet Association**: Attached to `snet-aks-system` and `snet-aks-user`.

---

### 4. Azure Container Registry (ACR) ([`acr.tf`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/terraform/acr.tf))
* **`azurerm_container_registry.acr`**: Standard SKU container registry (`kubeopsaegisacrprd`) for storing Docker images (`backend-api:v1.0.0`, `frontend-ui:v1.0.0`, `kubeops-aegis-agent:v2.0.0`).
* **`azurerm_role_assignment.aks_acr_pull`**: Grants the AKS Kubelet Managed Identity `AcrPull` permissions to fetch private images automatically without imagePullSecrets.

---

### 5. Azure Key Vault & Storage Account ([`modules/keyvault`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/terraform/modules/keyvault/main.tf), [`modules/storage`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/terraform/modules/storage/main.tf))
* **`module.keyvault`**: Azure Key Vault with Private Endpoint in `snet-private-endpoints`. Stores database passwords, JWT secrets, and Azure OpenAI API keys.
* **`module.storage`**: Azure Blob Storage Account (`kubeopsaegisstprd`) with 4 private containers (`tfstate`, `incident-logs`, `user-media`, `order-receipts`).

---

### 6. Azure Managed PostgreSQL Flexible Server ([`modules/postgresql`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/terraform/modules/postgresql/main.tf))
* **`azurerm_postgresql_flexible_server`**: Managed PostgreSQL 15 database instance using the cost-optimized **`Standard_B1ms` Burstable SKU** (~$15-$25/mo).
* **Private DNS Zone Link**: Connected to internal VNet DNS (`privatelink.postgres.database.azure.com`).

---

### 7. Azure Workload Identity & OIDC ([`identity.tf`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/terraform/identity.tf))
* **`azurerm_user_assigned_identity.agent_identity`**: User-Assigned Managed Identity for the SRE Agent.
* **`azurerm_federated_identity_credential.agent_federated`**: Establishes Passwordless OIDC federation between Kubernetes ServiceAccount `kubeops-system:aegis-agent-sa` and Azure Managed Identity.

---

### 8. Azure Kubernetes Service (AKS) ([`aks.tf`](file:///d:/Sundeep/projects/azure/KubeOps-Aegis/terraform/aks.tf))
* **`azurerm_kubernetes_cluster.aks`**: AKS 1.30+ cluster configured with:
  * **Azure CNI Overlay with Cilium eBPF**: High-performance eBPF network data plane & security policies.
  * **System Node Pool**: 2 nodes (`Standard_D2s_v5`).
  * **User Workload Node Pool**: Auto-scaling pool (2 to 10 nodes, `Standard_D4s_v5`).
  * **Azure Entra ID Integration**: Managed Azure RBAC for cluster access.

---

## 🚀 Execution Commands

```bash
# 1. Initialize Terraform & Azure Remote State Backend
terraform init \
  -backend-config="resource_group_name=rg-aegis-ops-prd" \
  -backend-config="storage_account_name=tfstateaegisprd" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=prd.terraform.tfstate"

# 2. Plan Infrastructure (Phase 1 Only)
terraform plan -var-file="env/prd.tfvars" -out=tfplan

# 3. Apply Infrastructure
terraform apply tfplan

# 4. Connect kubectl to AKS Cluster
$(terraform output -raw kubeconfig_command)
```
