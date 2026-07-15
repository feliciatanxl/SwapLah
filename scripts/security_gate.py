"""Fail CI when GitLab security reports contain blocking findings."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

JSON_REPORT_GLOB = "*.json"
BLOCKING_SEVERITIES = {"High", "Critical"}


@dataclass(frozen=True)
class ReportSpec:
    """Expected GitLab security report metadata."""

    name: str
    scan_types: tuple[str, ...]
    expected_paths: tuple[Path, ...]


SECURITY_REPORTS = (
    ReportSpec("SAST", ("sast",), (Path("gl-sast-report.json"),)),
    ReportSpec(
        "Dependency scanning",
        ("dependency_scanning",),
        (Path("gl-dependency-scanning-report.json"),),
    ),
    ReportSpec(
        "Secret detection",
        ("secret_detection",),
        (Path("gl-secret-detection-report.json"),),
    ),
)


def _read_json(path):
    """Return parsed JSON from a report path."""
    return json.loads(path.read_text(encoding="utf-8"))


def _report_scan_type(report):
    """Return the GitLab security report scan type, if present."""
    scan = report.get("scan", {})

    if isinstance(scan, dict):
        return scan.get("type")

    return None


def _is_security_report(report, spec):
    """Return True when a parsed report matches the expected security type."""
    return _report_scan_type(report) in spec.scan_types


def _discover_report(spec):
    """Find and load the expected GitLab security report."""
    for path in spec.expected_paths:
        if path.exists():
            report = _read_json(path)

            if _is_security_report(report, spec):
                return path, report

            print(f"Ignoring {path}: scan.type is not one of {spec.scan_types}.")

    for path in sorted(Path(".").glob(JSON_REPORT_GLOB)):
        if path in spec.expected_paths:
            continue

        try:
            report = _read_json(path)
        except json.JSONDecodeError:
            continue

        if _is_security_report(report, spec):
            return path, report

    expected = ", ".join(str(path) for path in spec.expected_paths)
    print(
        f"Missing expected {spec.name} report. Expected {expected} "
        f"or a GitLab report with scan.type in {spec.scan_types}."
    )
    return None, None


def _finding_label(vulnerability):
    """Return a readable vulnerability label."""
    name = vulnerability.get("name") or vulnerability.get("message") or "Unnamed finding"
    severity = vulnerability.get("severity", "Unknown")
    location = vulnerability.get("location", {})
    dependency = location.get("dependency", {})
    file_path = location.get("file") or dependency.get("package", {}).get("name")
    return f"{severity}: {name}" + (f" ({file_path})" if file_path else "")


def _blocking_findings(report_name, report):
    """Return blocking findings from one parsed report."""
    findings = []

    for vulnerability in report.get("vulnerabilities", []):
        severity = vulnerability.get("severity")

        if report_name == "Secret detection" or severity in BLOCKING_SEVERITIES:
            findings.append(_finding_label(vulnerability))

    return findings


def main():
    """Inspect GitLab security reports and return a process exit code."""
    failed = False

    for spec in SECURITY_REPORTS:
        path, report = _discover_report(spec)

        if report is None:
            failed = True
            continue

        print(f"Loaded {spec.name} report: {path}")
        findings = _blocking_findings(spec.name, report)

        for finding in findings:
            print(f"Blocking {spec.name} finding: {finding}")

        failed = failed or bool(findings)

    if failed:
        return 1

    print("Security gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
