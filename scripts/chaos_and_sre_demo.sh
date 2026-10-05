#!/usr/bin/env bash
# ==============================================================================
# KubeOps-Aegis: Production SRE Chaos Engineering & Autonomous Healing Suite
# Works from Azure Cloud Shell, Linux VMs, or any Kubernetes terminal
# ==============================================================================

set -eo pipefail

NAMESPACE="aegis-apps"
AGENT_APP_LABEL="app=kubeops-aegis-agent"
BACKEND_APP_LABEL="app=backend-api"

# Color Codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ------------------------------------------------------------------------------
# Helper: Print Banners
# ------------------------------------------------------------------------------
banner() {
  echo -e "\n${BLUE}==================================================================${NC}"
  echo -e "${CYAN}  $1${NC}"
  echo -e "${BLUE}==================================================================${NC}\n"
}

# ------------------------------------------------------------------------------
# Helper: Auto-Discover Endpoints
# ------------------------------------------------------------------------------
discover_endpoints() {
  echo -e "${YELLOW}>> Discovering cluster endpoints in namespace '${NAMESPACE}'...${NC}"
  
  FRONTEND_IP=$(kubectl get svc frontend-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
  if [ -z "$FRONTEND_IP" ]; then
    FRONTEND_IP="20.24.117.161"
    echo -e "   [Notice] Could not resolve frontend IP via jsonpath, defaulting to: ${FRONTEND_IP}"
  else
    echo -e "   [Found] Storefront Frontend Public IP: ${GREEN}http://${FRONTEND_IP}${NC}"
  fi

  AGENT_POD=$(kubectl get pods -n ${NAMESPACE} -l ${AGENT_APP_LABEL} -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
  if [ -z "$AGENT_POD" ]; then
    echo -e "${RED}   [Warning] SRE Agent pod not found with label ${AGENT_APP_LABEL} in ${NAMESPACE}${NC}"
  else
    echo -e "   [Found] SRE Agent Pod: ${GREEN}${AGENT_POD}${NC}"
  fi

  BACKEND_POD=$(kubectl get pods -n ${NAMESPACE} -l ${BACKEND_APP_LABEL} -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
  if [ -n "$BACKEND_POD" ]; then
    echo -e "   [Found] Backend API Pod: ${GREEN}${BACKEND_POD}${NC}"
  fi
  echo ""
}

# ------------------------------------------------------------------------------
# Scenario 1: Database Query Timeout / Deadlock
# ------------------------------------------------------------------------------
run_scenario_db_timeout() {
  banner "SCENARIO 1: PostgreSQL Connection Pool Deadlock & Query Timeout"
  echo -e "${YELLOW}Description:${NC} Simulates an unindexed query lock in PostgreSQL holding connections for 15s."
  echo -e "${YELLOW}Target URL:${NC}  http://${FRONTEND_IP}/api/v1/chaos/db-query-timeout\n"
  
  echo -e ">> Sending request (waiting for 15s lock wait timeout)..."
  HTTP_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}\nTIME_TOTAL:%{time_total}s\n" http://${FRONTEND_IP}/api/v1/chaos/db-query-timeout || true)
  echo "$HTTP_RESPONSE"
  
  echo -e "\n>> Verifying Prometheus Metric increment:"
  curl -s http://${FRONTEND_IP}/metrics | grep "db_query_timeouts_total" || echo "Metric not yet scraped"
  echo -e "\n${GREEN}✔ Scenario 1 completed successfully.${NC}"
}

# ------------------------------------------------------------------------------
# Scenario 2: Downstream Payment Gateway Timeout
# ------------------------------------------------------------------------------
run_scenario_gateway_timeout() {
  banner "SCENARIO 2: Downstream Payment Gateway Socket Timeout"
  echo -e "${YELLOW}Description:${NC} Simulates a 10s socket read hang to external payment-gateway.azure.internal."
  echo -e "${YELLOW}Target URL:${NC}  http://${FRONTEND_IP}/api/v1/chaos/http-request-timeout\n"

  echo -e ">> Sending request (waiting for 10s socket timeout)..."
  HTTP_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}\nTIME_TOTAL:%{time_total}s\n" http://${FRONTEND_IP}/api/v1/chaos/http-request-timeout || true)
  echo "$HTTP_RESPONSE"

  echo -e "\n>> Verifying Prometheus Metric increment:"
  curl -s http://${FRONTEND_IP}/metrics | grep "http_request_timeouts_total" || echo "Metric not yet scraped"
  echo -e "\n${GREEN}✔ Scenario 2 completed successfully.${NC}"
}

# ------------------------------------------------------------------------------
# Scenario 3: CPU Burn & Horizontal Pod Autoscaler (HPA)
# ------------------------------------------------------------------------------
run_scenario_cpu_burn() {
  banner "SCENARIO 3: CPU Burn -> Horizontal Pod Autoscaler (HPA) Trigger"
  echo -e "${YELLOW}Description:${NC} Computes prime numbers up to 500,000 to spike CPU past 75% threshold."
  echo -e "${YELLOW}Target URL:${NC}  http://${FRONTEND_IP}/api/v1/chaos/cpu-burn\n"

  echo -e ">> Checking HPA baseline state:"
  kubectl get hpa backend-api-hpa -n ${NAMESPACE} 2>/dev/null || echo "HPA backend-api-hpa not deployed"

  echo -e "\n>> Triggering heavy prime computation loop..."
  HTTP_RESPONSE=$(curl -s -X POST http://${FRONTEND_IP}/api/v1/chaos/cpu-burn || true)
  echo "$HTTP_RESPONSE"

  echo -e "\n>> HPA Status after load:"
  kubectl get hpa backend-api-hpa -n ${NAMESPACE} 2>/dev/null || true
  echo -e "\n${GREEN}✔ Scenario 3 completed. (Run 'kubectl get hpa -n aegis-apps -w' to watch replica scaling)${NC}"
}

# ------------------------------------------------------------------------------
# Scenario 4: Memory Leak -> OOMKilled -> Autonomous SRE Self-Healing
# ------------------------------------------------------------------------------
run_scenario_oom_healing() {
  banner "SCENARIO 4: Memory Leak -> OOMKilled -> LangGraph SRE Autonomous Healing"
  echo -e "${YELLOW}Description:${NC} Allocates 150MB chunks until cgroup 512MB limit triggers OOMKilled (Exit 137)."
  echo -e "${YELLOW}Target URL:${NC}  http://${FRONTEND_IP}/api/v1/chaos/oom-leak\n"

  echo -e ">> Current pod state:"
  kubectl get pods -n ${NAMESPACE}

  echo -e "\n>> Sending 5 consecutive memory leak allocations (150MB each)..."
  for i in {1..5}; do
    echo -n "   Burst #$i: "
    RES=$(curl -s -X POST http://${FRONTEND_IP}/api/v1/chaos/oom-leak || echo "Connection severed by OOM")
    echo "$RES"
    sleep 0.5
  done

  echo -e "\n>> Pod status post-bursts (checking for OOM / restart):"
  kubectl get pods -n ${NAMESPACE} -l ${BACKEND_APP_LABEL}

  echo -e "\n>> Triggering Autonomous SRE Agent Diagnosis & Healing Node Pipeline..."
  if [ -n "$AGENT_POD" ]; then
    kubectl exec -it ${AGENT_POD} -n ${NAMESPACE} -- bash -c '
      TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token -d "username=admin&password=AegisSre2026!" | grep -o "\"access_token\":\"[^\"]*" | cut -d"\"" -f4)
      curl -s -X POST http://localhost:8000/api/v1/sre/heal \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"namespace\": \"aegis-apps\", \"auto_apply\": true}"
    '
  else
    echo -e "${RED}Agent pod not found. Please verify deployment in ${NAMESPACE}.${NC}"
  fi
  echo -e "\n${GREEN}✔ Scenario 4 completed.${NC}"
}

# ------------------------------------------------------------------------------
# Status Dashboard
# ------------------------------------------------------------------------------
show_status() {
  banner "CURRENT CLUSTER & SRE STATUS (${NAMESPACE})"
  echo -e "${CYAN}>> Kubernetes Pods:${NC}"
  kubectl get pods -n ${NAMESPACE} -o wide

  echo -e "\n${CYAN}>> Kubernetes Services & LoadBalancers:${NC}"
  kubectl get svc -n ${NAMESPACE}

  echo -e "\n${CYAN}>> Horizontal Pod Autoscalers:${NC}"
  kubectl get hpa -n ${NAMESPACE} 2>/dev/null || echo "No HPAs found"

  echo -e "\n${CYAN}>> Node Resource Allocations:${NC}"
  kubectl describe nodes | grep -A 8 "Allocated resources:" || true
}

# ------------------------------------------------------------------------------
# Stream Agent Logs
# ------------------------------------------------------------------------------
stream_agent_logs() {
  banner "STREAMING SRE AGENT LOGS (Ctrl+C to stop)"
  if [ -n "$AGENT_POD" ]; then
    kubectl logs -n ${NAMESPACE} ${AGENT_POD} -f --tail=100
  else
    echo -e "${RED}Agent pod not found.${NC}"
  fi
}

# ------------------------------------------------------------------------------
# Interactive Menu
# ------------------------------------------------------------------------------
menu() {
  discover_endpoints

  while true; do
    echo -e "${PURPLE}==================================================================${NC}"
    echo -e "${YELLOW}           KubeOps-Aegis: Live SRE Chaos & Healing Menu          ${NC}"
    echo -e "${PURPLE}==================================================================${NC}"
    echo -e "  ${GREEN}1)${NC} Test Scenario 1: PostgreSQL Connection Pool Deadlock (504 Timeout)"
    echo -e "  ${GREEN}2)${NC} Test Scenario 2: Downstream Payment Gateway Socket Timeout (504)"
    echo -e "  ${GREEN}3)${NC} Test Scenario 3: CPU Burn Loop -> Trigger HPA Auto-Scaling"
    echo -e "  ${GREEN}4)${NC} Test Scenario 4: OOM Memory Leak -> SRE Agent Autonomous Healing"
    echo -e "  ${GREEN}5)${NC} Run Full Automated Suite (Scenarios 1 through 4 sequentially)"
    echo -e "  ${GREEN}6)${NC} Display Current Pods, HPA & Node Resource Status"
    echo -e "  ${GREEN}7)${NC} Stream Live SRE AI Agent Console Logs"
    echo -e "  ${GREEN}q)${NC} Quit"
    echo -e "${PURPLE}------------------------------------------------------------------${NC}"
    read -rp "Select an option [1-7 or q]: " choice

    case "$choice" in
      1) run_scenario_db_timeout ;;
      2) run_scenario_gateway_timeout ;;
      3) run_scenario_cpu_burn ;;
      4) run_scenario_oom_healing ;;
      5)
        run_scenario_db_timeout
        sleep 2
        run_scenario_gateway_timeout
        sleep 2
        run_scenario_cpu_burn
        sleep 2
        run_scenario_oom_healing
        ;;
      6) show_status ;;
      7) stream_agent_logs ;;
      q|Q) echo -e "\nExiting. Stay resilient!\n"; exit 0 ;;
      *) echo -e "${RED}Invalid option. Please choose 1-7 or q.${NC}\n" ;;
    esac
    echo ""
  done
}

# Handle command-line arguments if provided
case "${1:-}" in
  --scenario-1|--db) discover_endpoints; run_scenario_db_timeout ;;
  --scenario-2|--gateway) discover_endpoints; run_scenario_gateway_timeout ;;
  --scenario-3|--cpu) discover_endpoints; run_scenario_cpu_burn ;;
  --scenario-4|--oom) discover_endpoints; run_scenario_oom_healing ;;
  --all)
    discover_endpoints
    run_scenario_db_timeout
    run_scenario_gateway_timeout
    run_scenario_cpu_burn
    run_scenario_oom_healing
    ;;
  --status) discover_endpoints; show_status ;;
  --logs) discover_endpoints; stream_agent_logs ;;
  *) menu ;;
esac
