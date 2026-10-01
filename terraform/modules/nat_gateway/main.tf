# ============================================================
# Reusable Terraform Module: Azure Standard NAT Gateway
# Outbound Internet Egress for AKS & Subnets
# ============================================================

resource "azurerm_public_ip" "nat_pip" {
  name                = "${var.nat_gateway_name}-pip"
  location            = var.location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = var.tags
}

resource "azurerm_nat_gateway" "nat_gw" {
  name                    = var.nat_gateway_name
  location                = var.location
  resource_group_name     = var.resource_group_name
  sku_name                = "Standard"
  idle_timeout_in_minutes = 10
  tags                    = var.tags
}

resource "azurerm_nat_gateway_public_ip_association" "pip_assoc" {
  nat_gateway_id       = azurerm_nat_gateway.nat_gw.id
  public_ip_address_id = azurerm_public_ip.nat_pip.id
}

# Subnet NAT Associations
resource "azurerm_subnet_nat_gateway_association" "subnet_assoc" {
  count          = length(var.subnet_ids)
  subnet_id      = var.subnet_ids[count.index]
  nat_gateway_id = azurerm_nat_gateway.nat_gw.id
}
