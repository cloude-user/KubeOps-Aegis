# ============================================================
# Reusable Terraform Module: Azure Blob Storage + Private Endpoint
# RAG Document & Media Storage with Zero Public Access
# ============================================================

resource "azurerm_storage_account" "storage" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  public_network_access_enabled = false

  tags = var.tags
}

resource "azurerm_storage_container" "container_rag" {
  name                  = "rag-documents"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}

# Private DNS Zone for Blob Storage
resource "azurerm_private_dns_zone" "dns_blob" {
  name                = "privatelink.blob.core.windows.net"
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "vnet_link" {
  name                  = "${var.storage_account_name}-dns-link"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.dns_blob.name
  virtual_network_id    = var.vnet_id
}

# Private Endpoint for Storage Account
resource "azurerm_private_endpoint" "storage_pe" {
  name                = "${var.storage_account_name}-pe"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id

  private_service_connection {
    name                           = "${var.storage_account_name}-connection"
    private_connection_resource_id = azurerm_storage_account.storage.id
    is_manual_connection           = false
    subresource_names              = ["blob"]
  }

  private_dns_zone_group {
    name                 = "blob-dns-zone-group"
    private_dns_zone_ids = [azurerm_private_dns_zone.dns_blob.id]
  }

  tags = var.tags
}
