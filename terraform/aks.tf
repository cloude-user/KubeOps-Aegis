# ============================================================
# KubeOps-Aegis: Azure Kubernetes Service (AKS) & Node Pools
# Azure CNI Overlay, Workload Identity (OIDC), Auto-scaling
# ============================================================

# 1. Managed Identity for AKS Cluster
resource "azurerm_user_assigned_identity" "aks_identity" {
  name                = "${var.cluster_name}-aks-identity"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  tags = azurerm_resource_group.rg.tags
}

# 2. Azure Kubernetes Service (AKS) Cluster
resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.cluster_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "${var.cluster_name}-dns"
  kubernetes_version  = var.kubernetes_version

  # Security & Workload Identity Configuration
  oidc_issuer_enabled       = true
  workload_identity_enabled = true
  local_account_disabled    = false

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aks_identity.id]
  }

  # System Node Pool Configuration
  default_node_pool {
    name                 = "systempool"
    vm_size              = var.system_node_vm_size
    node_count           = var.system_node_count
    vnet_subnet_id       = azurerm_subnet.aks_system_subnet.id
    auto_scaling_enabled = false
    orchestrator_version = var.kubernetes_version
    only_critical_addons_enabled = true

    node_labels = {
      "role" = "system"
      "env"  = var.environment
    }

    tags = azurerm_resource_group.rg.tags
  }

  # Network Profile: Azure CNI Overlay with NAT Gateway Egress
  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
    ebpf_data_plane     = "cilium"
    outbound_type       = "userAssignedNATGateway"
    dns_service_ip      = "10.0.0.10"
    service_cidr        = "10.0.0.0/16"
  }

  tags = azurerm_resource_group.rg.tags

  depends_on = [
    azurerm_subnet_nat_gateway_association.system_subnet_nat,
    azurerm_subnet_nat_gateway_association.user_subnet_nat
  ]
}

# 3. User Workload Node Pool (Auto-scaling Spot / On-Demand)
resource "azurerm_kubernetes_cluster_node_pool" "user_workloads" {
  name                  = "userpool"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks.id
  vm_size               = var.user_node_vm_size
  vnet_subnet_id        = azurerm_subnet.aks_user_subnet.id

  auto_scaling_enabled = true
  min_count            = var.min_user_node_count
  max_count            = var.max_user_node_count
  node_count           = var.desired_user_node_count

  node_labels = {
    "role" = "workload"
    "team" = "payments"
    "env"  = var.environment
  }

  tags = azurerm_resource_group.rg.tags
}

# Provider configurations for Kubernetes, Helm, & Kubectl on AKS
provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.aks.kube_config[0].host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = azurerm_kubernetes_cluster.aks.kube_config[0].host
    client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].client_certificate)
    client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].client_key)
    cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].cluster_ca_certificate)
  }
}

provider "kubectl" {
  host                   = azurerm_kubernetes_cluster.aks.kube_config[0].host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].cluster_ca_certificate)
  load_config_file       = false
}
