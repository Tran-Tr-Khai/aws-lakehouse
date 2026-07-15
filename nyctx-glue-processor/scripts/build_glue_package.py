"""Build a zip artifact that AWS Glue can import via --extra-py-files."""

from __future__ import annotations

import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def build_package(output_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    source_root = project_root / "src"

    if not source_root.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_root}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as archive:
        for file_path in sorted(source_root.rglob("*.py")):
            archive.write(file_path, file_path.relative_to(source_root))


def main(argv: list[str] | None = None) -> None:
    args = argv or sys.argv[1:]
    if len(args) != 1:
        raise SystemExit("Usage: build_glue_package.py <output-zip-path>")
    build_package(Path(args[0]).resolve())


if __name__ == "__main__":
    main()
