variable "prefix" {
  type        = string
  description = "Prefix for all Azure resources"
  default     = "kubeops-aegis"
}

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

variable "tenant_id" {
  type        = string
  description = "Azure Tenant ID for Entra ID integration"
  default     = "00000000-0000-0000-0000-000000000000"
}

variable "admin_group_ids" {
  type        = list(string)
  description = "Object IDs of Entra ID groups with AKS Admin privileges"
  default     = ["00000000-0000-0000-0000-000000000000"]
}

variable "api_server_authorized_ip_ranges" {
  type        = list(string)
  description = "Authorized IP ranges for AKS API server"
  default     = ["198.51.100.0/24", "203.0.113.0/24"]
}

variable "db_password" {
  type        = string
  description = "Admin password for Neo4j and database resources"
  sensitive   = true
  default     = "P@ssw0rdAegis2026!Secure"
}

variable "db_sku_name" {
  type        = string
  description = "SKU Name for PostgreSQL Flexible Server"
  default     = "GP_Standard_D2s_v3"
}

variable "db_version" {
  type        = string
  description = "PostgreSQL Major Engine Version"
  default     = "16"
}

variable "tags" {
  type        = map(string)
  description = "Resource tags"
  default = {
    Environment = "prd"
    Project     = "KubeOps-Aegis"
    ManagedBy   = "Terraform"
  }
}

# ============================================================
# Feature Flags & Phased Deployment Controls
# ============================================================
variable "deploy_networking" {
  type        = bool
  description = "Enable deployment of Resource Groups, VNet, Subnets & NAT Gateway"
  default     = true
}

variable "deploy_data_layer" {
  type        = bool
  description = "Enable deployment of Key Vault, Storage Account, and Neo4j VM"
  default     = true
}

variable "deploy_aks" {
  type        = bool
  description = "Enable deployment of Azure Kubernetes Service (AKS) Cluster"
  default     = true
}

variable "deploy_neo4j" {
  type        = bool
  description = "Enable deployment of Neo4j VM instance"
  default     = false
}

variable "deploy_gitops_monitoring" {
  type        = bool
  description = "Enable deployment of ArgoCD & Prometheus Helm stacks inside AKS"
  default     = true
}

