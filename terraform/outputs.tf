output "resource_group_name" {
  value       = azurerm_resource_group.rg_compute.name
  description = "The name of the Azure Resource Group"
}

output "aks_cluster_name" {
  value       = try(azurerm_kubernetes_cluster.aks[0].name, "disabled")
  description = "The name of the AKS Cluster"
}

output "aks_oidc_issuer_url" {
  value       = try(azurerm_kubernetes_cluster.aks[0].oidc_issuer_url, "disabled")
  description = "OIDC Issuer URL for AKS Workload Identity"
}

output "acr_login_server" {
  value       = try(azurerm_container_registry.acr[0].login_server, "disabled")
  description = "Azure Container Registry Login Server URL"
}

output "nat_public_ip" {
  value       = try(module.nat_gateway[0].public_ip_address, "disabled")
  description = "Static Public IP attached to Azure NAT Gateway for egress"
}

output "kubeconfig_command" {
  value       = try("az aks get-credentials --resource-group ${azurerm_resource_group.rg_compute.name} --name ${azurerm_kubernetes_cluster.aks[0].name} --overwrite-existing", "disabled")
  description = "Azure CLI command to configure local kubectl context"
}
