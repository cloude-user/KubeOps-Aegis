# =============================================================ƒ KubeOps-Aegis: Production Environment Variables (prd.tfvars)
# =============================================================

# Feature Toggles (Phase 1: Deploy Networking Only Today)
deploy_networking        = true
deploy_data_layer        = false
deploy_aks               = false
deploy_gitops_monitoring = false

# General Azure Configuration
location            = "eastus"
resource_group_name = "rg-kubeops-aegis-prd"
cluster_name        = "aks-kubeops-aegis-prd"
environment         = "prd"
kubernetes_version  = "1.30.0"

# Networking Configuration
vnet_cidr = "10.100.0.0/16"

# Node Pool Sizing (Applies when deploy_aks = true)
system_node_vm_size     = "Standard_D2s_v5"
system_node_count       = 2
user_node_vm_size       = "Standard_D4s_v5"
min_user_node_count     = 2
max_user_node_count     = 10
desired_user_node_count = 3
