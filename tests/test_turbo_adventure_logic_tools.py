import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TURBO_ADVENTURE_DIR = REPO_ROOT / "turbo-adventure"

if str(TURBO_ADVENTURE_DIR) not in sys.path:
    sys.path.insert(0, str(TURBO_ADVENTURE_DIR))

extract_metadata = importlib.import_module("logic_tools.extract_metadata")
sync_metadata_builder = importlib.import_module("logic_tools.sync_metadata_builder")


@pytest.fixture
def metadata_dir(tmp_path):
    for name, payload in {
        "track_b.json": {
            "title": "Track B",
            "composer": "Duncan",
            "bpm": 120,
            "key": "A Minor",
            "genre": "Pop",
            "created": "2026-09-20",
            "mood": ["bright"],
            "file_path": "tracks/track_b.wav",
        },
        "track_a.json": {
            "title": "Track A",
            "composer": "Duncan",
            "bpm": 100,
            "key": "C Major",
            "genre": "Electronic",
            "updated_at": "2026-09-21T10:15:00Z",
            "mood_tags": ["driving"],
            "files": {
                "wav": "tracks/track_a.wav",
                "mp3": "tracks/track_a.mp3",
            },
        },
        "manifest.json": {
            "generated_at": "2026-09-22T10:00:00Z",
            "track_count": 99,
        },
        "sync_metadata.json": {"skip": True},
        "latest_metadata.json": {"skip": True},
        "track.schema.json": {"skip": True},
    }.items():
        (tmp_path / name).write_text(json.dumps(payload), encoding="utf-8")

    return tmp_path


def test_build_latest_metadata_picks_newest_track(metadata_dir):
    latest = extract_metadata.build_latest_metadata(metadata_dir)

    assert latest["title"] == "Track A"
    assert latest["metadata_file"] == "track_a.json"
    assert "files" in latest


def test_parse_metadata_timestamp_supports_supported_keys_and_z_suffix():
    parsed = extract_metadata.parse_metadata_timestamp({"updated_at": "2026-09-21T10:15:00Z"})
    fallback = extract_metadata.parse_metadata_timestamp({"created": "2026-09-20"})

    assert parsed.isoformat() == "2026-09-21T10:15:00+00:00"
    assert fallback.isoformat() == "2026-09-20T00:00:00+00:00"



def test_parse_metadata_timestamp_uses_newest_supported_timestamp():
    parsed = extract_metadata.parse_metadata_timestamp(
        {
            "updated_at": "2026-09-20T10:15:00Z",
            "created_at": "2026-09-21T09:00:00Z",
        }
    )

    assert parsed.isoformat() == "2026-09-21T09:00:00+00:00"


def test_load_track_metadata_ignores_non_track_json_objects(metadata_dir):
    tracks = extract_metadata.load_track_metadata(metadata_dir)

    assert [metadata_file.name for metadata_file, _ in tracks] == ["track_a.json", "track_b.json"]


def test_load_track_metadata_rejects_invalid_present_source_fields(tmp_path):
    for name, payload in {
        "valid.json": {
            "title": "Valid Track",
            "composer": "Duncan",
            "bpm": 128,
            "key": "E Minor",
            "genre": "Electronic",
            "file_path": "tracks/valid.wav",
        },
        "invalid_files_shape.json": {
            "title": "Invalid Files Shape",
            "composer": "Duncan",
            "bpm": 129,
            "key": "F Minor",
            "genre": "Electronic",
            "file_path": "tracks/invalid-files.wav",
            "files": [],
        },
        "invalid_file_path_type.json": {
            "title": "Invalid File Path Type",
            "composer": "Duncan",
            "bpm": 130,
            "key": "G Minor",
            "genre": "Electronic",
            "file_path": None,
            "files": {
                "wav": "tracks/invalid-path.wav",
                "mp3": "tracks/invalid-path.mp3",
            },
        },
        "invalid_stems_folder.json": {
            "title": "Invalid Stems Folder",
            "composer": "Duncan",
            "bpm": 131,
            "key": "A Minor",
            "genre": "Electronic",
            "files": {
                "wav": "tracks/invalid-stems.wav",
                "mp3": "tracks/invalid-stems.mp3",
                "stems_folder": None,
            },
        },
    }.items():
        (tmp_path / name).write_text(json.dumps(payload), encoding="utf-8")

    tracks = extract_metadata.load_track_metadata(tmp_path)

    assert [metadata_file.name for metadata_file, _ in tracks] == ["valid.json"]


