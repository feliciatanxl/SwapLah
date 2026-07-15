"""Fail CI when GitLab security reports contain blocking findings."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SECURITY_REPORTS = {
    "SAST": Path("gl-sast-report.json"),
    "Dependency scanning": Path("gl-dependency-scanning-report.json"),
    "Secret detection": Path("gl-secret-detection-report.json"),
}
BLOCKING_SEVERITIES = {"High", "Critical"}


def _load_report(report_name, path):
    """Load one GitLab security report or fail if it is missing."""
    if not path.exists():
        print(f"Missing expected {report_name} report: {path}")
        return None

    return json.loads(path.read_text(encoding="utf-8"))


def _finding_label(vulnerability):
    """Return a readable vulnerability label."""
    name = vulnerability.get("name") or vulnerability.get("message") or "Unnamed finding"
    severity = vulnerability.get("severity", "Unknown")
    location = vulnerability.get("location", {})
    file_path = location.get("file") or location.get("dependency", {}).get("package", {}).get("name")
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

    for report_name, path in SECURITY_REPORTS.items():
        report = _load_report(report_name, path)

        if report is None:
            failed = True
            continue

        findings = _blocking_findings(report_name, report)

        for finding in findings:
            print(f"Blocking {report_name} finding: {finding}")

        failed = failed or bool(findings)

    if failed:
        return 1

    print("Security gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
