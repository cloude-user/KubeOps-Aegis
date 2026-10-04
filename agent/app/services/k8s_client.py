import asyncio
import logging
from typing import Dict, Any, List, Optional
from kubernetes import client, config
from agent.app.core.config import settings

logger = logging.getLogger("aegis.k8s")


class KubernetesService:
    def __init__(self):
        self._core_v1: Optional[client.CoreV1Api] = None
        self._apps_v1: Optional[client.AppsV1Api] = None
        self._is_initialized = False

    def initialize(self):
        if self._is_initialized:
            return
        try:
            if settings.KUBERNETES_IN_CLUSTER:
                config.load_incluster_config()
                logger.info("Loaded in-cluster Kubernetes configuration.")
            else:
                config.load_kube_config(config_file=settings.KUBECONFIG_PATH)
                logger.info("Loaded kubeconfig from: %s", settings.KUBECONFIG_PATH)

            self._core_v1 = client.CoreV1Api()
            self._apps_v1 = client.AppsV1Api()
            self._is_initialized = True
        except Exception as e:
            logger.warning("Failed to load Kubernetes configuration (running in simulation mode): %s", e)

    def _get_cluster_nodes_sync(self) -> List[Dict[str, Any]]:
        self.initialize()
        if not self._core_v1:
            return [
                {"name": "aks-system-node-01", "status": "Ready", "cpu": "18%", "memory": "42%", "role": "control-plane"},
                {"name": "aks-user-node-01", "status": "Ready", "cpu": "64%", "memory": "78%", "role": "worker"},
                {"name": "aks-user-node-02", "status": "Ready", "cpu": "55%", "memory": "61%", "role": "worker"},
            ]
        try:
            nodes = self._core_v1.list_node()
            result = []
            for n in nodes.items:
                status = "Ready" if any(c.type == "Ready" and c.status == "True" for c in n.status.conditions) else "NotReady"
                result.append({
                    "name": n.metadata.name,
                    "status": status,
                    "version": n.status.node_info.kubelet_version,
                    "os": n.status.node_info.os_image
                })
            return result
        except Exception as e:
            logger.error("Error fetching cluster nodes: %s", e)
            return []

    def _get_failing_pods_sync(self, namespace: str) -> List[Dict[str, Any]]:
        self.initialize()
        if not self._core_v1:
            return [
                {
                    "name": "payment-api-78f994c65d-x89zk",
                    "namespace": namespace,
                    "status": "CrashLoopBackOff",
                    "restarts": 14,
                    "container": "payment-service",
                    "exit_code": 137,
                    "reason": "OOMKilled: Container exceeded memory limit 512Mi"
                }
            ]
        try:
            pods = self._core_v1.list_namespaced_pod(namespace)
            failing = []
            for p in pods.items:
                phase = p.status.phase
                restarts = sum(cs.restart_count for cs in (p.status.container_statuses or []))
                
                # Check container termination state (OOMKilled, Error, CrashLoop)
                exit_code = None
                term_reason = None
                container_name = None
                is_crashed = False

                for cs in (p.status.container_statuses or []):
                    container_name = cs.name
                    if cs.last_state and cs.last_state.terminated:
                        exit_code = cs.last_state.terminated.exit_code
                        term_reason = cs.last_state.terminated.reason
                        if exit_code in [137, 139, 1, 255] or term_reason in ["OOMKilled", "Error"]:
                            is_crashed = True
                    if cs.state and cs.state.waiting:
                        waiting_reason = cs.state.waiting.reason
                        if waiting_reason in ["CrashLoopBackOff", "ImagePullBackOff", "CreateContainerConfigError"]:
                            is_crashed = True
                            term_reason = waiting_reason

                if phase != "Running" or restarts > 0 or is_crashed:
                    failing.append({
                        "name": p.metadata.name,
                        "namespace": namespace,
                        "status": term_reason or phase,
                        "restarts": restarts,
                        "container": container_name,
                        "exit_code": exit_code,
                        "reason": f"{term_reason or phase} (Exit Code: {exit_code}, Restarts: {restarts})",
                        "node": p.spec.node_name
                    })
            return failing
        except Exception as e:
            logger.error("Error checking failing pods in namespace '%s': %s", namespace, e)
            return []

    def _get_pod_logs_sync(self, pod_name: str, namespace: str, tail_lines: int = 100) -> str:
        """Fetch complete multi-layer diagnostic logs: Current logs + Previous container crash logs + K8s Events."""
        self.initialize()
        if not self._core_v1:
            return (
                f"[COMPREHENSIVE TELEMETRY & LOG DUMP - {pod_name}]\n"
                "--- [1. PREVIOUS CRASH LOG (Exit Code 137)] ---\n"
                "2026-10-04T10:14:02Z [INFO] Processing batch checkout order payload...\n"
                "2026-10-04T10:14:05Z [ERROR] Memory consumption reached 99.8% of 512Mi cgroup limit.\n"
                "2026-10-04T10:14:06Z [FATAL] Linux Kernel OOM killer invoked. Process killed with signal SIGKILL (exit code 137).\n"
                "--- [2. CURRENT CONTAINER RESTART LOG] ---\n"
                "2026-10-04T10:14:10Z [INFO] Starting service up after restart (attempt 1)...\n"
                "--- [3. KUBERNETES POD WARNING EVENTS] ---\n"
                "Warning  OOMKilling  pod/payment-api  Memory cgroup out of memory: Killed process 412 (python)\n"
                "Warning  BackOff     pod/payment-api  Back-off restarting failed container\n"
            )

        log_sections = []

        # 1. Fetch Previous Terminated Container Log (if container crashed and restarted)
        try:
            prev_logs = self._core_v1.read_namespaced_pod_log(
                name=pod_name, namespace=namespace, tail_lines=tail_lines, previous=True
            )
            if prev_logs:
                log_sections.append(f"=== [PREVIOUS CRASHED CONTAINER LOG (Fatal Terminated Session)] ===\n{prev_logs}\n")
        except Exception as e:
            log_sections.append(f"[Previous container logs unavailable: {e}]")

        # 2. Fetch Current Running/Restarting Container Log
        try:
            curr_logs = self._core_v1.read_namespaced_pod_log(
                name=pod_name, namespace=namespace, tail_lines=tail_lines, previous=False
            )
            if curr_logs:
                log_sections.append(f"=== [CURRENT RUNNING CONTAINER LOG (Post-Restart)] ===\n{curr_logs}\n")
        except Exception as e:
            log_sections.append(f"[Current container logs unavailable: {e}]")

        # 3. Fetch Kubernetes Warning Events for this Pod
        try:
            events = self._core_v1.list_namespaced_event(
                namespace=namespace,
                field_selector=f"involvedObject.name={pod_name}"
            )
            warning_events = [f"[{e.type}] {e.reason}: {e.message} (x{e.count})" for e in events.items if e.type == "Warning"]
            if warning_events:
                log_sections.append(f"=== [KUBERNETES WARNING EVENTS] ===\n" + "\n".join(warning_events))
        except Exception as e:
            logger.warning("Could not fetch events for pod '%s': %s", pod_name, e)

        return "\n\n".join(log_sections)

    def _restart_pod_sync(self, pod_name: str, namespace: str) -> bool:
        self.initialize()
        if not self._core_v1:
            logger.info("[SIMULATION] Restarted pod '%s' in namespace '%s'.", pod_name, namespace)
            return True
        try:
            self._core_v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
            logger.info("Successfully deleted pod '%s' to trigger restart.", pod_name)
            return True
        except Exception as e:
            logger.error("Failed to restart pod '%s': %s", pod_name, e)
            return False

    async def get_cluster_nodes(self) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_cluster_nodes_sync)

    async def get_failing_pods(self, namespace: str = "default") -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_failing_pods_sync, namespace)

    async def get_pod_logs(self, pod_name: str, namespace: str = "default", tail_lines: int = 100) -> str:
        return await asyncio.to_thread(self._get_pod_logs_sync, pod_name, namespace, tail_lines)

    async def restart_pod(self, pod_name: str, namespace: str = "default") -> bool:
        return await asyncio.to_thread(self._restart_pod_sync, pod_name, namespace)


k8s_service = KubernetesService()
