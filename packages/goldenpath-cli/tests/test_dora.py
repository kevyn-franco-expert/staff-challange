"""Test DORA telemetry collection."""

import json
from pathlib import Path

import pytest

from goldenpath_cli.config import DoraConfig
from goldenpath_cli.dora import AuditContext, DoraEvent, DoraTelemetry


class TestDoraTelemetry:
    """DORA metrics tests."""

    def test_emit_event(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Events should be appended to local JSONL file."""
        monkeypatch.chdir(tmp_path)
        config = DoraConfig(local_metrics_path=".goldenpath/dora.jsonl")
        telemetry = DoraTelemetry(config)

        event = DoraEvent(
            event_type="validation",
            work_id="FIN-123",
            project="transactionify",
            success=True,
        )
        telemetry.emit(event)

        log_path = tmp_path / ".goldenpath" / "dora.jsonl"
        assert log_path.exists()
        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["work_id"] == "FIN-123"
        assert data["project"] == "transactionify"

    def test_compute_metrics_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Empty log should return empty metrics."""
        monkeypatch.chdir(tmp_path)
        config = DoraConfig(local_metrics_path=".goldenpath/dora.jsonl")
        telemetry = DoraTelemetry(config)

        metrics = telemetry.compute_metrics()
        assert metrics == {}

    def test_compute_metrics_with_data(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Metrics should aggregate correctly."""
        monkeypatch.chdir(tmp_path)
        config = DoraConfig(local_metrics_path=".goldenpath/dora.jsonl")
        telemetry = DoraTelemetry(config)

        # Record some events
        telemetry.record_deployment_start("FIN-1", "tx", "staging", "abc123")
        telemetry.record_change("FIN-1", "tx", "abc123", "main", 3600.0)
        telemetry.record_failure("FIN-2", "tx", "staging", "def456", "timeout")
        telemetry.record_recovery("FIN-2", "tx", "staging", "def456", 1800.0)

        metrics = telemetry.compute_metrics(project="tx")
        assert metrics["deployment_frequency"] == 1
        assert metrics["lead_time_for_changes_hours"] == 1.0
        assert metrics["change_failure_rate"] == 1.0
        assert metrics["mean_time_to_recovery_hours"] == 0.5

    def test_audit_context(self) -> None:
        """Audit context should capture SOC2 fields."""
        audit = AuditContext(
            actor="developer@example.com",
            action="deploy",
            reason="feature_release",
        )
        assert audit.actor == "developer@example.com"
        assert audit.compliance_framework == "soc2"
