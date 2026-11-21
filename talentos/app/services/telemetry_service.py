from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from uuid import uuid4

from app.domain.models import TelemetryEvent, TelemetrySummary
from app.ports.repositories import RepositoryPort

SUCCESS_STATUS = "ok"


class TelemetryService:
    """Persists bounded operation metrics and builds tenant-scoped summaries."""

    def __init__(self, repo: RepositoryPort) -> None:
        self._repo = repo

    def track(
        self,
        *,
        tenant_id: str,
        operation: str,
        provider: str = "offline",
        model: str = "offline-extractor",
        latency_ms: float = 0.0,
        tokens_in: int = 0,
        tokens_out: int = 0,
        citation_pass_rate: float = 0.0,
        status: str = SUCCESS_STATUS,
    ) -> TelemetryEvent:
        event = TelemetryEvent(
            id=str(uuid4()),
            tenant_id=tenant_id,
            operation=operation,
            provider=provider,
            model=model,
            latency_ms=max(0.0, float(latency_ms)),
            tokens_in=max(0, int(tokens_in)),
            tokens_out=max(0, int(tokens_out)),
            citation_pass_rate=min(1.0, max(0.0, float(citation_pass_rate))),
            status=status,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._repo.record_telemetry(event)
        return event

    def summary(self, tenant_id: str) -> TelemetrySummary:
        events = self._repo.list_telemetry(tenant_id)
        total = len(events)
        if total == 0:
            return TelemetrySummary(tenant_id, 0, 0, 0, 0.0, 0, 0, 0.0, {})
        success = sum(event.status == SUCCESS_STATUS for event in events)
        return TelemetrySummary(
            tenant_id=tenant_id,
            total_operations=total,
            success_count=success,
            failure_count=total - success,
            average_latency_ms=round(sum(event.latency_ms for event in events) / total, 3),
            tokens_in=sum(event.tokens_in for event in events),
            tokens_out=sum(event.tokens_out for event in events),
            citation_pass_rate=round(
                sum(event.citation_pass_rate for event in events) / total, 6
            ),
            by_operation=dict(Counter(event.operation for event in events)),
        )
