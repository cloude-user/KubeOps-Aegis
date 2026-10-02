# ============================================================
# KubeOps-Aegis: Azure Container Registry (ACR) & Role Assignments
# Stores Docker Container Images for Backend API & Frontend UI
# ============================================================

# 1. Azure Container Registry (Standard SKU for Image Storage & Security Scanning)
resource "azurerm_container_registry" "acr" {
  count               = var.deploy_data_layer || var.deploy_aks ? 1 : 0
  name                = "${replace(var.prefix, "-", "")}acr${var.environment}" # e.g. kubeopsaegisacrprd
  resource_group_name = azurerm_resource_group.rg_compute.name
  location            = azurerm_resource_group.rg_compute.location
  sku                 = "Standard"
  admin_enabled       = false # Admin keys disabled for security (uses Entra ID / Managed Identity)

  tags = var.tags
}

# 2. RBAC Role Assignment: Grant AKS Kubelet Permission to Pull Images from ACR (AcrPull)
resource "azurerm_role_assignment" "aks_acr_pull" {
  count                = var.deploy_aks && (var.deploy_data_layer || var.deploy_aks) ? 1 : 0
  principal_id         = azurerm_kubernetes_cluster.aks[0].kubelet_identity[0].object_id
  role_definition_name = "AcrPull"
  scope                = azurerm_container_registry.acr[0].id
}
