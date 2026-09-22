import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "catalog.json"
AUDIO_EXTENSIONS = {".mp3", ".wav"}
SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    "build",
    "dist",
    "generated",
    "node_modules",
    "output",
}
SKIP_FILE_NAMES = {OUTPUT_PATH.name, "CATALOG.md"}


def build_catalog(repo_root: Path) -> list[dict[str, str]]:
    entries_by_path = {}

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = sorted(directory for directory in dirs if directory not in SKIP_DIR_NAMES)
        root_path = Path(root)

        for filename in sorted(files):
            if filename in SKIP_FILE_NAMES:
                continue

            file_path = root_path / filename
            if file_path.suffix.lower() not in AUDIO_EXTENSIONS:
                continue

            relative_path = file_path.relative_to(repo_root).as_posix()
            entries_by_path[relative_path] = {
                "filename": filename,
                "path": relative_path,
            }

    return [entries_by_path[path] for path in sorted(entries_by_path)]


def write_catalog(catalog: list[dict[str, str]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as file_handle:
        json.dump(catalog, file_handle, indent=2)


def main() -> None:
    catalog = build_catalog(REPO_ROOT)
    write_catalog(catalog, OUTPUT_PATH)
    print(f"Found {len(catalog)} audio files")


if __name__ == "__main__":
    main()
