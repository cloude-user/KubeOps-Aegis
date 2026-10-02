variable "server_name" {
  type        = string
  description = "PostgreSQL Flexible Server Name"
}

variable "location" {
  type        = string
  description = "Azure Region Location"
}

variable "resource_group_name" {
  type        = string
  description = "Resource Group Name"
}

variable "subnet_id" {
  type        = string
  description = "Delegated Subnet ID for PostgreSQL"
}

variable "vnet_id" {
  type        = string
  description = "Virtual Network ID"
}

variable "admin_username" {
  type        = string
  description = "Database Admin Username"
  default     = "aegisadmin"
}

variable "admin_password" {
  type        = string
  description = "Database Admin Password"
  sensitive   = true
}

variable "sku_name" {
  type        = string
  description = "SKU Name for PostgreSQL Flexible Server"
  default     = "B_Standard_B1ms"
}

variable "tags" {
  type        = map(string)
  description = "Tags map"
  default     = {}
}
