#!/usr/bin/env python3
"""
Generate Grafana v11 dashboard from metrics.py declarations.

This script:
1. Reads all metric declarations from app/core/metrics.py
2. Automatically generates appropriate panel configurations for each metric type
3. Organizes panels by category
4. Adds dashboard-level variable for commit_sha filtering
5. Outputs a complete Grafana v11 compatible dashboard JSON

Usage:
    uv run python scripts/generate_dashboard.py

This will generate/update tools/main-dashboard.json
"""

import json
import re
import sys
from pathlib import Path
from typing import Any


def extract_metrics_with_metadata(metrics_file: Path) -> dict[str, dict[str, Any]]:
    """
    Extract all metric declarations with their types and metadata.

    Returns:
        Dict mapping metric name to {type, description, labels}
    """
    metrics = {}

    if not metrics_file.exists():
        print(f"Error: Metrics file not found: {metrics_file}", file=sys.stderr)
        return metrics

    content = metrics_file.read_text()

    # Pattern to match metric declarations with their docstrings
    # Looks for: MetricType(\n    "metric_name",\n    "description",\n    ["labels"]
    pattern = r'(Counter|Histogram|Gauge|Summary)\s*\(\s*["\']([a-zA-Z_][a-zA-Z0-9_]*)["\'],\s*["\']([^"\']*)["\'],\s*\[([^\]]*)\]'

    matches = re.finditer(pattern, content, re.MULTILINE)
    for match in matches:
        metric_type = match.group(1)
        metric_name = match.group(2)
        description = match.group(3)
        labels_str = match.group(4)

        # Parse labels
        labels = [label.strip().strip("\"'") for label in labels_str.split(",")]
        labels = [
            label for label in labels if label and label != "commit_sha"
        ]  # Remove commit_sha as it's a dashboard variable

        metrics[metric_name] = {
            "type": metric_type,
            "description": description,
            "labels": labels,
        }

    return metrics


def categorize_metrics(
    metrics: dict[str, dict[str, Any]],
) -> dict[str, list[tuple[str, dict[str, Any]]]]:
    """Group metrics by category based on their names."""
    categories = {
        "HTTP Layer": [],
        "Authentication & Authorization": [],
        "Database": [],
        "Resilience & Retries": [],
        "Queue & Workers": [],
        "Email & Notifications": [],
        "User Management": [],
    }

    for metric_name, metadata in metrics.items():
        name_lower = metric_name.lower()

        if "http_request" in name_lower or name_lower.startswith("http_"):
            categories["HTTP Layer"].append((metric_name, metadata))
        elif any(x in name_lower for x in ["login", "auth", "token", "password"]):
            categories["Authentication & Authorization"].append((metric_name, metadata))
        elif "database" in name_lower:
            categories["Database"].append((metric_name, metadata))
        elif any(x in name_lower for x in ["retry", "circuit"]):
            categories["Resilience & Retries"].append((metric_name, metadata))
        elif any(x in name_lower for x in ["queue", "worker"]):
            categories["Queue & Workers"].append((metric_name, metadata))
        elif any(x in name_lower for x in ["email", "notification", "digest"]):
            categories["Email & Notifications"].append((metric_name, metadata))
        elif any(x in name_lower for x in ["user", "registration"]):
            categories["User Management"].append((metric_name, metadata))

    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def create_panel(
    metric_name: str, metadata: dict[str, Any], panel_id: int, x: int, y: int
) -> dict[str, Any]:
    """Create a Grafana panel for a metric."""

    metric_type = metadata["type"]
    description = metadata["description"]
    labels = metadata["labels"]

    # Build PromQL expression based on metric type
    if metric_type == "Counter":
        # Counters: use rate() and include all labels in grouping
        base_name = metric_name  # Keep full name with _total
        if labels:
            by_clause = f" by ({', '.join(labels)})"
            legend = "{{" + "}} - {{".join(labels) + "}}"
        else:
            by_clause = ""
            legend = metric_name

        expr = f'sum(rate({base_name}{{commit_sha=~"$commit_sha"}}[5m])){by_clause}'
        unit = "ops"

    elif metric_type == "Histogram":
        # Histograms: use histogram_quantile for p95
        base_name = re.sub(r"_(bucket|count|sum)$", "", metric_name)

        # Determine unit based on metric name
        if "duration" in metric_name or "seconds" in metric_name:
            unit = "s"
        elif "size" in metric_name or "bytes" in metric_name:
            unit = "bytes"
        elif "count" in metric_name:
            unit = "short"
        else:
            unit = "short"

        # Build legend with labels
        if labels:
            by_clause = f", {', '.join(labels)}"
            legend = "{{" + "}} - {{".join(labels) + "}}"
        else:
            by_clause = ""
            legend = "p95"

        expr = f'histogram_quantile(0.95, sum(rate({base_name}_bucket{{commit_sha=~"$commit_sha"}}[5m])) by (le{by_clause}))'

    else:  # Gauge
        if labels:
            by_clause = f" by ({', '.join(labels)})"
            legend = "{{" + "}} - {{".join(labels) + "}}"
        else:
            by_clause = ""
            legend = metric_name

        expr = f'sum({metric_name}{{commit_sha=~"$commit_sha"}}){by_clause}'
        unit = "short"

    # Create friendly title from metric name
    title = metric_name.replace("_", " ").title()

    return {
        "id": panel_id,
        "type": "timeseries",
        "title": title,
        "description": description,
        "gridPos": {"h": 8, "w": 12, "x": x, "y": y},
        "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
        "targets": [
            {
                "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
                "expr": expr,
                "legendFormat": legend,
                "refId": "A",
            }
        ],
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {
                    "axisBorderShow": False,
                    "axisCenteredZero": False,
                    "axisColorMode": "text",
                    "axisLabel": "",
                    "axisPlacement": "auto",
                    "barAlignment": 0,
                    "drawStyle": "line",
                    "fillOpacity": 10,
                    "gradientMode": "none",
                    "hideFrom": {"legend": False, "tooltip": False, "viz": False},
                    "insertNulls": False,
                    "lineInterpolation": "linear",
                    "lineWidth": 1,
                    "pointSize": 5,
                    "scaleDistribution": {"type": "linear"},
                    "showPoints": "never",
                    "spanNulls": False,
                    "stacking": {"group": "A", "mode": "none"},
                    "thresholdsStyle": {"mode": "off"},
                },
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "red", "value": 80},
                    ],
                },
                "unit": unit,
                "unitScale": True,
            },
            "overrides": [],
        },
        "options": {
            "legend": {
                "calcs": [],
                "displayMode": "list",
                "placement": "bottom",
                "showLegend": True,
            },
            "tooltip": {"mode": "multi", "sort": "none"},
        },
        "transparent": False,
    }


