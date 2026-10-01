# ============================================================
# KubeOps-Aegis: Prometheus Monitoring Stack Helm Release on AKS
# ============================================================

resource "helm_release" "kube_prometheus_stack" {
  count            = (var.deploy_aks && var.deploy_gitops_monitoring) ? 1 : 0
  name             = "kube-prometheus-stack"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  version          = "58.2.2"
  namespace        = "monitoring"
  create_namespace = true

  set {
    name  = "alertmanager.alertmanagerSpec.routePrefix"
    value = "/"
  }

  set {
    name  = "grafana.service.type"
    value = "ClusterIP"
  }

  depends_on = [azurerm_kubernetes_cluster.aks]
}
