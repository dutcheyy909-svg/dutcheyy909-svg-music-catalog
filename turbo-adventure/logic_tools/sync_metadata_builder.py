from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from extract_metadata import METADATA_DIR, load_track_metadata

SYNC_METADATA_PATH = METADATA_DIR / "sync_metadata.json"
SUMMARY_FIELDS = ("title", "composer", "bpm", "key", "genre", "subgenre")


def build_track_summary(metadata_file: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    summary = {field: metadata[field] for field in SUMMARY_FIELDS if field in metadata}
    summary["metadata_file"] = metadata_file.name

    if "mood" in metadata:
        summary["mood"] = metadata["mood"]
    elif "mood_tags" in metadata:
        summary["mood"] = metadata["mood_tags"]

    if "file_path" in metadata:
        summary["file_path"] = metadata["file_path"]
    if "files" in metadata:
        summary["files"] = metadata["files"]

    return summary


def build_sync_metadata_index(metadata_dir: Path = METADATA_DIR) -> dict[str, Any]:
    tracks = [
        build_track_summary(metadata_file, metadata)
        for metadata_file, metadata in load_track_metadata(metadata_dir)
    ]
    tracks.sort(key=lambda track: track.get("title", ""))

    return {
        "project": "turbo-adventure",
        "track_count": len(tracks),
        "tracks": tracks,
    }


def write_sync_metadata(
    output_path: Path = SYNC_METADATA_PATH,
    metadata_dir: Path = METADATA_DIR,
) -> Path:
    sync_metadata = build_sync_metadata_index(metadata_dir)
    output_path.write_text(
        json.dumps(sync_metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


if __name__ == "__main__":
    written_path = write_sync_metadata()
    print(f"Wrote sync metadata to {written_path}")
