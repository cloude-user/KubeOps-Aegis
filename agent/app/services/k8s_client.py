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
                    "reason": "OOMKilled: Memory limit 512Mi exceeded"
                }
            ]
        try:
            pods = self._core_v1.list_namespaced_pod(namespace)
            failing = []
            for p in pods.items:
                phase = p.status.phase
                restarts = sum(cs.restart_count for cs in (p.status.container_statuses or []))
                if phase != "Running" or restarts > 5:
                    failing.append({
                        "name": p.metadata.name,
                        "namespace": namespace,
                        "status": phase,
                        "restarts": restarts,
                        "node": p.spec.node_name
                    })
            return failing
        except Exception as e:
            logger.error("Error checking failing pods in namespace '%s': %s", namespace, e)
            return []

    def _get_pod_logs_sync(self, pod_name: str, namespace: str, tail_lines: int) -> str:
        self.initialize()
        if not self._core_v1:
            return (
                f"[LOG DUMP - {pod_name}]\n"
                "2026-10-01T21:40:01Z [INFO] Initializing Payment Service v2.4...\n"
                "2026-10-01T21:40:05Z [ERROR] java.lang.OutOfMemoryError: Java heap space\n"
                "2026-10-01T21:40:06Z [FATAL] Terminating process due to unhandled OOMKilled signal.\n"
            )
        try:
            return self._core_v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=tail_lines)
        except Exception as e:
            logger.error("Failed to fetch pod logs for '%s': %s", pod_name, e)
            return f"Error retrieving logs: {str(e)}"

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
