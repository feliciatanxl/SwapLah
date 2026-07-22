"""Create a reproducible SwapLah source archive for CI."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

SOURCE_DATE = (2026, 1, 1, 0, 0, 0)
INCLUDE_FILES = [
    Path(".env.example"),
    Path("README.md"),
    Path("requirements.txt"),
    Path("requirements-dev.txt"),
    Path("run.py"),
    Path("setup.cfg"),
    Path("pytest.ini"),
]
INCLUDE_DIRS = [Path("app"), Path("postman"), Path("scripts")]
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".pylint-cache",
    "reports",
    "dist",
    "build",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".db", ".sqlite", ".sqlite3", ".log"}
EXCLUDED_NAMES = {".env", ".coverage", "swaplah.db", "swaplah-sbom.cdx.json"}


def _is_excluded(path: Path):
    """Return True when a path should not be packaged."""
    return (
        path.name in EXCLUDED_NAMES
        or path.suffix in EXCLUDED_SUFFIXES
        or any(part in EXCLUDED_PARTS for part in path.parts)
    )


def _source_files():
    """Yield all source files for the build archive."""
    for path in INCLUDE_FILES:
        if path.exists() and not _is_excluded(path):
            yield path

    for directory in INCLUDE_DIRS:
        for path in directory.rglob("*"):
            if path.is_file() and not _is_excluded(path):
                yield path


def _write_file(archive, path):
    """Write one file with stable metadata."""
    info = zipfile.ZipInfo(str(path).replace("\\", "/"), SOURCE_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, path.read_bytes())


def build_archive(output_path):
    """Create the build archive and return the included files."""
    files = sorted(set(_source_files()), key=lambda item: str(item).lower())
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w") as archive:
        for path in files:
            _write_file(archive, path)

    return files


def main():
    """Parse CLI arguments and build the source archive."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--output",
        default="dist/swaplah-build.zip",
        help="Archive output path.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    files = build_archive(output_path)
    print(f"Built {output_path} with {len(files)} files.")


if __name__ == "__main__":
    main()