def generate_dashboard(metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Generate complete Grafana dashboard JSON."""

    # Categorize metrics
    categories = categorize_metrics(metrics)

    panels: list[dict[str, Any]] = []
    panel_id = 1
    y_pos = 0

    # Add panels for each category
    for category_name, category_metrics in categories.items():
        # Add row header
        panels.append(
            {
                "type": "row",
                "title": category_name,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
                "id": panel_id,
                "collapsed": False,
            }
        )
        panel_id += 1
        y_pos += 1

        # Add panels for each metric in this category
        for i, (metric_name, metadata) in enumerate(sorted(category_metrics)):
            x_pos = 0 if i % 2 == 0 else 12

            # Move to next row if starting left panel (except first)
            if i % 2 == 0 and i > 0:
                y_pos += 8

            panel = create_panel(metric_name, metadata, panel_id, x_pos, y_pos)
            panels.append(panel)
            panel_id += 1

        # Move to next row after last panel in category
        y_pos += 8

    # Build complete dashboard
    dashboard = {
        "__inputs": [
            {
                "name": "DS_PROMETHEUS",
                "label": "Prometheus/VictoriaMetrics",
                "description": "Select your VictoriaMetrics or Prometheus datasource",
                "type": "datasource",
                "pluginId": "prometheus",
            }
        ],
        "__elements": {},
        "__requires": [
            {
                "type": "grafana",
                "id": "grafana",
                "name": "Grafana",
                "version": "11.0.0",
            },
            {
                "type": "datasource",
                "id": "prometheus",
                "name": "Prometheus",
                "version": "1.0.0",
            },
            {"type": "panel", "id": "timeseries", "name": "Time series", "version": ""},
        ],
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": panels,
        "refresh": "30s",
        "schemaVersion": 39,
        "tags": ["codeleash", "metrics", "prometheus"],
        "templating": {
            "list": [
                {
                    "allValue": ".*",
                    "current": {"selected": True, "text": "All", "value": "$__all"},
                    "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
                    "definition": "label_values(commit_sha)",
                    "hide": 0,
                    "includeAll": True,
                    "multi": True,
                    "name": "commit_sha",
                    "options": [],
                    "query": {
                        "query": "label_values(commit_sha)",
                        "refId": "PrometheusVariableQueryEditor-VariableQuery",
                    },
                    "refresh": 1,
                    "regex": "",
                    "skipUrlSync": False,
                    "sort": 1,
                    "type": "query",
                }
            ]
        },
        "time": {"from": "now-6h", "to": "now"},
        "timepicker": {},
        "timezone": "browser",
        "title": "CodeLeash Metrics Dashboard",
        "uid": None,
        "version": 1,
        "weekStart": "",
    }

    return dashboard


def main() -> int:
    """Main entry point."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    tools_dir = project_root / "tools"

    metrics_file = project_root / "app" / "core" / "metrics.py"
    output_file = tools_dir / "main-dashboard.json"

    print("📊 Generating Grafana v11 dashboard from metrics.py...")
    print()

    # Extract metrics
    metrics = extract_metrics_with_metadata(metrics_file)
    if not metrics:
        print("❌ Error: No metrics found in metrics.py", file=sys.stderr)
        return 1

    print(f"Found {len(metrics)} metrics:")
    print(f"  - {sum(1 for m in metrics.values() if m['type'] == 'Counter')} Counters")
    print(
        f"  - {sum(1 for m in metrics.values() if m['type'] == 'Histogram')} Histograms"
    )
    print(f"  - {sum(1 for m in metrics.values() if m['type'] == 'Gauge')} Gauges")
    print()

    # Generate dashboard
    dashboard = generate_dashboard(metrics)

    # Write to file
    with open(output_file, "w") as f:
        json.dump(dashboard, f, indent=2)

    print(f"✅ Generated dashboard with {len(dashboard['panels'])} panels")
    print(f"   Saved to: {output_file}")
    print()
    print("Dashboard features:")
    print("  ✅ Grafana v11 compatible (schema v39)")
    print("  ✅ All panels use timeseries visualization")
    print("  ✅ Organized by category with row headers")
    print("  ✅ Dashboard variable for commit_sha filtering")
    print("  ✅ All queries filtered by commit_sha variable")
    print("  ✅ Automatic legend formatting with labels")
    print()
    print("You can now import tools/main-dashboard.json into Grafana!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
