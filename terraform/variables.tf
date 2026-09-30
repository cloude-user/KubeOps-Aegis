variable "location" {
  type        = string
  description = "Azure Region location for all resources"
  default     = "eastus"
}

variable "resource_group_name" {
  type        = string
  description = "Name of the Azure Resource Group"
  default     = "rg-kubeops-aegis-prd"
}

variable "cluster_name" {
  type        = string
  description = "Name of the Azure Kubernetes Service (AKS) cluster"
  default     = "aks-kubeops-aegis-prd"
}

variable "environment" {
  type        = string
  description = "Deployment Environment (prd, dev, staging)"
  default     = "prd"
}

variable "kubernetes_version" {
  type        = string
  description = "Kubernetes Version for AKS"
  default     = "1.30.0"
}

variable "vnet_cidr" {
  type        = string
  description = "CIDR block for Virtual Network"
  default     = "10.100.0.0/16"
}

variable "system_node_vm_size" {
  type        = string
  description = "VM Size for AKS System Node Pool"
  default     = "Standard_D2s_v5"
}

variable "system_node_count" {
  type        = number
  description = "Count of nodes in System Node Pool"
  default     = 2
}

variable "user_node_vm_size" {
  type        = string
  description = "VM Size for AKS User Workload Node Pool"
  default     = "Standard_D4s_v5"
}

variable "min_user_node_count" {
  type        = number
  description = "Minimum nodes in User Node Pool"
  default     = 2
}

variable "max_user_node_count" {
  type        = number
  description = "Maximum nodes in User Node Pool"
  default     = 10
}

variable "desired_user_node_count" {
  type        = number
  description = "Desired nodes in User Node Pool"
  default     = 3
}
