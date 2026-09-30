variable "neo4j_instance_name" {
  type        = string
  description = "Name of Neo4j VM Instance"
  default     = "vm-neo4j-graphrag"
}

variable "location" {
  type        = string
  description = "Azure Region location"
}

variable "resource_group_name" {
  type        = string
  description = "Resource Group Name"
}

variable "subnet_id" {
  type        = string
  description = "Subnet ID for Neo4j VM"
}

variable "vm_size" {
  type        = string
  description = "VM Size for Neo4j Graph DB"
  default     = "Standard_D2s_v5"
}

variable "admin_username" {
  type        = string
  description = "Admin Username"
  default     = "neo4jadmin"
}

variable "admin_password" {
  type        = string
  description = "Admin Password"
  sensitive   = true
}

variable "tags" {
  type        = map(string)
  description = "Tags map"
  default     = {}
}
