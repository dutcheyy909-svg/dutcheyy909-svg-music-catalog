from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
METADATA_DIR = ROOT_DIR / "metadata"
LATEST_METADATA_PATH = METADATA_DIR / "latest_metadata.json"
TRACK_FILES_TO_SKIP = {"latest_metadata.json", "sync_metadata.json", "track.schema.json"}
TRACK_REQUIRED_FIELDS = {"title", "composer", "bpm", "key", "genre"}
GENERATED_METADATA_MARKER = "logic_tools.extract_metadata"
TIMESTAMP_KEYS = ("updated_at", "updated", "created_at", "created")


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_valid_files_shape(files: Any) -> bool:
    if not isinstance(files, dict) or not files:
        return False
    if not {"wav", "mp3"}.issubset(files):
        return False
    for key, value in files.items():
        if not isinstance(key, str):
            return False
        if not is_nonempty_string(value):
            return False
    return True


def is_track_metadata(metadata: Any) -> bool:
    if not isinstance(metadata, dict):
        return False
    if metadata.get("_generated_by") == GENERATED_METADATA_MARKER:
        return False
    if not TRACK_REQUIRED_FIELDS.issubset(metadata):
        return False

    if not all(is_nonempty_string(metadata.get(field)) for field in ("title", "composer", "key", "genre")):
        return False

    bpm = metadata.get("bpm")
    if isinstance(bpm, bool) or not isinstance(bpm, (int, float)) or bpm <= 0:
        return False

    if "file_path" in metadata:
        if not is_nonempty_string(metadata["file_path"]):
            return False
    if "files" in metadata:
        if not is_valid_files_shape(metadata["files"]):
            return False
    if "file_path" not in metadata and "files" not in metadata:
        return False

    return True


def load_track_metadata(metadata_dir: Path = METADATA_DIR) -> list[tuple[Path, dict[str, Any]]]:
    tracks: list[tuple[Path, dict[str, Any]]] = []
    for metadata_file in sorted(metadata_dir.glob("*.json")):
        if metadata_file.name in TRACK_FILES_TO_SKIP:
            continue

        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if is_track_metadata(metadata):
            tracks.append((metadata_file, metadata))

    return tracks


def parse_metadata_timestamp(metadata: dict[str, Any]) -> datetime:
    timestamps: list[datetime] = []

    for key in TIMESTAMP_KEYS:
        value = metadata.get(key)
        if not is_nonempty_string(value):
            continue

        normalized = value.strip()
        if normalized.endswith(("Z", "z")):
            normalized = normalized[:-1] + "+00:00"
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


def build_latest_metadata(metadata_dir: Path = METADATA_DIR) -> dict[str, Any]:
    tracks = load_track_metadata(metadata_dir)
    if not tracks:
        raise ValueError(
            "No valid track metadata files found in "
            f"{metadata_dir}; expected JSON objects with title, composer, bpm, "
            "key, genre, and either file_path or files"
        )

    track_details = [
        (metadata_file, metadata, parse_metadata_timestamp(metadata))
        for metadata_file, metadata in tracks
    ]
    latest_timestamp = max(timestamp for _, _, timestamp in track_details)
    latest_candidates = [
        (metadata_file, metadata)
        for metadata_file, metadata, timestamp in track_details
        if timestamp == latest_timestamp
    ]
    latest_file, latest_metadata = min(latest_candidates, key=lambda track_detail: track_detail[0].name)

    result = dict(latest_metadata)
    result["metadata_file"] = latest_file.name
    result["_generated_by"] = GENERATED_METADATA_MARKER
    return result


def write_latest_metadata(
    output_path: Path = LATEST_METADATA_PATH,
    metadata_dir: Path = METADATA_DIR,
) -> Path:
    latest_metadata = build_latest_metadata(metadata_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=output_path.parent,
        prefix=f"{output_path.stem}-",
        suffix=".tmp",
        delete=False,
    ) as temp_file:
        temp_file.write(json.dumps(latest_metadata, indent=2, ensure_ascii=False) + "\n")
        temp_output_path = Path(temp_file.name)

    try:
        temp_output_path.replace(output_path)
    except OSError:
        temp_output_path.unlink(missing_ok=True)
        raise
    return output_path


if __name__ == "__main__":
    written_path = write_latest_metadata()
    print(f"Wrote latest metadata to {written_path}")
