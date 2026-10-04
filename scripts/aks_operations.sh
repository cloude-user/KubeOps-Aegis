#!/usr/bin/env bash
# ==============================================================================
# KubeOps-Aegis: AKS Operations, Cluster Login & Public Access Cheatsheet
# Target Cluster: aks-kubeops-aegis-prd (Resource Group: kubeops-aegis-rg-compute-prd)
# ==============================================================================

set -e

echo "=========================================================="
echo " 1. Authenticating to AKS Cluster (Admin Credentials)"
echo "=========================================================="
az aks get-credentials \
  --resource-group kubeops-aegis-rg-compute-prd \
  --name aks-kubeops-aegis-prd \
  --admin \
  --overwrite-existing

echo ""
echo ">> Verifying Node Connection:"
kubectl get nodes -o wide

echo ""
echo "=========================================================="
echo " 2. ArgoCD GitOps Public Access & Credentials"
echo "=========================================================="
ARGOCD_IP=$(kubectl get svc argocd-server -n argocd -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending")
ARGOCD_PW=$(kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || echo "N/A")

echo ">> ArgoCD URL:      http://${ARGOCD_IP}"
echo ">> ArgoCD Username: admin"
echo ">> ArgoCD Password: ${ARGOCD_PW}"

echo ""
echo "=========================================================="
echo " 3. Grafana Monitoring Public Access & Credentials"
echo "=========================================================="
GRAFANA_IP=$(kubectl get svc kube-prometheus-stack-grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending")
GRAFANA_PW=$(kubectl get secret kube-prometheus-stack-grafana -n monitoring -o jsonpath="{.data.admin-password}" 2>/dev/null | base64 -d || echo "prom-operator")

echo ">> Grafana URL:      http://${GRAFANA_IP}"
echo ">> Grafana Username: admin"
echo ">> Grafana Password: ${GRAFANA_PW}"

echo ""
echo "=========================================================="
echo " 4. Prometheus Server Access"
echo "=========================================================="
echo ">> Access via Grafana Data Source: Pre-configured at http://${GRAFANA_IP}"
echo ">> Or Port-Forward in Cloud Shell:"
echo "   kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring --address 0.0.0.0"
echo "   (Use Cloud Shell Web Preview on port 9090)"
echo ">> Or Expose via Public LoadBalancer:"
echo "   kubectl patch svc kube-prometheus-stack-prometheus -n monitoring -p '{\"spec\": {\"type\": \"LoadBalancer\"}}'"

echo ""
echo "=========================================================="
echo " 5. Application Microservices (Namespace: aegis-apps)"
echo "=========================================================="
FRONTEND_IP=$(kubectl get svc frontend-service -n aegis-apps -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending")
echo ">> Frontend Storefront URL: http://${FRONTEND_IP}"
echo ""
echo ">> All Workloads Status in aegis-apps:"
kubectl get pods,svc,hpa,ingress -n aegis-apps -o wide 2>/dev/null || echo "Namespace aegis-apps not deployed yet."
echo ""
echo "=========================================================="
echo " Done!"
echo "=========================================================="
