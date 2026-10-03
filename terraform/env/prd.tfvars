# =============================================================
# KubeOps-Aegis: Production Environment Variables (prd.tfvars)
# =============================================================

# Feature Toggles
deploy_networking        = true
deploy_data_layer        = true
deploy_neo4j             = false
deploy_aks               = true
deploy_gitops_monitoring = false

# General Azure Configuration
location            = "eastasia"
resource_group_name = "rg-kubeops-aegis-prd"
cluster_name        = "aks-kubeops-aegis-prd"
environment         = "prd"
kubernetes_version  = "1.36.4"

# Database Configuration
db_sku_name = "B_Standard_B1ms"
db_version  = "16"

# Networking Configuration
vnet_cidr = "10.100.0.0/16"

# Node Pool Sizing (Applies when deploy_aks = true)
system_node_vm_size     = "Standard_D2s_v5"
system_node_count       = 1
user_node_vm_size       = "Standard_D4s_v5"
min_user_node_count     = 1
max_user_node_count     = 5
desired_user_node_count = 1
