import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set


AUDIO_EXTENSIONS = {".mp3", ".wav"}
SKIP_DIRECTORIES = {
    ".git",
    ".github",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
}


def get_repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def build_catalog(
    repository_root: Path, ignored_paths: Optional[Set[Path]] = None
) -> List[Dict[str, str]]:
    catalog = []
    ignored_paths = {path.resolve() for path in ignored_paths or set()}

    for root, directories, files in os.walk(repository_root):
        directories[:] = sorted(
            directory for directory in directories if directory not in SKIP_DIRECTORIES
        )

        for file_name in sorted(files):
            path = Path(root, file_name)

            if path.resolve() in ignored_paths:
                continue

            if path.suffix.lower() in AUDIO_EXTENSIONS:
                catalog.append(
                    {
                        "filename": path.name,
                        "path": path.relative_to(repository_root).as_posix(),
                    }
                )

    return sorted(catalog, key=lambda item: item["path"])


def write_catalog(catalog: List[Dict[str, str]], output_path: Path) -> None:
    output_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    repository_root = get_repository_root()
    output_path = repository_root / "catalog.json"
    catalog = build_catalog(repository_root, ignored_paths={output_path})
    write_catalog(catalog, output_path)
    print(f"Wrote {len(catalog)} audio files to {output_path.relative_to(repository_root)}")


if __name__ == "__main__":
    main()
