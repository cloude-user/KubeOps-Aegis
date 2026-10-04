# ============================================================
# Reusable Terraform Module: Azure Virtual Network, Subnets & NSGs
# Creates VNet with 6 dedicated enterprise subnets & Network Security Groups
# ============================================================

resource "azurerm_virtual_network" "vnet" {
  name                = var.vnet_name
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = [var.vnet_cidr]
  tags                = var.tags
}

# Subnet 1: AKS System Nodes
resource "azurerm_subnet" "aks_system" {
  name                 = "snet-aks-system"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.subnet_cidrs["aks_system"]]
}

# Subnet 2: AKS User / AI Workload Nodes
resource "azurerm_subnet" "aks_user" {
  name                 = "snet-aks-user"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.subnet_cidrs["aks_user"]]
}

# Subnet 3: PostgreSQL Flexible Server (Delegated)
resource "azurerm_subnet" "database" {
  name                 = "snet-database"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.subnet_cidrs["database"]]

  delegation {
    name = "psql-delegation"
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

# Subnet 4: Neo4j Graph Database
resource "azurerm_subnet" "neo4j" {
  name                 = "snet-neo4j"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.subnet_cidrs["neo4j"]]
}

# Subnet 5: Private Endpoints (Storage, Key Vault, ACR)
resource "azurerm_subnet" "private_endpoints" {
  name                 = "snet-private-endpoints"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.subnet_cidrs["private_endpoints"]]
}

# Subnet 6: Ingress Gateway (App Gateway / ALB)
resource "azurerm_subnet" "ingress" {
  name                 = "snet-ingress"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.subnet_cidrs["ingress"]]
}

# ============================================================
# Enterprise Network Security Groups (NSG) Rules
# ============================================================

# NSG 1: Database Subnet Protection NSG
resource "azurerm_network_security_group" "nsg_database" {
  name                = "${var.vnet_name}-nsg-database"
  location            = var.location
  resource_group_name = var.resource_group_name

  security_rule {
    name                       = "AllowPostgreSQLFromAKS"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5432"
    source_address_prefixes    = [var.subnet_cidrs["aks_system"], var.subnet_cidrs["aks_user"]]
    destination_address_prefix = var.subnet_cidrs["database"]
  }

  security_rule {
    name                       = "DenyAllInbound"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = var.tags
}

resource "azurerm_subnet_network_security_group_association" "nsg_assoc_database" {
  subnet_id                 = azurerm_subnet.database.id
  network_security_group_id = azurerm_network_security_group.nsg_database.id
}

# NSG 2: Private Endpoints Protection NSG
resource "azurerm_network_security_group" "nsg_private_endpoints" {
  name                = "${var.vnet_name}-nsg-pe"
  location            = var.location
  resource_group_name = var.resource_group_name

  security_rule {
    name                       = "AllowHTTPSFromVNet"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = var.vnet_cidr
    destination_address_prefix = var.subnet_cidrs["private_endpoints"]
  }

  tags = var.tags
}

resource "azurerm_subnet_network_security_group_association" "nsg_assoc_pe" {
  subnet_id                 = azurerm_subnet.private_endpoints.id
  network_security_group_id = azurerm_network_security_group.nsg_private_endpoints.id
}
