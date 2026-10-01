variable "vnet_name" {
  type        = string
  description = "Name of the Virtual Network"
}

variable "location" {
  type        = string
  description = "Azure Region location"
}

variable "resource_group_name" {
  type        = string
  description = "Resource Group Name"
}

variable "vnet_cidr" {
  type        = string
  description = "Virtual Network CIDR block"
  default     = "10.100.0.0/16"
}

variable "subnet_cidrs" {
  type        = map(string)
  description = "Map of subnet names to CIDR blocks"
  default = {
    aks_system        = "10.100.1.0/24"
    aks_user          = "10.100.2.0/24"
    database          = "10.100.3.0/24"
    neo4j             = "10.100.4.0/24"
    private_endpoints = "10.100.5.0/24"
    ingress           = "10.100.6.0/24"
  }
}

variable "tags" {
  type        = map(string)
  description = "Tags map"
  default     = {}
}
