# ============================================================
# Reusable Terraform Module: Azure Database for PostgreSQL Flexible Server
# Burstable SKU (Standard_B1ms) for Cost Optimization (~$15-$25/mo)
# ============================================================

resource "azurerm_postgresql_flexible_server" "psql" {
  name                   = var.server_name
  resource_group_name    = var.resource_group_name
  location               = var.location
  version                = "14"
  delegated_subnet_id    = var.subnet_id
  private_dns_zone_id    = azurerm_private_dns_zone.dns_psql.id
  administrator_login    = var.admin_username
  administrator_password = var.admin_password
  zone                   = "1"

  sku_name   = "B_Standard_B1ms" # Burstable 1 vCPU, 2GB RAM (~$15-$25/month)
  storage_mb = 32768             # 32 GB Storage

  backup_retention_days = 7

  tags = var.tags

  depends_on = [
    azurerm_private_dns_zone_virtual_network_link.dns_vnet_link
  ]
}

resource "azurerm_postgresql_flexible_server_database" "db" {
  name      = "orderdb"
  server_id = azurerm_postgresql_flexible_server.psql.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# Private DNS Zone for PostgreSQL Flexible Server
resource "azurerm_private_dns_zone" "dns_psql" {
  name                = "${var.server_name}.private.postgres.database.azure.com"
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "dns_vnet_link" {
  name                  = "${var.server_name}-dns-link"
  private_dns_zone_name = azurerm_private_dns_zone.dns_psql.name
  resource_group_name   = var.resource_group_name
  virtual_network_id    = var.vnet_id
}
