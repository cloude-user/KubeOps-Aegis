# ============================================================
# KubeOps-Aegis: Azure Workload Identity & Federated Credentials
# Maps Kubernetes Service Account to Azure Managed Identity
# ============================================================

# 1. Managed Identity for KubeOps AI Agent
resource "azurerm_user_assigned_identity" "agent_identity" {
  name                = "${var.cluster_name}-agent-identity"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  tags = azurerm_resource_group.rg.tags
}

# 2. Federated Identity Credential (OIDC Binding)
# Binds default:kubeops-agent-sa in K8s to Azure Managed Identity
resource "azurerm_federated_identity_credential" "agent_federated" {
  name                = "${var.cluster_name}-agent-federated"
  resource_group_name = azurerm_resource_group.rg.name
  audience            = ["api://AzureADTokenExchange"]
  issuer              = azurerm_kubernetes_cluster.aks.oidc_issuer_url
  parent_id           = azurerm_user_assigned_identity.agent_identity.id
  subject             = "system:serviceaccount:default:kubeops-agent-sa"
}

# 3. Azure RBAC Reader Role Assignment on Resource Group
resource "azurerm_role_assignment" "agent_rg_reader" {
  scope                = azurerm_resource_group.rg.id
  role_definition_name = "Reader"
  principal_id         = azurerm_user_assigned_identity.agent_identity.principal_id
}

# 4. Azure RBAC Cluster User Role Assignment on AKS
resource "azurerm_role_assignment" "agent_aks_cluster_user" {
  scope                = azurerm_kubernetes_cluster.aks.id
  role_definition_name = "Azure Kubernetes Service Cluster User Role"
  principal_id         = azurerm_user_assigned_identity.agent_identity.principal_id
}
