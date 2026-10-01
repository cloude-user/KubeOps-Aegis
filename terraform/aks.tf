# ============================================================
# KubeOps-Aegis: Azure Kubernetes Service (AKS) & Node Pools
# Azure CNI Overlay, Cilium Network Policy, Workload Identity, RBAC
# ============================================================

# 1. Managed Identity for AKS Cluster
resource "azurerm_user_assigned_identity" "aks_identity" {
  count               = var.deploy_aks ? 1 : 0
  name                = "${var.cluster_name}-aks-identity"
  location            = azurerm_resource_group.rg_compute.location
  resource_group_name = azurerm_resource_group.rg_compute.name

  tags = var.tags
}

# 2. Azure Kubernetes Service (AKS) Cluster
resource "azurerm_kubernetes_cluster" "aks" {
  count               = var.deploy_aks ? 1 : 0
  name                = var.cluster_name
  location            = azurerm_resource_group.rg_compute.location
  resource_group_name = azurerm_resource_group.rg_compute.name
  dns_prefix          = "${var.cluster_name}-dns"
  kubernetes_version  = var.kubernetes_version

  # Security, RBAC & Workload Identity Configuration
  role_based_access_control_enabled = true
  oidc_issuer_enabled               = true
  workload_identity_enabled         = true
  local_account_disabled            = false

  azure_active_directory_role_based_access_control {
    managed                = true
    azure_rbac_enabled     = true
    tenant_id              = var.tenant_id
    admin_group_object_ids = var.admin_group_ids
  }

  api_server_authorized_ip_ranges = var.api_server_authorized_ip_ranges

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aks_identity[0].id]
  }

  # System Node Pool Configuration
  default_node_pool {
    name                         = "systempool"
    vm_size                      = var.system_node_vm_size
    node_count                   = var.system_node_count
    vnet_subnet_id               = module.vnet[0].aks_system_subnet_id
    enable_auto_scaling          = false
    orchestrator_version         = var.kubernetes_version
    only_critical_addons_enabled = true

    node_labels = {
      "role" = "system"
      "env"  = var.environment
    }

    tags = var.tags
  }

  # Network Profile: Azure CNI Overlay with Cilium eBPF Data Plane & Network Policy
  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
    network_policy      = "cilium"
    network_data_plane  = "cilium"
    outbound_type       = "userAssignedNATGateway"
    dns_service_ip      = "10.0.0.10"
    service_cidr        = "10.0.0.0/16"
  }

  tags = var.tags

  depends_on = [
    module.nat_gateway
  ]
}

# 3. User Workload Node Pool (Auto-scaling Spot / On-Demand)
resource "azurerm_kubernetes_cluster_node_pool" "user_workloads" {
  count                 = var.deploy_aks ? 1 : 0
  name                  = "userpool"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks[0].id
  vm_size               = var.user_node_vm_size
  vnet_subnet_id        = module.vnet[0].aks_user_subnet_id

  enable_auto_scaling = true
  min_count           = var.min_user_node_count
  max_count           = var.max_user_node_count
  node_count          = var.desired_user_node_count

  node_labels = {
    "role" = "workload"
    "team" = "payments"
    "env"  = var.environment
  }

  tags = var.tags
}

# Provider configurations for Kubernetes, Helm, & Kubectl on AKS
provider "kubernetes" {
  host                   = try(azurerm_kubernetes_cluster.aks[0].kube_config[0].host, "")
  client_certificate     = try(base64decode(azurerm_kubernetes_cluster.aks[0].kube_config[0].client_certificate), "")
  client_key             = try(base64decode(azurerm_kubernetes_cluster.aks[0].kube_config[0].client_key), "")
  cluster_ca_certificate = try(base64decode(azurerm_kubernetes_cluster.aks[0].kube_config[0].cluster_ca_certificate), "")
}

provider "helm" {
  kubernetes {
    host                   = try(azurerm_kubernetes_cluster.aks[0].kube_config[0].host, "")
    client_certificate     = try(base64decode(azurerm_kubernetes_cluster.aks[0].kube_config[0].client_certificate), "")
    client_key             = try(base64decode(azurerm_kubernetes_cluster.aks[0].kube_config[0].client_key), "")
    cluster_ca_certificate = try(base64decode(azurerm_kubernetes_cluster.aks[0].kube_config[0].cluster_ca_certificate), "")
  }
}

provider "kubectl" {
  host                   = try(azurerm_kubernetes_cluster.aks[0].kube_config[0].host, "")
  client_certificate     = try(base64decode(azurerm_kubernetes_cluster.aks[0].kube_config[0].client_certificate), "")
  client_key             = try(base64decode(azurerm_kubernetes_cluster.aks[0].kube_config[0].client_key), "")
  cluster_ca_certificate = try(base64decode(azurerm_kubernetes_cluster.aks[0].kube_config[0].cluster_ca_certificate), "")
  load_config_file       = false
}
