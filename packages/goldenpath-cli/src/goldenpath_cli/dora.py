"""DORA metrics collection and audit trail.

Captures four core DORA metrics:
1. Deployment Frequency
2. Lead Time for Changes
3. Change Failure Rate
4. Mean Time To Recovery (MTTR)

All events are logged in a SOC 2 compliant structured format.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from goldenpath_cli.config import DoraConfig


@dataclass(frozen=True)
class DoraEvent:
    """A single DORA telemetry event."""

    event_type: str  # deployment | change | failure | recovery | validation
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    work_id: str = ""
    project: str = ""
    team: str = ""
    environment: str = "local"  # local | sandbox | staging | production
    commit_sha: str = ""
    branch: str = ""
    duration_seconds: float = 0.0
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    audit: AuditContext = field(default_factory=lambda: AuditContext())

    def to_json(self) -> str:
        """Serialize to JSON line."""
        return json.dumps(asdict(self), default=str)


@dataclass(frozen=True)
class AuditContext:
    """SOC 2 compliant audit context (who, what, when, why)."""

    actor: str = field(default_factory=lambda: os.environ.get("USER", "unknown"))
    actor_email: str = field(default_factory=lambda: os.environ.get("EMAIL", ""))
    action: str = ""
    reason: str = ""
    source_ip: str = "127.0.0.1"
    session_id: str = ""
    compliance_framework: str = "soc2"


class DoraTelemetry:
    """DORA metrics collector with local persistence."""

    def __init__(self, config: DoraConfig) -> None:
        self.config = config
        self._buffer: list[DoraEvent] = []
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        """Create local storage directory if needed."""
        path = Path(self.config.local_metrics_path)
        path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: DoraEvent) -> None:
        """Emit a DORA event to local storage."""
        if not self.config.enabled:
            return
        self._buffer.append(event)
        self._flush_event(event)

    def _flush_event(self, event: DoraEvent) -> None:
        """Append event to local JSONL file."""
        path = Path(self.config.local_metrics_path)
        with open(path, "a", encoding="utf-8") as f:
            f.write(event.to_json() + "\n")

    def record_validation(
        self,
        work_id: str,
        project: str,
        commit_sha: str,
        branch: str,
        success: bool,
        duration: float,
        metadata: dict[str, Any] | None = None,
    ) -> DoraEvent:
        """Record a validation event (Shift-Left metric)."""
        event = DoraEvent(
            event_type="validation",
            work_id=work_id,
            project=project,
            environment="local",
            commit_sha=commit_sha,
            branch=branch,
            success=success,
            duration_seconds=duration,
            metadata=metadata or {},
            audit=AuditContext(
                action="local_validation",
                reason="pre-push_governance_check",
            ),
        )
        self.emit(event)
        return event

    def record_deployment_start(
        self,
        work_id: str,
        project: str,
        environment: str,
        commit_sha: str,
    ) -> DoraEvent:
        """Record deployment initiation."""
        event = DoraEvent(
            event_type="deployment",
            work_id=work_id,
            project=project,
            environment=environment,
            commit_sha=commit_sha,
            metadata={"status": "started", "start_time": time.time()},
            audit=AuditContext(
                action="deploy",
                reason=f"deploy_to_{environment}",
            ),
        )
        self.emit(event)
        return event

    def record_change(
        self,
        work_id: str,
        project: str,
        commit_sha: str,
        branch: str,
        lead_time_seconds: float,
    ) -> DoraEvent:
        """Record a change (for Lead Time calculation)."""
        event = DoraEvent(
            event_type="change",
            work_id=work_id,
            project=project,
            commit_sha=commit_sha,
            branch=branch,
            duration_seconds=lead_time_seconds,
            metadata={"metric": "lead_time_for_changes"},
            audit=AuditContext(
                action="merge",
                reason="change_integrated_to_main",
            ),
        )
        self.emit(event)
        return event

    def record_failure(
        self,
        work_id: str,
        project: str,
        environment: str,
        commit_sha: str,
        error_message: str,
    ) -> DoraEvent:
        """Record a deployment failure (for Change Failure Rate)."""
        event = DoraEvent(
            event_type="failure",
            work_id=work_id,
            project=project,
            environment=environment,
            commit_sha=commit_sha,
            success=False,
            metadata={"error": error_message},
            audit=AuditContext(
                action="incident",
                reason="deployment_failure_detected",
            ),
        )
        self.emit(event)
        return event

    def record_recovery(
        self,
        work_id: str,
        project: str,
        environment: str,
        commit_sha: str,
        mttr_seconds: float,
    ) -> DoraEvent:
        """Record incident recovery (for MTTR)."""
        event = DoraEvent(
            event_type="recovery",
            work_id=work_id,
            project=project,
            environment=environment,
            commit_sha=commit_sha,
            duration_seconds=mttr_seconds,
            metadata={"metric": "mttr"},
            audit=AuditContext(
                action="remediate",
                reason="incident_resolved",
            ),
        )
        self.emit(event)
        return event

    def compute_metrics(self, project: str | None = None, days: int = 30) -> dict[str, Any]:
        """Compute DORA metrics from local event log."""
        path = Path(self.config.local_metrics_path)
        if not path.exists():
            return {}

        events: list[dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))

        # Filter by project if specified
        if project:
            events = [e for e in events if e.get("project") == project]

        deployments = [e for e in events if e["event_type"] == "deployment" and e["success"]]
        changes = [e for e in events if e["event_type"] == "change"]
        failures = [e for e in events if e["event_type"] == "failure"]
        recoveries = [e for e in events if e["event_type"] == "recovery"]

        deployment_frequency = len(deployments)
        avg_lead_time = (
            sum(c["duration_seconds"] for c in changes) / len(changes) if changes else 0.0
        )
        change_failure_rate = len(failures) / len(deployments) if deployments else 0.0
        avg_mttr = (
            sum(r["duration_seconds"] for r in recoveries) / len(recoveries) if recoveries else 0.0
        )

        return {
            "period_days": days,
            "project": project or "all",
            "deployment_frequency": deployment_frequency,
            "lead_time_for_changes_seconds": round(avg_lead_time, 2),
            "lead_time_for_changes_hours": round(avg_lead_time / 3600, 2),
            "change_failure_rate": round(change_failure_rate, 4),
            "mean_time_to_recovery_seconds": round(avg_mttr, 2),
            "mean_time_to_recovery_hours": round(avg_mttr / 3600, 2),
            "total_events": len(events),
            "audit_trail_compliance": "soc2",
        }
