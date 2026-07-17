"""Fail the GitLab pipeline when security findings are detected."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


SECURITY_REPORTS = {
    "SAST": Path("gl-sast-report.json"),
    "Dependency Scanning": Path(
        "gl-dependency-scanning-report.json"
    ),
    "Secret Detection": Path(
        "gl-secret-detection-report.json"
    ),
}


def load_findings(
    report_name: str,
    report_path: Path,
) -> list[dict[str, Any]]:
    """Load vulnerabilities from one GitLab security report."""

    if not report_path.is_file():
        raise RuntimeError(
            f"{report_name} report is missing: {report_path}"
        )

    try:
        with report_path.open(
            "r",
            encoding="utf-8",
        ) as report_file:
            report = json.load(report_file)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"{report_name} report contains invalid JSON: {error}"
        ) from error
    except OSError as error:
        raise RuntimeError(
            f"{report_name} report could not be read: {error}"
        ) from error

    findings = report.get("vulnerabilities")

    if not isinstance(findings, list):
        raise RuntimeError(
            f"{report_name} report does not contain a valid "
            "'vulnerabilities' list."
        )

    return findings


def describe_finding(
    report_name: str,
    finding: dict[str, Any],
) -> str:
    """Return a safe finding description without printing secret values."""

    name = finding.get("name", "Unnamed security finding")
    severity = finding.get("severity", "Unknown")

    location = finding.get("location", {})
    file_path = location.get("file", "unknown location")
    start_line = location.get("start_line")

    if start_line is not None:
        location_text = f"{file_path}:{start_line}"
    else:
        location_text = str(file_path)

    return (
        f"[{report_name}] "
        f"{severity} - {name} - {location_text}"
    )


def main() -> int:
    """Check all reports and return a failing exit code if necessary."""

    all_findings: list[tuple[str, dict[str, Any]]] = []
    report_errors: list[str] = []

    print("=" * 65)
    print("GitLab Security Gate")
    print("=" * 65)

    for report_name, report_path in SECURITY_REPORTS.items():
        try:
            findings = load_findings(
                report_name,
                report_path,
            )
        except RuntimeError as error:
            report_errors.append(str(error))
            print(f"{report_name}: ERROR")
            continue

        print(
            f"{report_name}: "
            f"{len(findings)} finding(s)"
        )

        for finding in findings:
            all_findings.append(
                (report_name, finding)
            )

    if report_errors:
        print("\nSECURITY GATE BLOCKED")
        print("One or more security reports could not be verified:")

        for error in report_errors:
            print(f"- {error}")

        # Fail closed when a report is unavailable or invalid.
        return 1

    if all_findings:
        print("\nDetected security findings:")

        for report_name, finding in all_findings:
            print(
                "- "
                + describe_finding(
                    report_name,
                    finding,
                )
            )

        print("\nSECURITY GATE FAILED")
        print(
            f"{len(all_findings)} security finding(s) detected."
        )
        print("Build and deployment are blocked.")

        return 1

    print("\nSECURITY GATE PASSED")
    print("No security findings were detected.")

    return 0


if __name__ == "__main__":
    sys.exit(main())