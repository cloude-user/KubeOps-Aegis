// KubeOps-Aegis (Azure) WebSocket & Dashboard Handler
const state = {
  incidents: [],
  selectedIncidentId: null,
  ws: null
};

document.addEventListener("DOMContentLoaded", () => {
  initWebSocket();
  fetchIncidents();
});

function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  state.ws = new WebSocket(wsUrl);

  state.ws.onopen = () => {
    document.getElementById("ws-status").textContent = "Azure AKS Connected";
  };

  state.ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleServerEvent(message);
  };

  state.ws.onclose = () => {
    document.getElementById("ws-status").textContent = "Reconnecting...";
    setTimeout(initWebSocket, 2000);
  };
}

function handleServerEvent(event) {
  if (event.type === "INCIDENT_CREATED" || event.type === "STATE_UPDATED" || event.type === "WAITING_APPROVAL" || event.type === "INCIDENT_RESOLVED") {
    fetchIncidents();
  }
}

async function fetchIncidents() {
  try {
    const res = await fetch("/api/incidents");
    state.incidents = await res.json();
    renderIncidentList();
    if (state.incidents.length > 0 && !state.selectedIncidentId) {
      selectIncident(state.incidents[0].incident_id);
    } else if (state.selectedIncidentId) {
      const activeInc = state.incidents.find(i => i.incident_id === state.selectedIncidentId);
      if (activeInc) renderIncidentDetails(activeInc);
    }
  } catch (err) {
    console.error("Failed to fetch incidents:", err);
  }
}

function renderIncidentList() {
  const listEl = document.getElementById("incident-list");
  document.getElementById("incident-count").textContent = `${state.incidents.length} total`;
  document.getElementById("metric-active").textContent = state.incidents.filter(i => ["triaging", "diagnosing", "remediating", "waiting_approval"].includes(i.status)).length;

  if (state.incidents.length === 0) {
    listEl.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🛡️</div>
        <p>No active incidents. Azure AKS Cluster is healthy.</p>
        <small>Click one of the Chaos buttons above to trigger an incident.</small>
      </div>`;
    return;
  }

  listEl.innerHTML = state.incidents.map(inc => {
    const isActive = inc.incident_id === state.selectedIncidentId;
    const badgeClass = inc.status === "resolved" ? "badge-success" : inc.status === "failed" ? "badge-danger" : "badge-warning";
    return `
      <div class="incident-card ${isActive ? 'active' : ''}" onclick="selectIncident('${inc.incident_id}')">
        <div class="incident-card-top">
          <span class="incident-name">${inc.alert_name}</span>
          <span class="badge ${badgeClass}">${inc.status}</span>
        </div>
        <div class="incident-meta">Service: <strong>${inc.resource_name}</strong> (${inc.namespace})</div>
      </div>`;
  }).join("");
}

function selectIncident(id) {
  state.selectedIncidentId = id;
  renderIncidentList();
  const inc = state.incidents.find(i => i.incident_id === id);
  if (inc) renderIncidentDetails(inc);
}

function renderIncidentDetails(inc) {
  // Update Agent Workflow Nodes
  const stepMap = {
    "triaging": ["node-triage"],
    "diagnosing": ["node-triage", "node-diagnostic"],
    "remediating": ["node-triage", "node-diagnostic", "node-remediation"],
    "waiting_approval": ["node-triage", "node-diagnostic", "node-remediation", "node-gitops"],
    "resolved": ["node-triage", "node-diagnostic", "node-remediation", "node-gitops", "node-verification"]
  };

  const activeNodes = stepMap[inc.status] || ["node-triage"];
  document.querySelectorAll(".node-pill").forEach(el => {
    el.classList.remove("active", "completed");
    if (activeNodes.includes(el.id)) {
      if (el.id === activeNodes[activeNodes.length - 1] && inc.status !== "resolved") {
        el.classList.add("active");
      } else {
        el.classList.add("completed");
      }
    }
  });

  // Activity Stream Logs
  const timelineEl = document.getElementById("timeline-list");
  if (inc.step_logs && inc.step_logs.length > 0) {
    timelineEl.innerHTML = inc.step_logs.map(log => `
      <div class="log-item ${log.status}">
        <span class="log-time">${log.timestamp.split("T")[1]?.slice(0, 8) || "00:00:00"}</span>
        <span class="log-agent">[${log.agent}]</span>
        <span class="log-text">${log.details}</span>
      </div>`).join("");
  }

  // Approval Panel & Diff Viewer
  const approvalEl = document.getElementById("approval-panel");
  if (inc.status === "waiting_approval" && inc.remediation) {
    document.getElementById("approval-badge").textContent = "Approval Needed";
    approvalEl.innerHTML = `
      <div class="pr-summary-box">
        <div class="pr-title">PR Proposed: ${inc.gitops_pr?.pr_title || 'Remediation Patch'}</div>
        <div class="rca-box">
          <strong>Root Cause:</strong> ${inc.diagnostic?.root_cause || 'Memory limit exceeded (OOMKilled exit code 137).'}<br/>
          <strong>Strategy:</strong> Bump memory limit from 512Mi to 1Gi in Helm values.yaml
        </div>
        <div class="diff-viewer">
          <span class="diff-line-del">- resources.limits.memory: 512Mi</span>
          <span class="diff-line-add">+ resources.limits.memory: 1Gi</span>
        </div>
        <div class="approval-btn-group">
          <button class="btn btn-approve" onclick="approveIncident('${inc.incident_id}')">⚡ Approve & Sync via ArgoCD</button>
          <button class="btn btn-reject" onclick="rejectIncident('${inc.incident_id}')">Reject</button>
        </div>
      </div>`;
  } else if (inc.status === "resolved") {
    document.getElementById("approval-badge").textContent = "Resolved & Verified";
    approvalEl.innerHTML = `
      <div class="pr-summary-box">
        <div class="pr-title text-success">✅ Incident Resolved</div>
        <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:8px;">Patch merged to Git. ArgoCD reconciled cluster state on Azure AKS.</p>
        <pre style="font-size:0.75rem; background:rgba(0,0,0,0.3); padding:10px; border-radius:6px; white-space:pre-wrap;">${inc.post_mortem || 'Post-Mortem report generated successfully.'}</pre>
      </div>`;
  } else {
    document.getElementById("approval-badge").textContent = "Processing";
    approvalEl.innerHTML = `<div class="empty-state"><div class="empty-icon">⏳</div><p>Agent state machine running on Azure AKS...</p></div>`;
  }
}

async function triggerChaos(scenario) {
  try {
    await fetch("/api/chaos/trigger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario, service: "payment-service", namespace: "default" })
    });
    fetchIncidents();
  } catch (err) {
    console.error("Failed to trigger chaos:", err);
  }
}

async function approveIncident(id) {
  try {
    await fetch(`/api/incidents/${id}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ comment: "Approved via Azure SRE Dashboard" })
    });
    fetchIncidents();
  } catch (err) {
    console.error("Failed to approve incident:", err);
  }
}

async function rejectIncident(id) {
  try {
    await fetch(`/api/incidents/${id}/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ comment: "Rejected via Azure SRE Dashboard" })
    });
    fetchIncidents();
  } catch (err) {
    console.error("Failed to reject incident:", err);
  }
}
