output "storage_account_id" {
  value       = azurerm_storage_account.storage.id
  description = "Storage Account ID"
}

output "storage_account_name" {
  value       = azurerm_storage_account.storage.name
  description = "Storage Account Name"
}

output "primary_blob_endpoint" {
  value       = azurerm_storage_account.storage.primary_blob_endpoint
  description = "Primary Blob Endpoint URL"
}

output "private_endpoint_ip" {
  value       = azurerm_private_endpoint.storage_pe.private_service_connection[0].private_ip_address
  description = "Private IP of Storage Private Endpoint"
}
