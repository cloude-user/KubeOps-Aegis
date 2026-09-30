output "vnet_id" {
  value       = azurerm_virtual_network.vnet.id
  description = "Virtual Network ID"
}

output "vnet_name" {
  value       = azurerm_virtual_network.vnet.name
  description = "Virtual Network Name"
}

output "aks_system_subnet_id" {
  value       = azurerm_subnet.aks_system.id
  description = "AKS System Subnet ID"
}

output "aks_user_subnet_id" {
  value       = azurerm_subnet.aks_user.id
  description = "AKS User Subnet ID"
}

output "database_subnet_id" {
  value       = azurerm_subnet.database.id
  description = "PostgreSQL Database Subnet ID"
}

output "neo4j_subnet_id" {
  value       = azurerm_subnet.neo4j.id
  description = "Neo4j Subnet ID"
}

output "private_endpoints_subnet_id" {
  value       = azurerm_subnet.private_endpoints.id
  description = "Private Endpoints Subnet ID"
}

output "ingress_subnet_id" {
  value       = azurerm_subnet.ingress.id
  description = "Ingress Subnet ID"
}
