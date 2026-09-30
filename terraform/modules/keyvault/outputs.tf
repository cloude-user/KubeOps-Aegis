output "keyvault_id" {
  value       = azurerm_key_vault.kv.id
  description = "Key Vault ID"
}

output "keyvault_uri" {
  value       = azurerm_key_vault.kv.vault_uri
  description = "Key Vault URI"
}

output "private_endpoint_ip" {
  value       = azurerm_private_endpoint.kv_pe.private_service_connection[0].private_ip_address
  description = "Private IP of Key Vault Private Endpoint"
}
