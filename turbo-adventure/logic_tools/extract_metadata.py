from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
METADATA_DIR = ROOT_DIR / "metadata"
LATEST_METADATA_PATH = METADATA_DIR / "latest_metadata.json"
TRACK_FILES_TO_SKIP = {"latest_metadata.json", "sync_metadata.json", "track.schema.json"}
TRACK_REQUIRED_FIELDS = {"title", "composer", "bpm", "key", "genre"}
TRACK_REQUIRED_STRING_FIELDS = ("title", "composer", "key", "genre")
GENERATED_METADATA_MARKER = "logic_tools.extract_metadata"
TIMESTAMP_KEYS = ("updated_at", "updated", "created_at", "created")


def has_valid_file_path(metadata: dict[str, Any]) -> bool:
    file_path = metadata.get("file_path")
    return isinstance(file_path, str) and bool(file_path.strip())


def has_valid_files(metadata: dict[str, Any]) -> bool:
    files = metadata.get("files")
    if not isinstance(files, dict):
        return False

    wav = files.get("wav")
    mp3 = files.get("mp3")
    if not isinstance(wav, str) or not wav.strip():
        return False
    if not isinstance(mp3, str) or not mp3.strip():
        return False

    stems_folder = files.get("stems_folder")
    if "stems_folder" in files and (
        not isinstance(stems_folder, str) or not stems_folder.strip()
    ):
        return False

    return True


def has_valid_required_fields(metadata: dict[str, Any]) -> bool:
    for field in TRACK_REQUIRED_STRING_FIELDS:
        value = metadata.get(field)
        if not isinstance(value, str) or not value.strip():
            return False

    bpm = metadata.get("bpm")
    if (
        isinstance(bpm, bool)
        or not isinstance(bpm, (int, float))
        or not math.isfinite(bpm)
        or bpm <= 0
    ):
        return False

    return True


def has_invalid_present_source_fields(metadata: dict[str, Any]) -> bool:
    if "file_path" in metadata and not has_valid_file_path(metadata):
        return True
    if "files" in metadata and not has_valid_files(metadata):
        return True

    return False


def is_track_metadata(metadata: Any) -> bool:
    if not isinstance(metadata, dict):
        return False
    if metadata.get("_generated_by") == GENERATED_METADATA_MARKER:
        return False
    if not TRACK_REQUIRED_FIELDS.issubset(metadata):
        return False
    if not has_valid_required_fields(metadata):
        return False
    if has_invalid_present_source_fields(metadata):
        return False

    return has_valid_file_path(metadata) or has_valid_files(metadata)


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


def metadata_signature(metadata: dict[str, Any]) -> str:
    return json.dumps(metadata, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def build_latest_metadata(metadata_dir: Path = METADATA_DIR) -> dict[str, Any]:
    tracks = load_track_metadata(metadata_dir)
    if not tracks:
        raise ValueError(
            "No valid track metadata files found in "
            f"{metadata_dir}; expected JSON objects with title, composer, bpm, "
            "key, genre, and either a non-empty file_path or files with wav/mp3 paths"
        )

    track_details = [
        (metadata_file, metadata, parse_metadata_timestamp(metadata), metadata_signature(metadata))
        for metadata_file, metadata in tracks
    ]
    latest_timestamp = max(timestamp for _, _, timestamp, _ in track_details)
    latest_candidates = [
        track_detail
        for track_detail in track_details
        if track_detail[2] == latest_timestamp
    ]
    strongest_signature = max(signature for _, _, _, signature in latest_candidates)
    strongest_candidates = [
        track_detail
        for track_detail in latest_candidates
        if track_detail[3] == strongest_signature
    ]
    latest_file, latest_metadata, _, _ = min(
        strongest_candidates,
        key=lambda track_detail: track_detail[0].name,
    )

    result = dict(latest_metadata)
    result["metadata_file"] = latest_file.name
    result["_generated_by"] = GENERATED_METADATA_MARKER
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