def test_load_track_metadata_rejects_invalid_required_field_types(tmp_path):
    (tmp_path / "invalid_bpm.json").write_text(
        json.dumps(
            {
                "title": "Invalid BPM",
                "composer": "Duncan",
                "bpm": True,
                "key": "A Minor",
                "genre": "Electronic",
                "file_path": "tracks/invalid-bpm.wav",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "nan_bpm.json").write_text(
        json.dumps(
            {
                "title": "NaN BPM",
                "composer": "Duncan",
                "bpm": float("nan"),
                "key": "A Minor",
                "genre": "Electronic",
                "file_path": "tracks/nan-bpm.wav",
            },
            allow_nan=True,
        ),
        encoding="utf-8",
    )
    (tmp_path / "infinite_bpm.json").write_text(
        json.dumps(
            {
                "title": "Infinite BPM",
                "composer": "Duncan",
                "bpm": float("inf"),
                "key": "A Minor",
                "genre": "Electronic",
                "file_path": "tracks/infinite-bpm.wav",
            },
            allow_nan=True,
        ),
        encoding="utf-8",
    )
    (tmp_path / "invalid_title.json").write_text(
        json.dumps(
            {
                "title": "   ",
                "composer": "Duncan",
                "bpm": 120,
                "key": "A Minor",
                "genre": "Electronic",
                "file_path": "tracks/invalid-title.wav",
            }
        ),
        encoding="utf-8",
    )

    assert extract_metadata.load_track_metadata(tmp_path) == []



def test_build_latest_metadata_uses_metadata_tiebreaker_instead_of_filename(tmp_path):
    for name, payload in {
        "zeta.json": {
            "title": "Alpha",
            "composer": "Duncan",
            "bpm": 110,
            "key": "C Major",
            "genre": "Pop",
            "updated_at": "2026-09-21T10:15:00Z",
            "file_path": "tracks/alpha.wav",
        },
        "alpha.json": {
            "title": "Zeta",
            "composer": "Duncan",
            "bpm": 111,
            "key": "D Major",
            "genre": "Pop",
            "updated_at": "2026-09-21T10:15:00Z",
            "file_path": "tracks/zeta.wav",
        },
    }.items():
        (tmp_path / name).write_text(json.dumps(payload), encoding="utf-8")

    latest = extract_metadata.build_latest_metadata(tmp_path)

    assert latest["title"] == "Zeta"
    assert latest["metadata_file"] == "alpha.json"




def test_build_latest_metadata_uses_filename_only_for_exact_metadata_ties(tmp_path):
    duplicate_payload = {
        "title": "Shared Title",
        "composer": "Duncan",
        "bpm": 110,
        "key": "C Major",
        "genre": "Pop",
        "updated_at": "2026-09-21T10:15:00Z",
        "file_path": "tracks/shared.wav",
    }

    for name in ["alpha.json", "zeta.json"]:
        (tmp_path / name).write_text(json.dumps(duplicate_payload), encoding="utf-8")

    latest = extract_metadata.build_latest_metadata(tmp_path)

    assert latest["metadata_file"] == "alpha.json"


def test_write_latest_metadata_serializes_metadata_file(metadata_dir, tmp_path):
    output_path = tmp_path / "latest_metadata.json"

    written_path = extract_metadata.write_latest_metadata(output_path=output_path, metadata_dir=metadata_dir)
    written = json.loads(written_path.read_text(encoding="utf-8"))

    assert written_path == output_path
    assert written["metadata_file"] == "track_a.json"
    assert written["_generated_by"] == extract_metadata.GENERATED_METADATA_MARKER
    assert written["title"] == "Track A"
    assert output_path.read_text(encoding="utf-8").endswith("\n")



def test_generated_latest_outputs_are_not_retreated_as_source_tracks(metadata_dir):
    derived_output = metadata_dir / "custom_latest_snapshot.json"
    extract_metadata.write_latest_metadata(output_path=derived_output, metadata_dir=metadata_dir)

    latest = extract_metadata.build_latest_metadata(metadata_dir)
    track_files = [metadata_file.name for metadata_file, _ in extract_metadata.load_track_metadata(metadata_dir)]

    assert latest["metadata_file"] == "track_a.json"
    assert "custom_latest_snapshot.json" not in track_files


def test_write_sync_metadata_serializes_track_index(metadata_dir, tmp_path):
    output_path = tmp_path / "sync_metadata.json"

    written_path = sync_metadata_builder.write_sync_metadata(output_path=output_path, metadata_dir=metadata_dir)
    written = json.loads(written_path.read_text(encoding="utf-8"))

    assert written_path == output_path
    assert written["project"] == "turbo-adventure"
    assert written["track_count"] == 2
    assert written["tracks"][0]["metadata_file"] == "track_a.json"
    assert output_path.read_text(encoding="utf-8").endswith("\n")


def test_build_sync_metadata_index_sorts_and_filters_tracks(metadata_dir):
    sync_index = sync_metadata_builder.build_sync_metadata_index(metadata_dir)

    assert sync_index["project"] == "turbo-adventure"
    assert sync_index["track_count"] == 2
    assert [track["title"] for track in sync_index["tracks"]] == ["Track A", "Track B"]
    assert sync_index["tracks"][0]["metadata_file"] == "track_a.json"
    assert sync_index["tracks"][0]["mood"] == ["driving"]
    assert sync_index["tracks"][0]["files"]["mp3"] == "tracks/track_a.mp3"
    assert sync_index["tracks"][1]["mood"] == ["bright"]
    assert sync_index["tracks"][1]["file_path"] == "tracks/track_b.wav"
