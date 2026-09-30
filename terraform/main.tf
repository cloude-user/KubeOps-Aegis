# ============================================================
# KubeOps-Aegis: Azure Production Infrastructure (Terraform)
# Resource Group, VNet, Subnets, NAT Gateway & Network Security Groups
# ============================================================

terraform {
  required_version = ">= 1.14.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.14"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# 1. Primary Azure Resource Group
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Project     = "KubeOps-Aegis-Azure"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# 2. Virtual Network (VNet)
resource "azurerm_virtual_network" "vnet" {
  name                = "${var.cluster_name}-vnet"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  address_space       = [var.vnet_cidr]

  tags = azurerm_resource_group.rg.tags
}

# 3. Subnets (AKS System Subnet, Workload Subnet, Ingress Subnet)
resource "azurerm_subnet" "aks_system_subnet" {
  name                 = "aks-system-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.100.1.0/24"]
}

resource "azurerm_subnet" "aks_user_subnet" {
  name                 = "aks-user-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.100.2.0/24"]
}

resource "azurerm_subnet" "ingress_subnet" {
  name                 = "ingress-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.100.3.0/24"]
}

# 4. Azure NAT Gateway & Public IP (Secure Outbound Internet Egress)
resource "azurerm_public_ip" "nat_pip" {
  name                = "${var.cluster_name}-nat-pip"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = azurerm_resource_group.rg.tags
}

resource "azurerm_nat_gateway" "nat_gw" {
  name                    = "${var.cluster_name}-nat-gw"
  location                = azurerm_resource_group.rg.location
  resource_group_name     = azurerm_resource_group.rg.name
  sku_name                = "Standard"
  idle_timeout_in_minutes = 10

  tags = azurerm_resource_group.rg.tags
}

resource "azurerm_nat_gateway_public_ip_association" "nat_pip_assoc" {
  nat_gateway_id       = azurerm_nat_gateway.nat_gw.id
  public_ip_address_id = azurerm_public_ip.nat_pip.id
}

# Associate NAT Gateway with AKS Subnets
resource "azurerm_subnet_nat_gateway_association" "system_subnet_nat" {
  subnet_id      = azurerm_subnet.aks_system_subnet.id
  nat_gateway_id = azurerm_nat_gateway.nat_gw.id
}

resource "azurerm_subnet_nat_gateway_association" "user_subnet_nat" {
  subnet_id      = azurerm_subnet.aks_user_subnet.id
  nat_gateway_id = azurerm_nat_gateway.nat_gw.id
}

# 5. Network Security Group (NSG) with Strict Security Protocols
resource "azurerm_network_security_group" "aks_nsg" {
  name                = "${var.cluster_name}-nsg"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  # Security Rule 1: Allow HTTPS Inbound
  security_rule {
    name                       = "AllowHTTPSInbound"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  # Security Rule 2: Allow Internal VNet Traffic
  security_rule {
    name                       = "AllowVNetInbound"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "VirtualNetwork"
  }

  # Security Rule 3: Deny All Other Inbound Traffic
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

  tags = azurerm_resource_group.rg.tags
}

# Associate NSG with Subnets
resource "azurerm_subnet_network_security_group_association" "system_nsg_assoc" {
  subnet_id                 = azurerm_subnet.aks_system_subnet.id
  network_security_group_id = azurerm_network_security_group.aks_nsg.id
}

resource "azurerm_subnet_network_security_group_association" "user_nsg_assoc" {
  subnet_id                 = azurerm_subnet.aks_user_subnet.id
  network_security_group_id = azurerm_network_security_group.aks_nsg.id
}
