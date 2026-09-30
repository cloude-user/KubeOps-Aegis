output "neo4j_private_ip" {
  value       = azurerm_network_interface.neo4j_nic.private_ip_address
  description = "Private IP of Neo4j Instance"
}

output "bolt_url" {
  value       = "bolt://${azurerm_network_interface.neo4j_nic.private_ip_address}:7687"
  description = "Neo4j Bolt Driver Connection String"
}

output "browser_url" {
  value       = "http://${azurerm_network_interface.neo4j_nic.private_ip_address}:7474"
  description = "Neo4j Browser HTTP Endpoint"
}
