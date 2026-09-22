from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
METADATA_DIR = ROOT_DIR / "metadata"
LATEST_METADATA_PATH = METADATA_DIR / "latest_metadata.json"
TRACK_FILES_TO_SKIP = {"latest_metadata.json", "sync_metadata.json", "track.schema.json"}
TRACK_REQUIRED_FIELDS = {"title", "composer", "bpm", "key", "genre"}
TIMESTAMP_KEYS = ("updated_at", "updated", "created_at", "created")


def is_track_metadata(metadata: Any) -> bool:
    if not isinstance(metadata, dict):
        return False
    if not TRACK_REQUIRED_FIELDS.issubset(metadata):
        return False
    return "file_path" in metadata or "files" in metadata


def load_track_metadata(metadata_dir: Path = METADATA_DIR) -> list[tuple[Path, dict[str, Any]]]:
    tracks: list[tuple[Path, dict[str, Any]]] = []
    for metadata_file in sorted(metadata_dir.glob("*.json")):
        if metadata_file.name in TRACK_FILES_TO_SKIP:
            continue

        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        if is_track_metadata(metadata):
            tracks.append((metadata_file, metadata))

    return tracks


def parse_metadata_timestamp(metadata: dict[str, Any]) -> datetime:
    timestamps: list[datetime] = []

    for key in TIMESTAMP_KEYS:
        value = metadata.get(key)
        if not value:
            continue

        normalized = str(value).replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            continue

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        timestamps.append(parsed)

    if timestamps:
        return max(timestamps)

    return datetime.min.replace(tzinfo=timezone.utc)


def latest_track_sort_key(track: tuple[Path, dict[str, Any]]) -> tuple[datetime, str, str]:
    metadata = track[1]
    return (
        parse_metadata_timestamp(metadata),
        str(metadata.get("title", "")),
        str(metadata.get("composer", "")),
    )


def build_latest_metadata(metadata_dir: Path = METADATA_DIR) -> dict[str, Any]:
    tracks = load_track_metadata(metadata_dir)
    if not tracks:
        raise ValueError(
            "No valid track metadata files found in "
            f"{metadata_dir}; expected JSON objects with title, composer, bpm, "
            "key, genre, and either file_path or files"
        )

    latest_file, latest_metadata = max(tracks, key=latest_track_sort_key)

    result = dict(latest_metadata)
    result["metadata_file"] = latest_file.name
    return result


def write_latest_metadata(
    output_path: Path = LATEST_METADATA_PATH,
    metadata_dir: Path = METADATA_DIR,
) -> Path:
    latest_metadata = build_latest_metadata(metadata_dir)
    output_path.write_text(
        json.dumps(latest_metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path


if __name__ == "__main__":
    written_path = write_latest_metadata()
    print(f"Wrote latest metadata to {written_path}")
