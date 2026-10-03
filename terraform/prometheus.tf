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

  timeout = 900 # 15 minutes timeout

  set {
    name  = "alertmanager.alertmanagerSpec.routePrefix"
    value = "/"
  }

  set {
    name  = "grafana.service.type"
    value = "ClusterIP"
  }

  # Disable admission webhook job that got stuck on pre-install
  set {
    name  = "prometheusOperator.admissionWebhooks.enabled"
    value = "false"
  }

  set {
    name  = "prometheusOperator.admissionWebhooks.patch.enabled"
    value = "false"
  }

  # Tolerations for Prometheus Operator
  set {
    name  = "prometheusOperator.tolerations[0].key"
    value = "CriticalAddonsOnly"
  }

  set {
    name  = "prometheusOperator.tolerations[0].operator"
    value = "Exists"
  }

  # Tolerations for Prometheus Server
  set {
    name  = "prometheus.prometheusSpec.tolerations[0].key"
    value = "CriticalAddonsOnly"
  }

  set {
    name  = "prometheus.prometheusSpec.tolerations[0].operator"
    value = "Exists"
  }

  # Tolerations for Alertmanager
  set {
    name  = "alertmanager.alertmanagerSpec.tolerations[0].key"
    value = "CriticalAddonsOnly"
  }

  set {
    name  = "alertmanager.alertmanagerSpec.tolerations[0].operator"
    value = "Exists"
  }

  # Tolerations for Grafana
  set {
    name  = "grafana.tolerations[0].key"
    value = "CriticalAddonsOnly"
  }

  set {
    name  = "grafana.tolerations[0].operator"
    value = "Exists"
  }

  # Tolerations for Kube-State-Metrics
  set {
    name  = "kube-state-metrics.tolerations[0].key"
    value = "CriticalAddonsOnly"
  }

  set {
    name  = "kube-state-metrics.tolerations[0].operator"
    value = "Exists"
  }

  # Tolerations for Node Exporter
  set {
    name  = "prometheus-node-exporter.tolerations[0].key"
    value = "CriticalAddonsOnly"
  }

  set {
    name  = "prometheus-node-exporter.tolerations[0].operator"
    value = "Exists"
  }

  depends_on = [azurerm_kubernetes_cluster.aks]
}
