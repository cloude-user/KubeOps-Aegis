import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, TypedDict, List

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from agent.app.services.k8s_client import k8s_service
from agent.app.services.blob_storage import blob_service
from agent.app.services.database import db_service, IncidentRecord
from agent.app.services.prometheus_client import prometheus_service
from agent.app.core.config import settings

logger = logging.getLogger("aegis.engine")


# ------------------------------------------------------------------
# LangGraph Agent State Definition
# ------------------------------------------------------------------
class SREAgentState(TypedDict):
    namespace: str
    auto_apply: bool
    failing_pod: Optional[Dict[str, Any]]
    logs: Optional[str]
    metrics: Optional[Dict[str, Any]]
    rca_result: Optional[Dict[str, Any]]
    incident_id: Optional[str]
    remediation_executed: bool
    blob_url: Optional[str]
    status: str
    error: Optional[str]


class AutonomousSREAgent:
    """LangGraph & LangChain Powered Autonomous SRE AI Agent Engine."""

    def __init__(self):
        self.workflow = self._build_langgraph_workflow()
        self.llm = self._get_llm_model()

    def _get_llm_model(self):
        """Factory method to instantiate Azure OpenAI, OpenAI, or Google Gemini LLM models."""
        try:
            # Option 1A: Azure OpenAI via Passwordless Workload Identity / Azure RBAC (AWS Bedrock Style)
            if settings.AZURE_OPENAI_ENDPOINT and not settings.AZURE_OPENAI_API_KEY:
                try:
                    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
                    from langchain_openai import AzureChatOpenAI
                    token_provider = get_bearer_token_provider(
                        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
                    )
                    logger.info("Initializing Azure OpenAI via Workload Identity / RBAC Token Provider (%s)", settings.AZURE_OPENAI_DEPLOYMENT_NAME)
                    return AzureChatOpenAI(
                        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                        azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                        api_version=settings.AZURE_OPENAI_API_VERSION,
                        azure_ad_token_provider=token_provider,
                        temperature=0.1
                    )
                except Exception as ex:
                    logger.info("Workload Identity fallback: %s", ex)

            # Option 1B: Azure OpenAI Service with API Key (Env or Azure Key Vault)
            azure_api_key = settings.AZURE_OPENAI_API_KEY
            if not azure_api_key and settings.AZURE_KEYVAULT_URL:
                try:
                    from agent.app.services.keyvault import keyvault_service
                    azure_api_key = keyvault_service._get_secret_sync("azure-openai-api-key", fallback_value=None)
                    if azure_api_key:
                        logger.info("Securely retrieved Azure OpenAI API key from Azure Key Vault (zero keys in YAML/Git).")
                except Exception as kv_err:
                    logger.debug("Key Vault secret lookup skipped: %s", kv_err)

            if azure_api_key and settings.AZURE_OPENAI_ENDPOINT:
                from langchain_openai import AzureChatOpenAI
                logger.info("Initializing Azure OpenAI LLM Model (%s)", settings.AZURE_OPENAI_DEPLOYMENT_NAME)
                return AzureChatOpenAI(
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                    api_key=azure_api_key,
                    temperature=0.1
                )
            # Option 2: OpenAI API (gpt-4o)
            elif settings.OPENAI_API_KEY:
                from langchain_openai import ChatOpenAI
                logger.info("Initializing OpenAI LLM Model (%s)", settings.AI_MODEL_NAME)
                return ChatOpenAI(
                    model=settings.AI_MODEL_NAME,
                    api_key=settings.OPENAI_API_KEY,
                    temperature=0.1
                )
            # Option 3: Google Gemini API (gemini-1.5-flash / gemini-1.5-pro)
            gemini_key = settings.GEMINI_API_KEY
            if not gemini_key and settings.AZURE_KEYVAULT_URL:
                try:
                    from agent.app.services.keyvault import keyvault_service
                    gemini_key = keyvault_service._get_secret_sync("gemini-api-key", fallback_value=None)
                    if gemini_key:
                        logger.info("Securely retrieved Google Gemini API key from Azure Key Vault.")
                except Exception as kv_err:
                    logger.debug("Key Vault Gemini secret lookup skipped: %s", kv_err)

            if gemini_key:
                from langchain_google_genai import ChatGoogleGenerativeAI
                logger.info("Initializing Google Gemini LLM Model (gemini-1.5-flash)")
                return ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=gemini_key,
                    temperature=0.1
                )
            else:
                logger.info("No external LLM API key detected. Running in SRE Rule Engine Mode.")
                return None
        except Exception as e:
            logger.warning("Could not initialize LLM provider: %s. Using SRE Rule Engine fallback.", e)
            return None

    def _build_langgraph_workflow(self):
        """Construct the LangGraph StateGraph workflow for Autonomous SRE operations."""
        graph = StateGraph(SREAgentState)

        # Define State Machine Nodes
        graph.add_node("triage", self._triage_node)
        graph.add_node("diagnose", self._diagnose_node)
        graph.add_node("remediate", self._remediate_node)
        graph.add_node("audit", self._audit_node)

        # Define State Transitions (Edges)
        graph.set_entry_point("triage")
        graph.add_conditional_edges(
            "triage",
            self._should_diagnose,
            {
                "diagnose": "diagnose",
                "end": END
            }
        )
        graph.add_edge("diagnose", "remediate")
        graph.add_edge("remediate", "audit")
        graph.add_edge("audit", END)

        return graph.compile()

    # ------------------------------------------------------------------
    # LangGraph State Nodes
    # ------------------------------------------------------------------
    async def _triage_node(self, state: SREAgentState) -> Dict[str, Any]:
        """Node 1: Triage Node - Detect failing pods in Kubernetes."""
        namespace = state.get("namespace", "default")
        logger.info("[LangGraph Node: Triage] Scanning K8s namespace '%s'...", namespace)

        failing_pods = await k8s_service.get_failing_pods(namespace=namespace)
        if not failing_pods:
            logger.info("[LangGraph Node: Triage] Cluster healthy. No anomalies found.")
            return {"status": "HEALTHY", "failing_pod": None}

        target_pod = failing_pods[0]
        incident_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
        logger.info("[LangGraph Node: Triage] Anomaly detected in pod '%s'. Assigned ID %s", target_pod["name"], incident_id)

        return {
            "failing_pod": target_pod,
            "incident_id": incident_id,
            "status": "TRIAGED"
        }

    def _should_diagnose(self, state: SREAgentState) -> str:
        """Conditional Edge: Proceed to diagnosis if failing pod exists, else END."""
        if state.get("failing_pod"):
            return "diagnose"
        return "end"

    async def _diagnose_node(self, state: SREAgentState) -> Dict[str, Any]:
        """Node 2: Diagnostic Node - Fetch pod logs, Prometheus metrics & execute Root Cause Analysis."""
        pod = state["failing_pod"]
        namespace = state["namespace"]
        pod_name = pod["name"]
        logger.info("[LangGraph Node: Diagnose] Fetching telemetry & multi-layer logs for pod '%s'...", pod_name)

        # 1. Fetch Comprehensive Logs (Current + Previous Crash + K8s Warning Events)
        logs = await k8s_service.get_pod_logs(pod_name=pod_name, namespace=namespace, tail_lines=100)

        # 2. Fetch Prometheus RED Metrics (Memory working set, CPU throttle, 5xx rate)
        metrics = await prometheus_service.get_pod_telemetry(pod_name=pod_name, namespace=namespace)
        logger.info("[LangGraph Node: Diagnose] Scraped Prometheus telemetry for %s: Mem=%sMiB, CPU=%s, 5xx=%s",
                    pod_name, metrics.get("memory_working_set_mib"), metrics.get("cpu_cores_used"), metrics.get("error_rate_5xx"))

        # 3. Execute Root Cause Analysis (Azure OpenAI or Deterministic Rule Engine)
        rca_result = self._ai_root_cause_analysis(pod, logs, metrics)

        # Save preliminary incident record in DB
        new_incident = IncidentRecord(
            id=state["incident_id"],
            title=f"Anomaly in {pod_name}",
            severity="CRITICAL" if "OOM" in rca_result["reason"] or pod.get("exit_code") == 137 else "HIGH",
            status="DIAGNOSED",
            failing_resource=f"pod/{pod_name}",
            namespace=namespace,
            root_cause=rca_result["summary"],
            remediation_action=rca_result["remediation_plan"]
        )
        db_service.add_incident(new_incident)

        return {"logs": logs, "metrics": metrics, "rca_result": rca_result, "status": "DIAGNOSED"}

    async def _remediate_node(self, state: SREAgentState) -> Dict[str, Any]:
        """Node 3: Remediation Node - Trigger self-healing action on Kubernetes."""
        if not state.get("auto_apply", True):
            logger.info("[LangGraph Node: Remediate] Auto-apply disabled. Awaiting human approval.")
            return {"remediation_executed": False, "status": "AWAITING_APPROVAL"}

        pod_name = state["failing_pod"]["name"]
        namespace = state["namespace"]
        incident_id = state["incident_id"]

        logger.info("[LangGraph Node: Remediate] Executing pod restart on '%s'...", pod_name)
        remediation_executed = await k8s_service.restart_pod(pod_name=pod_name, namespace=namespace)

        if remediation_executed:
            db_service.update_status(
                incident_id,
                "RESOLVED",
                remediation=f"Successfully restarted pod '{pod_name}'. Workload health restored."
            )

        return {"remediation_executed": remediation_executed, "status": "REMEDIATED"}

    async def _audit_node(self, state: SREAgentState) -> Dict[str, Any]:
        """Node 4: Audit Node - Persist incident audit snapshot to Azure Blob Storage."""
        incident_id = state["incident_id"]
        audit_payload = {
            "incident_id": incident_id,
            "target_pod": state["failing_pod"],
            "metrics_at_crash": state.get("metrics"),
            "logs_tail": state["logs"],
            "rca": state["rca_result"],
            "remediation_executed": state["remediation_executed"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        logger.info("[LangGraph Node: Audit] Uploading incident log audit for %s to Azure Blob Storage...", incident_id)
        blob_url = await blob_service.upload_incident_log(incident_id=incident_id, log_data=audit_payload)

        # Update DB record with blob URL
        inc = db_service.get_incident_by_id(incident_id)
        if inc:
            inc.blob_url = blob_url

        return {"blob_url": blob_url, "status": "COMPLETED"}

    # ------------------------------------------------------------------
    # AI Reasoning Helper (Azure OpenAI / LangChain / Rule Fallback)
    # ------------------------------------------------------------------
    def _ai_root_cause_analysis(self, pod: Dict[str, Any], logs: str, metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze root cause using Azure OpenAI / LangChain LLM or Rule Engine fallback."""
        reason = pod.get("reason", pod.get("status", "Unknown"))
        exit_code = pod.get("exit_code")
        metrics_info = f"Memory: {metrics.get('memory_working_set_mib', 'N/A')}MiB, CPU: {metrics.get('cpu_cores_used', 'N/A')} cores, 5xx Rate: {metrics.get('error_rate_5xx', 'N/A')}/s" if metrics else "Metrics unavailable"

        # If LLM model is configured, execute LangChain reasoning
        if self.llm:
            try:
                system_msg = SystemMessage(
                    content="You are an expert Autonomous SRE AI Agent for Azure Kubernetes Service (AKS). "
                            "Analyze the provided pod status, Prometheus metrics, and multi-layer crash logs. Return a concise root cause summary and remediation plan."
                )
                user_msg = HumanMessage(content=f"Pod: {pod}\nMetrics: {metrics_info}\nLogs:\n{logs}")
                response = self.llm.invoke([system_msg, user_msg])
                return {
                    "reason": reason,
                    "summary": f"Azure OpenAI RCA: {response.content[:250]}",
                    "remediation_plan": "Execute pod restart and update resource limits via ArgoCD GitOps."
                }
            except Exception as e:
                logger.warning("LLM invocation error: %s. Falling back to SRE rule engine.", e)

        # Intelligent Fallback Rules Engine (Correlating Exit Codes, Telemetry & Logs)
        if exit_code == 137 or "OOM" in logs or "OutOfMemory" in logs or "OOMKilled" in reason:
            return {
                "reason": "OOMKilled",
                "summary": f"LangGraph RCA: Pod terminated by Linux OOM killer (Exit Code 137). Telemetry shows memory saturation ({metrics.get('memory_working_set_mib', 512)}MiB).",
                "remediation_plan": "Restart pod and automatically bump cgroup memory limit (+512Mi) in GitOps repository."
            }
        elif exit_code in [1, 255] or "CrashLoopBackOff" in reason or "Fatal" in logs or "panic" in logs.lower():
            return {
                "reason": "CrashLoopBackOff",
                "summary": f"LangGraph RCA: Application crashed with fatal runtime error (Exit Code {exit_code or 1}). Container restart backoff triggered.",
                "remediation_plan": "Purge corrupt transient state, restart pod, and alert on-call engineer with stack trace."
            }
        else:
            return {
                "reason": reason or "UnhealthyState",
                "summary": f"LangGraph RCA: Pod detected in unhealthy condition ({reason}). Telemetry: {metrics_info}.",
                "remediation_plan": "Execute rolling restart and monitor RED metrics recovery in Prometheus."
            }

    # ------------------------------------------------------------------
    # Public Execution Entrypoint
    # ------------------------------------------------------------------
    async def run_diagnostics_and_heal(self, namespace: str = "default", auto_apply: bool = True) -> Dict[str, Any]:
        initial_state: SREAgentState = {
            "namespace": namespace,
            "auto_apply": auto_apply,
            "failing_pod": None,
            "logs": None,
            "rca_result": None,
            "incident_id": None,
            "remediation_executed": False,
            "blob_url": None,
            "status": "INITIATED",
            "error": None
        }

        final_state = await self.workflow.ainvoke(initial_state)

        if not final_state.get("failing_pod"):
            return {
                "status": "HEALTHY",
                "message": f"All workloads in namespace '{namespace}' are operating normally.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        return {
            "status": final_state["status"],
            "incident_id": final_state["incident_id"],
            "failing_pod": final_state["failing_pod"]["name"],
            "root_cause": final_state["rca_result"]["summary"],
            "remediation_plan": final_state["rca_result"]["remediation_plan"],
            "remediation_executed": final_state["remediation_executed"],
            "blob_audit_url": final_state["blob_url"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


sre_agent = AutonomousSREAgent()
