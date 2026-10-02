# ============================================================
# KubeOps-Aegis: Azure Modular Infrastructure (Terraform)
# Resource Groups, VNet, Subnets, NAT Gateway, NSGs, Private Endpoints
# ============================================================

terraform {
  required_version = ">= 1.9.0"

  # Dynamic Azure Blob Remote Backend (initialized via GitHub Actions -backend-config)
  backend "azurerm" {}

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
      version = ">= 1.14.0"
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

# 1. Functional Resource Groups
resource "azurerm_resource_group" "rg_network" {
  name     = "${var.prefix}-rg-network-${var.environment}"
  location = var.location
  tags     = var.tags
}

resource "azurerm_resource_group" "rg_compute" {
  name     = "${var.prefix}-rg-compute-${var.environment}"
  location = var.location
  tags     = var.tags
}

resource "azurerm_resource_group" "rg_data" {
  name     = "${var.prefix}-rg-data-${var.environment}"
  location = var.location
  tags     = var.tags
}

resource "azurerm_resource_group" "rg_ops" {
  name     = "${var.prefix}-rg-ops-${var.environment}"
  location = var.location
  tags     = var.tags
}

# 2. VNet & Subnets Module
module "vnet" {
  count               = var.deploy_networking ? 1 : 0
  source              = "./modules/vnet"
  vnet_name           = "${var.prefix}-vnet-${var.environment}"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg_network.name
  vnet_cidr           = var.vnet_cidr
  tags                = var.tags
}

# 3. NAT Gateway Module
module "nat_gateway" {
  count               = var.deploy_networking ? 1 : 0
  source              = "./modules/nat_gateway"
  nat_gateway_name    = "${var.prefix}-nat-gw-${var.environment}"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg_network.name
  subnet_ids          = [module.vnet[0].aks_system_subnet_id, module.vnet[0].aks_user_subnet_id]
  tags                = var.tags
}

# 4. Azure Storage & Private Endpoint Module
module "storage" {
  count                      = var.deploy_data_layer && var.deploy_networking ? 1 : 0
  source                     = "./modules/storage"
  storage_account_name       = "${replace(var.prefix, "-", "")}st${var.environment}" # e.g. kubeopsaegisstprd
  location                   = var.location
  resource_group_name        = azurerm_resource_group.rg_data.name
  vnet_id                    = module.vnet[0].vnet_id
  private_endpoint_subnet_id = module.vnet[0].private_endpoints_subnet_id
  tags                       = var.tags
}

# 5. Azure Key Vault & Private Endpoint Module
module "keyvault" {
  count                      = var.deploy_data_layer && var.deploy_networking ? 1 : 0
  source                     = "./modules/keyvault"
  keyvault_name              = "${var.prefix}-kv-${var.environment}"
  location                   = var.location
  resource_group_name        = azurerm_resource_group.rg_data.name
  vnet_id                    = module.vnet[0].vnet_id
  private_endpoint_subnet_id = module.vnet[0].private_endpoints_subnet_id
  tags                       = var.tags
}

# 6. PostgreSQL Flexible Server Module (Managed DB - ~$15-$25/mo)
module "postgresql" {
  count               = var.deploy_data_layer && var.deploy_networking ? 1 : 0
  source              = "./modules/postgresql"
  server_name         = "${var.prefix}-psql-${var.environment}"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg_data.name
  subnet_id           = module.vnet[0].database_subnet_id
  vnet_id             = module.vnet[0].vnet_id
  admin_password      = var.db_password
  tags                = var.tags
}

# 7. Neo4j Graph Database Module
module "neo4j" {
  count               = var.deploy_data_layer && var.deploy_networking ? 1 : 0
  source              = "./modules/neo4j"
  neo4j_instance_name = "${var.prefix}-vm-neo4j-${var.environment}"
  location            = var.location
  resource_group_name = azurerm_resource_group.rg_data.name
  subnet_id           = module.vnet[0].neo4j_subnet_id
  admin_password      = var.db_password
  tags                = var.tags
}
