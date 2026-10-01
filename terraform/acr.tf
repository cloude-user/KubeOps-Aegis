# ============================================================
# KubeOps-Aegis: Azure Container Registry (ACR) & Role Assignments
# ============================================================

resource "azurerm_container_registry" "acr" {
  count               = var.deploy_aks ? 1 : 0
  name                = "${replace(var.cluster_name, "-", "")}acr"
  resource_group_name = azurerm_resource_group.rg_compute.name
  location            = azurerm_resource_group.rg_compute.location
  sku                 = "Standard"
  admin_enabled       = false

  tags = var.tags
}

# Grant AKS Identity permission to pull images from ACR (AcrPull)
resource "azurerm_role_assignment" "aks_acr_pull" {
  count                = var.deploy_aks ? 1 : 0
  principal_id         = azurerm_kubernetes_cluster.aks[0].kubelet_identity[0].object_id
  role_definition_name = "AcrPull"
  scope                = azurerm_container_registry.acr[0].id
}
