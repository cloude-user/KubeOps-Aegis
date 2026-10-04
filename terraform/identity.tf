# ============================================================
# KubeOps-Aegis: Azure Workload Identity & Federated Credentials
# Maps Kubernetes Service Account to Azure Managed Identity
# ============================================================

# 1. Managed Identity for KubeOps AI Agent
resource "azurerm_user_assigned_identity" "agent_identity" {
  count               = var.deploy_aks ? 1 : 0
  name                = "${var.cluster_name}-agent-identity"
  location            = azurerm_resource_group.rg_ops.location
  resource_group_name = azurerm_resource_group.rg_ops.name

  tags = var.tags
}

# 2. Federated Identity Credential (OIDC Binding)
# Binds default:kubeops-agent-sa in K8s to Azure Managed Identity
resource "azurerm_federated_identity_credential" "agent_federated" {
  count               = var.deploy_aks ? 1 : 0
  name                = "${var.cluster_name}-agent-federated"
  resource_group_name = azurerm_resource_group.rg_ops.name
  audience            = ["api://AzureADTokenExchange"]
  issuer              = azurerm_kubernetes_cluster.aks[0].oidc_issuer_url
  parent_id           = azurerm_user_assigned_identity.agent_identity[0].id
  subject             = "system:serviceaccount:default:kubeops-agent-sa"
}

# 3. Azure RBAC Reader Role Assignment on Resource Group
resource "azurerm_role_assignment" "agent_rg_reader" {
  count                = var.deploy_aks ? 1 : 0
  scope                = azurerm_resource_group.rg_compute.id
  role_definition_name = "Reader"
  principal_id         = azurerm_user_assigned_identity.agent_identity[0].principal_id
}

# 4. Azure RBAC Cluster User Role Assignment on AKS
resource "azurerm_role_assignment" "agent_aks_cluster_user" {
  count                = var.deploy_aks ? 1 : 0
  scope                = azurerm_kubernetes_cluster.aks[0].id
  role_definition_name = "Azure Kubernetes Service Cluster User Role"
  principal_id         = azurerm_user_assigned_identity.agent_identity[0].principal_id
}
