# KubeOps-Aegis: AKS Operations & Public Endpoints Access Guide

This guide contains the exact copy-pasteable commands for Azure Cloud Shell / Bash to login to the AKS cluster and access all public web interfaces (**ArgoCD**, **Grafana**, **Prometheus**, and **Aegis Commerce UI**).

---

## 1. Quick One-Line Script Execution

To automatically retrieve all cluster URLs and administrative passwords in one shot:

```bash
# In Azure Cloud Shell or Bash:
curl -sSL https://raw.githubusercontent.com/cloude-user/KubeOps-Aegis/main/scripts/aks_operations.sh | bash
```

Or run the local file directly:
```bash
bash scripts/aks_operations.sh
```

---

## 2. Step-by-Step Individual Commands

### Step 1: Login to AKS Cluster (Fix Expired Credentials)

```bash
az aks get-credentials \
  --resource-group kubeops-aegis-rg-compute-prd \
  --name aks-kubeops-aegis-prd \
  --admin \
  --overwrite-existing
```

**Verify connection:**
```bash
kubectl get nodes
```


---

### Step 2: Access ArgoCD GitOps UI

#### A. Get ArgoCD Public External IP:
```bash
kubectl get svc argocd-server -n argocd -o jsonpath='{.status.loadBalancer.ingress[0].ip}'; echo
```

#### B. Get ArgoCD Admin Password:
```bash
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d; echo
```

#### C. Access URL:
* **Browser URL:** `http://<ARGOCD-EXTERNAL-IP>`
* **Username:** `admin`
* **Password:** *(Output from command B)*

---

### Step 3: Access Grafana Monitoring Dashboard

#### A. Get Grafana Public External IP:
```bash
kubectl get svc kube-prometheus-stack-grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}'; echo
```

#### B. Get Grafana Admin Password:
```bash
kubectl get secret kube-prometheus-stack-grafana -n monitoring -o jsonpath="{.data.admin-password}" | base64 -d; echo
```

#### C. Access URL:
* **Browser URL:** `http://<GRAFANA-EXTERNAL-IP>`
* **Username:** `admin`
* **Password:** *(Output from command B)*

---

### Step 4: Access Prometheus Server

#### Option A: Built-in inside Grafana (Recommended - Zero Setup)
Prometheus is already connected as the default datasource in Grafana. Go to **Explore** inside Grafana to write PromQL queries.

#### Option B: Cloud Shell Port-Forward
```bash
kubectl port-forward svc/kube-prometheus-stack-prometheus 9090:9090 -n monitoring --address 0.0.0.0
```
In Azure Cloud Shell, click **Web Preview (top right)** $\rightarrow$ **Configure Port** $\rightarrow$ `9090` $\rightarrow$ **Open and Browse**.

#### Option C: Expose via Azure Public Load Balancer
```bash
# Convert Prometheus service to LoadBalancer:
kubectl patch svc kube-prometheus-stack-prometheus -n monitoring -p '{"spec": {"type": "LoadBalancer"}}'

# Retrieve Public IP:
kubectl get svc kube-prometheus-stack-prometheus -n monitoring -w
```
Open `http://<PROMETHEUS-EXTERNAL-IP>:9090` in your browser.

---

### Step 5: Check Application Microservices in `aegis-apps`

#### A. View Pods, Services, HPA, and Ingress:
```bash
kubectl get pods,svc,hpa,ingress -n aegis-apps -o wide
```

#### B. Get Storefront Frontend Public URL:
```bash
kubectl get svc frontend-service -n aegis-apps -o jsonpath='{.status.loadBalancer.ingress[0].ip}'; echo
```
Open `http://<FRONTEND-EXTERNAL-IP>/` in your browser to test the e-commerce store!

#### C. View Backend Real-time Logs:
```bash
kubectl logs -l app=backend-api -n aegis-apps -f --tail=100
```

#### D. View Frontend Nginx Logs:
```bash
kubectl logs -l app=frontend-ui -n aegis-apps -f --tail=100
```

---

### Step 6: Trigger ArgoCD Sync Manually (Optional)

```bash
# Trigger immediate GitOps sync:
kubectl patch application kubeops-aegis-workloads -n argocd --type merge -p '{"operation":{"sync":{"prune":true}}}'
```
