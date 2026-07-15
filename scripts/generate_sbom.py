"""Generate a deterministic CycloneDX SBOM from requirement files."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

PINNED_REQUIREMENT_RE = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s#]+)")


def _requirement_lines(path: Path, seen: set[Path] | None = None):
    """Yield requirement lines, resolving local -r includes."""
    seen = seen or set()
    path = path.resolve()

    if path in seen:
        return

    seen.add(path)

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("-r "):
            include = path.parent / line.removeprefix("-r ").strip()
            yield from _requirement_lines(include, seen)
            continue

        yield line


def _components(requirement_files):
    """Return CycloneDX components from pinned requirement files."""
    components = {}

    for requirement_file in requirement_files:
        for line in _requirement_lines(Path(requirement_file)):
            match = PINNED_REQUIREMENT_RE.match(line)

            if not match:
                raise ValueError(f"Requirement must be pinned with ==: {line}")

            name, version = match.groups()
            key = name.lower()
            components[key] = {
                "type": "library",
                "name": name,
                "version": version,
                "purl": f"pkg:pypi/{key}@{version}",
            }

    return [components[key] for key in sorted(components)]


def generate_sbom(requirement_files):
    """Build a CycloneDX JSON document."""
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "component": {
                "type": "application",
                "name": "swaplah",
            },
        },
        "components": _components(requirement_files),
    }


def main():
    """Parse CLI arguments and write the SBOM."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r",
        "--requirements",
        action="append",
        required=True,
        help="Requirement file to include. May be supplied multiple times.",
    )
    parser.add_argument("-o", "--output", required=True, help="SBOM JSON output path.")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(generate_sbom(args.requirements), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Generated CycloneDX SBOM: {output_path}")


if __name__ == "__main__":
    main()
