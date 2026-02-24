#!/usr/bin/env python3
"""
Validate Grafana v11 dashboard structure and ensure all metrics are tracked.

This script:
1. Validates dashboard JSON structure (Grafana v11 requirements)
   - Checks for required fields (__inputs, __requires, schemaVersion, etc.)
   - Validates panel structure and types
   - Detects deprecated panel types (e.g., 'graph' instead of 'timeseries')
2. Extracts all metric declarations from app/core/metrics.py
3. Extracts all metric references from tools/main-dashboard.json
4. Reports any missing metrics

Exit codes:
  0 - Dashboard is valid and all metrics are tracked
  1 - Validation errors or missing metrics found
"""

import json
import re
import sys
from pathlib import Path


def extract_declared_metrics(metrics_file: Path) -> tuple[set[str], set[str]]:
    """
    Extract all metric names declared in the metrics.py file.

    Returns:
        (all_metrics, base_metrics): all_metrics includes full names with suffixes,
                                      base_metrics includes stripped versions for comparison
    """
    all_metrics = set()
    base_metrics = set()

    if not metrics_file.exists():
        print(f"Error: Metrics file not found: {metrics_file}", file=sys.stderr)
        return all_metrics, base_metrics

    content = metrics_file.read_text()

    # Pattern to match Counter("metric_name", ...), Histogram("metric_name", ...), Gauge("metric_name", ...)
    # Looking for: MetricType("metric_name"
    pattern = (
        r'(?:Counter|Histogram|Gauge|Summary)\s*\(\s*["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']'
    )

    matches = re.finditer(pattern, content)
    for match in matches:
        metric_name = match.group(1)
        all_metrics.add(metric_name)

        # Create base metric name for comparison
        # Strip _total (Counter suffix), _bucket/_sum/_count (Histogram suffixes)
        base_name = re.sub(r"_(total|bucket|sum|count)$", "", metric_name)
        base_metrics.add(base_name)

        # Also add the original name to base metrics for exact matches
        base_metrics.add(metric_name)

    return all_metrics, base_metrics


