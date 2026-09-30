# ⚡ KubeOps-Aegis (Azure): Autonomous Self-Healing Kubernetes & GitOps Agent

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_State_Machine-00f2fe?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![Kubernetes](https://img.shields.io/badge/AKS-Azure_Kubernetes-0089D6?style=for-the-badge&logo=microsoftazure&logoColor=white)](https://azure.microsoft.com)
[![ArgoCD](https://img.shields.io/badge/ArgoCD-GitOps_Auto_Sync-EF7B4D?style=for-the-badge&logo=argo&logoColor=white)](https://argoproj.github.io/argo-cd/)
[![Terraform](https://img.shields.io/badge/Terraform-Azure_AKS_IaC-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)](https://terraform.io)
[![Prometheus](https://img.shields.io/badge/Prometheus-AlertManager-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)](https://prometheus.io)

**KubeOps-Aegis (Azure Edition)** is an enterprise-grade **Autonomous SRE & GitOps AI Agent** engineered for production **Azure Kubernetes Service (AKS 1.30+)** environments.

---

## 🏛️ Azure Architecture & Flow

```mermaid
flowchart TD
    subgraph AKSCluster["1. Azure Kubernetes Service (AKS 1.30+)"]
        Pods["Microservice Pods (payment-service)"] -->|OOM / CrashLoop / Throttling| Prom["Prometheus AlertManager"]
    end

    subgraph Ingestion["2. Webhook & Ingestion Layer"]
        Prom -->|HTTP POST Webhook| Ingest["FastAPI Alert Ingestor"]
        UIChaos["Web Dashboard"] -->|API POST /chaos/trigger| Ingest
    end

    subgraph LangGraphEngine["3. LangGraph Multi-Agent State Machine"]
        Ingest --> Triage["Triage Agent"]
        Triage --> Diagnostic["Diagnostic Agent (AKS Logs & PromQL)"]
        Diagnostic --> Remediation["Remediation Agent (Resource Bump)"]
        Remediation --> GitOpsAgent["GitOps PR Agent (Unified Diff)"]
    end

    subgraph HITL["4. Human-In-The-Loop Guardrail"]
        GitOpsAgent --> HITLCheck{"Web Dashboard Sign-Off"}
        HITLCheck -->|Approved| ApplyNode["Apply Patch to Git Repo"]
    end

    subgraph Reconciliation["5. Declarative Reconciliation"]
        ApplyNode --> GitRepo["GitOps Repo / values.yaml"]
        GitRepo -->|Auto Sync| ArgoCD["ArgoCD Controller"]
        ArgoCD -->|Reconciles AKS State| Pods
    end
```

---

## 🔒 Azure Security Protocols & Networking Highlights

1. **Dedicated Subnet Isolation**: AKS system and user node pools run in isolated private subnets (`10.100.1.0/24` and `10.100.2.0/24`).
2. **Azure NAT Gateway**: Outbound egress is routed through an **Azure Standard NAT Gateway** with static Public IP.
3. **Network Security Group (NSG)**: Enforces strict inbound rules (`AllowHTTPSInbound`, `AllowVNetInbound`, `DenyAllInbound`).
4. **Azure Workload Identity**: Uses federated OIDC credentials mapping Kubernetes ServiceAccount (`default:kubeops-agent-sa`) to Azure Managed Identity.
5. **Azure Container Registry (ACR)**: Configured with `AcrPull` role binding to AKS Kubelet Managed Identity.

---

## 📂 Repository Structure

```
KubeOps-Aegis/
├── agent/                         # Python AI Agent (LangGraph + FastAPI + K8s API)
│   ├── app/
│   │   ├── agents/                # Triage, Diagnostic, Remediation, GitOps, PostMortem agents
│   │   ├── api/                   # FastAPI routes & WebSocket manager
│   │   ├── core/                  # Settings (Azure/AWS), state schemas, LLM factory
│   │   ├── graph/                 # LangGraph State Machine compilation
│   │   ├── tools/                 # AKS / EKS K8s tools, Prometheus PromQL, Git tools
│   │   └── main.py                # Agent daemon entrypoint
│   ├── tests/                     # Pytest suite
│   └── requirements.txt
├── web/                           # Real-Time Glassmorphism SRE Dashboard
├── k8s/                           # PrometheusRules, AlertManager config, Chaos tools
├── gitops/                        # GitOps Application Helm chart & ArgoCD CRDs
├── terraform/                     # Production Azure AKS Infrastructure (RG, VNet, NAT, NSG, AKS, ACR)
│   ├── main.tf                    # Resource Group, VNet, Subnets, NAT Gateway, NSG
│   ├── aks.tf                     # AKS 1.30+ CNI Overlay cluster & Node Pools
│   ├── identity.tf                # Azure Workload Identity & Federated Credentials
│   ├── acr.tf                     # Azure Container Registry & AcrPull RBAC
│   ├── argocd.tf                  # ArgoCD Helm deployment
│   ├── prometheus.tf              # Prometheus Stack Helm deployment
│   └── env/prd.tfvars             # Production Azure tfvars
├── scripts/                       # Run & Demo Scripts
│   ├── run_agent.ps1              # Agent daemon launcher
│   └── simulate_incident.py       # Interactive CLI simulator
└── README.md
```

---

## 🚀 Azure AKS Deployment Guide

```bash
# 1. Log in to Azure CLI
az login

# 2. Deploy Azure Infrastructure via Terraform
cd terraform
terraform init
terraform apply -var-file="env/prd.tfvars" -auto-approve

# 3. Connect kubectl to AKS
$(terraform output -raw kubeconfig_command)

# 4. Run the Agent Backend
cd ../agent
pip install -r requirements.txt
python -m agent.app.main
```
