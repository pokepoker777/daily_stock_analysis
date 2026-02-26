# -*- coding: utf-8 -*-
"""
===================================
Application Metrics (Lightweight)
===================================

Provides a lightweight, zero-dependency metrics collection system
that exposes a Prometheus-compatible /metrics endpoint.

No external library required — uses simple counters and gauges
stored in-process. For production deployments with Grafana,
swap this with prometheus_client if needed.

Tracked metrics:
- analysis_total (counter) — total analysis requests by stock/status
- analysis_duration_seconds (histogram-like) — AI call latency
- data_fetch_total (counter) — data fetch attempts by source/status
- notification_total (counter) — notifications sent by channel/status
- api_request_total (counter) — HTTP requests by method/path/status
- data_quality_issues (counter) — data validation issues by severity
- active_tasks (gauge) — currently running analysis tasks

Usage:
    from src.metrics import metrics
    metrics.inc("analysis_total", labels={"code": "600519", "status": "success"})
    metrics.observe("analysis_duration_seconds", 2.35, labels={"model": "gemini"})
    metrics.set_gauge("active_tasks", 3)
"""

import logging
import threading
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Thread-safe in-process metrics collector."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._start_time = time.time()

    def inc(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter."""
        key = self._label_key(labels)
        with self._lock:
            self._counters[name][key] += value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge value."""
        key = f"{name}{self._label_key(labels)}"
        with self._lock:
            self._gauges[key] = value

    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram observation (e.g., latency)."""
        key = f"{name}{self._label_key(labels)}"
        with self._lock:
            self._histograms[key].append(value)
            # Keep only last 1000 observations to bound memory
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-500:]

    def get_all(self) -> Dict[str, Any]:
        """Get all metrics as a JSON-serializable dict."""
        with self._lock:
            result = {
                "uptime_seconds": round(time.time() - self._start_time, 1),
                "counters": {},
                "gauges": dict(self._gauges),
                "histograms": {},
            }

            for name, label_map in self._counters.items():
                result["counters"][name] = dict(label_map)

            for key, values in self._histograms.items():
                if values:
                    sorted_v = sorted(values)
                    n = len(sorted_v)
                    result["histograms"][key] = {
                        "count": n,
                        "sum": round(sum(sorted_v), 4),
                        "avg": round(sum(sorted_v) / n, 4),
                        "min": round(sorted_v[0], 4),
                        "max": round(sorted_v[-1], 4),
                        "p50": round(sorted_v[n // 2], 4),
                        "p95": round(sorted_v[int(n * 0.95)], 4) if n >= 20 else None,
                        "p99": round(sorted_v[int(n * 0.99)], 4) if n >= 100 else None,
                    }

            return result

    def to_prometheus_text(self) -> str:
        """Export metrics in Prometheus text exposition format."""
        lines = []
        lines.append(f"# HELP uptime_seconds Time since process start")
        lines.append(f"# TYPE uptime_seconds gauge")
        lines.append(f"uptime_seconds {time.time() - self._start_time:.1f}")

        with self._lock:
            # Counters
            for name, label_map in self._counters.items():
                lines.append(f"# HELP {name} Counter metric")
                lines.append(f"# TYPE {name} counter")
                for label_key, value in label_map.items():
                    if label_key:
                        lines.append(f"{name}{{{label_key}}} {value}")
                    else:
                        lines.append(f"{name} {value}")

            # Gauges
            for key, value in self._gauges.items():
                lines.append(f"# TYPE {key} gauge")
                lines.append(f"{key} {value}")

            # Histograms (simplified — just count and sum)
            for key, values in self._histograms.items():
                if values:
                    lines.append(f"# TYPE {key} summary")
                    lines.append(f"{key}_count {len(values)}")
                    lines.append(f"{key}_sum {sum(values):.4f}")

        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        """Reset all metrics (for testing)."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()

    @staticmethod
    def _label_key(labels: Optional[Dict[str, str]]) -> str:
        """Convert labels dict to Prometheus label string."""
        if not labels:
            return ""
        parts = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return ",".join(parts)


# Global singleton
metrics = MetricsCollector()