def validate_dashboard_structure(data: dict) -> list[str]:
    """
    Validate Grafana v11 dashboard structure.

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Check for __inputs section
    if "__inputs" not in data:
        errors.append("Missing '__inputs' section (required for import)")

    # Check for __requires section
    if "__requires" not in data:
        errors.append("Missing '__requires' section")
    else:
        requires = data["__requires"]
        if not any(r.get("type") == "grafana" for r in requires):
            errors.append("Missing Grafana requirement in '__requires'")
        if not any(r.get("id") == "prometheus" for r in requires):
            errors.append("Missing Prometheus datasource in '__requires'")

    # Check dashboard-level required fields
    required_fields = ["panels", "title", "schemaVersion", "version"]
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")

    # Validate schema version is recent (v11 = 39)
    schema_version = data.get("schemaVersion")
    if schema_version and schema_version < 39:
        errors.append(
            f"Schema version {schema_version} is outdated (Grafana v11 uses 39)"
        )

    # Validate panels
    panels = data.get("panels", [])
    if not panels:
        errors.append("Dashboard has no panels")

    for i, panel in enumerate(panels):
        if "type" not in panel:
            errors.append(f"Panel {i+1} missing 'type' field")
        elif panel["type"] == "graph":
            errors.append(
                f"Panel {i+1} '{panel.get('title', 'Untitled')}' uses deprecated 'graph' type (use 'timeseries')"
            )

        if "id" not in panel:
            errors.append(f"Panel {i+1} missing 'id' field")

        # Check non-row panels have required structure
        if panel.get("type") != "row":
            if "targets" not in panel:
                errors.append(
                    f"Panel {i+1} '{panel.get('title', 'Untitled')}' missing 'targets'"
                )

            if panel.get("type") == "timeseries" and "fieldConfig" not in panel:
                errors.append(
                    f"Panel {i+1} '{panel.get('title', 'Untitled')}' missing 'fieldConfig'"
                )

    return errors


def extract_dashboard_metrics(dashboard_file: Path) -> tuple[set[str], set[str]]:
    """
    Extract all metric names referenced in the Grafana dashboard JSON.

    Returns:
        (raw_metrics, normalized_metrics): raw as found in queries,
                                            normalized with base names for comparison
    """
    raw_metrics = set()
    normalized_metrics = set()

    if not dashboard_file.exists():
        print(f"Error: Dashboard file not found: {dashboard_file}", file=sys.stderr)
        return raw_metrics, normalized_metrics

    try:
        with open(dashboard_file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse dashboard JSON: {e}", file=sys.stderr)
        return raw_metrics, normalized_metrics

    # Validate dashboard structure
    validation_errors = validate_dashboard_structure(data)
    if validation_errors:
        print("❌ Dashboard validation failed:", file=sys.stderr)
        for error in validation_errors:
            print(f"   - {error}", file=sys.stderr)
        print()
        return raw_metrics, normalized_metrics

    # Grafana v11 uses flat structure (no nested "dashboard" key)
    panels = data.get("panels", [])

    for panel in panels:
        targets = panel.get("targets", [])
        for target in targets:
            expr = target.get("expr", "")
            if expr:
                # Extract metric names from PromQL expressions
                panel_metrics = extract_metrics_from_promql(expr)
                raw_metrics.update(panel_metrics)

                # Normalize: strip suffixes and add variants
                for metric in panel_metrics:
                    normalized_metrics.add(metric)
                    # Strip common suffixes for comparison
                    base_name = re.sub(r"_(total|bucket|sum|count)$", "", metric)
                    normalized_metrics.add(base_name)

    return raw_metrics, normalized_metrics


def extract_metrics_from_promql(expr: str) -> set[str]:
    """
    Extract base metric names from PromQL expressions.

    Handles patterns like:
    - sum(rate(metric_name[5m]))
    - histogram_quantile(0.95, sum(rate(metric_name_bucket[5m])))
    - metric_name{label="value"}
    - sum(metric_name) by (label)
    - metric_name (bare metric)
    """
    metrics = set()

    # Pattern: metric name followed by {, [, ), space, comma, or end of string
    # Captures metric names that look like Prometheus metrics (contain underscores)
    pattern = r"\b([a-z_][a-z0-9_]+)(?=[\{\[\)\s,]|$)"

    # Find all potential metric names
    potential_metrics = re.findall(pattern, expr)

    # Filter out PromQL functions and keywords
    promql_keywords = {
        "sum",
        "rate",
        "avg",
        "max",
        "min",
        "count",
        "by",
        "without",
        "histogram_quantile",
        "increase",
        "irate",
        "delta",
        "idelta",
        "changes",
        "deriv",
        "predict_linear",
        "abs",
        "ceil",
        "floor",
        "round",
        "exp",
        "ln",
        "log2",
        "log10",
        "sqrt",
        "and",
        "or",
        "unless",
        "group_left",
        "group_right",
        "on",
        "ignoring",
        "bool",
        "offset",
        "le",
        "job",
        "instance",
        "status",
        "code",
        "method",
    }

    for metric in potential_metrics:
        # Skip if it's a known PromQL function/keyword
        if metric.lower() in promql_keywords:
            continue

        # Must have at least one underscore (Prometheus naming convention)
        if "_" in metric:
            # Handle _bucket, _count, _sum suffixes for histograms
            # We want the base metric name without these suffixes
            base_metric = re.sub(r"_(bucket|count|sum|total)$", "", metric)

            # Add both the original and base name
            metrics.add(metric)
            if base_metric != metric:
                metrics.add(base_metric)

    return metrics


def main() -> int:
    """Main validation logic."""
    # Determine project root (script is in tools/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    metrics_file = project_root / "app" / "core" / "metrics.py"
    dashboard_file = project_root / "tools" / "main-dashboard.json"

    print("🔍 Validating Grafana v11 dashboard and checking metrics coverage...")
    print()

    # Extract metrics (this also validates dashboard structure)
    declared_all, _declared_base = extract_declared_metrics(metrics_file)
    dashboard_raw, dashboard_normalized = extract_dashboard_metrics(dashboard_file)

    if not declared_all:
        print("❌ Error: No metrics found in metrics.py", file=sys.stderr)
        return 1

    if not dashboard_raw:
        # Error already printed by validation
        return 1

    print("✅ Dashboard structure is valid (Grafana v11)")
    print()

    print(f"📊 Found {len(declared_all)} metrics declared in code")
    print(f"📈 Found {len(dashboard_raw)} unique metric references in dashboard")
    print()

    # Find metrics that are declared but not covered in dashboard
    # A metric is considered "covered" if its base name appears in the normalized dashboard metrics
    missing_from_dashboard = set()
    for metric in declared_all:
        # Check if metric or its base name exists in dashboard
        base_name = re.sub(r"_(total|bucket|sum|count)$", "", metric)
        if metric not in dashboard_normalized and base_name not in dashboard_normalized:
            missing_from_dashboard.add(metric)

    # Report missing metrics
    if missing_from_dashboard:
        print("⚠️  Metrics declared in code but NOT in dashboard:")
        for metric in sorted(missing_from_dashboard):
            print(f"  - {metric}")
        print()

    # Summary
    if not missing_from_dashboard:
        print("✅ All declared metrics are covered in the dashboard!")
        coverage = len(declared_all) - len(missing_from_dashboard)
        print(f"   {coverage}/{len(declared_all)} metrics are tracked")
        return 0
    else:
        print("❌ Some metrics are missing from the dashboard")
        coverage = len(declared_all) - len(missing_from_dashboard)
        print(f"   {coverage}/{len(declared_all)} metrics are tracked")
        print(
            f"   Please run `uv run python scripts/generate_dashboard.py` to add {len(missing_from_dashboard)} missing metric(s) to the dashboard"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
