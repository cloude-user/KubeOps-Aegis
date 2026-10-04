from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from agent.app.core.security import get_current_user, TokenData
from agent.app.services.k8s_client import k8s_service
from agent.app.services.keyvault import keyvault_service
from agent.app.services.blob_storage import blob_service
from agent.app.services.database import db_service, IncidentRecord
from agent.app.engine.sre_agent import sre_agent
from agent.app.core.config import settings

router = APIRouter()


class HealRequest(BaseModel):
    namespace: str = "default"
    auto_apply: bool = True


@router.get("/health", tags=["System"])
async def system_health():
    """Service health probe for K8s liveness & readiness."""
    return {
        "status": "UP",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "2.0.0",
        "integrations": {
            "azure_keyvault": bool(settings.AZURE_KEYVAULT_URL),
            "azure_storage": bool(settings.AZURE_STORAGE_ACCOUNT_NAME),
            "kubernetes_mode": "In-Cluster" if settings.KUBERNETES_IN_CLUSTER else "Local/Config"
        }
    }


@router.get("/cluster/nodes", tags=["Kubernetes"])
async def list_nodes(current_user: TokenData = Depends(get_current_user)):
    """List cluster node status and health asynchronously."""
    return await k8s_service.get_cluster_nodes()


@router.get("/cluster/pods/failing", tags=["Kubernetes"])
async def list_failing_pods(
    namespace: str = "default",
    current_user: TokenData = Depends(get_current_user)
):
    """List failing or unstable pods in a namespace asynchronously."""
    return await k8s_service.get_failing_pods(namespace=namespace)


@router.get("/incidents", response_model=List[IncidentRecord], tags=["Incidents"])
async def get_incident_history(current_user: TokenData = Depends(get_current_user)):
    """Retrieve SRE incident and auto-healing history."""
    return db_service.get_all_incidents()


@router.post("/sre/heal", tags=["Autonomous SRE"])
async def trigger_autonomous_healing(
    request: HealRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Trigger the Autonomous SRE Agent to diagnose and heal failing workloads asynchronously."""
    result = await sre_agent.run_diagnostics_and_heal(
        namespace=request.namespace,
        auto_apply=request.auto_apply
    )
    return result


@router.get("/azure/keyvault/secret", tags=["Azure Integrations"])
async def get_keyvault_secret(
    secret_name: str = Query(..., description="Name of secret in Azure Key Vault"),
    current_user: TokenData = Depends(get_current_user)
):
    """Fetch secret status from Azure Key Vault asynchronously."""
    value = await keyvault_service.get_secret(secret_name, fallback_value="[REDACTED_DEMO_SECRET]")
    return {"secret_name": secret_name, "retrieved": bool(value), "status": "SECURE"}


@router.get("/azure/storage/blobs", tags=["Azure Integrations"])
async def list_storage_blobs(current_user: TokenData = Depends(get_current_user)):
    """List incident audit logs saved in Azure Blob Storage asynchronously."""
    blobs = await blob_service.list_incident_logs()
    return {"container": settings.AZURE_STORAGE_CONTAINER, "total_blobs": len(blobs), "blobs": blobs}
