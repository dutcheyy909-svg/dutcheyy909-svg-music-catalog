import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LOGIC_TOOLS_DIR = REPO_ROOT / "turbo-adventure" / "logic_tools"

if str(LOGIC_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(LOGIC_TOOLS_DIR))

extract_metadata = importlib.import_module("extract_metadata")
sync_metadata_builder = importlib.import_module("sync_metadata_builder")


@pytest.fixture
def metadata_dir(tmp_path):
    for name, payload in {
        "track_b.json": {
            "title": "Track B",
            "composer": "Duncan",
            "bpm": 120,
            "key": "A Minor",
            "genre": "Pop",
            "created_at": "2026-09-20",
            "file_path": "tracks/track_b.wav",
        },
        "track_a.json": {
            "title": "Track A",
            "composer": "Duncan",
            "bpm": 100,
            "key": "C Major",
            "genre": "Electronic",
            "updated": "2026-09-21",
            "mood_tags": ["driving"],
            "files": {
                "wav": "tracks/track_a.wav",
                "mp3": "tracks/track_a.mp3",
            },
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


def test_build_sync_metadata_index_sorts_and_filters_tracks(metadata_dir):
    sync_index = sync_metadata_builder.build_sync_metadata_index(metadata_dir)

    assert sync_index["project"] == "turbo-adventure"
    assert sync_index["track_count"] == 2
    assert [track["title"] for track in sync_index["tracks"]] == ["Track A", "Track B"]
    assert sync_index["tracks"][0]["metadata_file"] == "track_a.json"
