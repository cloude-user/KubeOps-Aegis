# ============================================================
# KubeOps-Aegis: Azure Container Registry (ACR) & Role Assignments
# ============================================================

resource "azurerm_container_registry" "acr" {
  name                = "${replace(var.cluster_name, "-", "")}acr"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Standard"
  admin_enabled       = false

  tags = azurerm_resource_group.rg.tags
}

# Grant AKS Identity permission to pull images from ACR (AcrPull)
resource "azurerm_role_assignment" "aks_acr_pull" {
  principal_id         = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
  role_definition_name = "AcrPull"
  scope                = azurerm_container_registry.acr.id
}
