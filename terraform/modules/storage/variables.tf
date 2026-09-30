variable "storage_account_name" {
  type        = string
  description = "Globally unique name for Storage Account"
}

variable "location" {
  type        = string
  description = "Azure Region location"
}

variable "resource_group_name" {
  type        = string
  description = "Resource Group Name"
}

variable "vnet_id" {
  type        = string
  description = "Virtual Network ID for Private DNS link"
}

variable "private_endpoint_subnet_id" {
  type        = string
  description = "Subnet ID for Private Endpoint"
}

variable "tags" {
  type        = map(string)
  description = "Tags map"
  default     = {}
}
