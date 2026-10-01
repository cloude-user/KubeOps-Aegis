import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("aegis.database")


class IncidentRecord(BaseModel):
    id: str
    title: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    status: str    # DETECTED, ANALYZING, REMEDIATING, RESOLVED
    failing_resource: str
    namespace: str = "default"
    root_cause: str
    remediation_action: str
    blob_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# In-memory store initialized with realistic incident history
_INCIDENT_STORE: List[IncidentRecord] = [
    IncidentRecord(
        id="INC-2026-0901",
        title="OOMKilled in payment-api deployment",
        severity="CRITICAL",
        status="RESOLVED",
        failing_resource="pod/payment-api-78f994c65d-x89zk",
        namespace="default",
        root_cause="Java Heap Memory leak during peak billing batch cycle.",
        remediation_action="Increased memory limit from 512Mi to 1024Mi and restarted pod.",
        blob_url="https://kubeopsaegisstprd.blob.core.windows.net/incident-logs/incidents/20260929_INC-2026-0901.json"
    ),
    IncidentRecord(
        id="INC-2026-0902",
        title="Ingress NGINX SSL Cert Renewal Failure",
        severity="HIGH",
        status="RESOLVED",
        failing_resource="ingress/aegis-api-ingress",
        namespace="ingress-nginx",
        root_cause="Key Vault Certificate sync timeout.",
        remediation_action="Triggered Key Vault Secret sync and re-issued ingress TLS secret.",
        blob_url="https://kubeopsaegisstprd.blob.core.windows.net/incident-logs/incidents/20260930_INC-2026-0902.json"
    )
]


class DatabaseService:
    def get_all_incidents(self) -> List[IncidentRecord]:
        return _INCIDENT_STORE

    def get_incident_by_id(self, incident_id: str) -> Optional[IncidentRecord]:
        for inc in _INCIDENT_STORE:
            if inc.id == incident_id:
                return inc
        return None

    def add_incident(self, incident: IncidentRecord) -> IncidentRecord:
        _INCIDENT_STORE.insert(0, incident)
        logger.info(f"Recorded new incident: {incident.id} - {incident.title}")
        return incident

    def update_status(self, incident_id: str, new_status: str, remediation: Optional[str] = None) -> Optional[IncidentRecord]:
        inc = self.get_incident_by_id(incident_id)
        if inc:
            inc.status = new_status
            if remediation:
                inc.remediation_action = remediation
        return inc


db_service = DatabaseService()
