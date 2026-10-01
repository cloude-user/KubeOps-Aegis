# ============================================================
# KubeOps-Aegis: ArgoCD Helm Release on AKS
# ============================================================

resource "helm_release" "argocd" {
  count            = (var.deploy_aks && var.deploy_gitops_monitoring) ? 1 : 0
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = "6.7.18"
  namespace        = "argocd"
  create_namespace = true

  set {
    name  = "server.service.type"
    value = "LoadBalancer"
  }

  set {
    name  = "server.extraArgs"
    value = "{--insecure}"
  }

  set {
    name  = "configs.params.server\\.insecure"
    value = "true"
  }

  depends_on = [azurerm_kubernetes_cluster.aks]
}
