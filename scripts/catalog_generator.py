import json
import posixpath
from pathlib import Path


AUDIO_EXTENSIONS = {".mp3", ".wav"}
CATALOG_FILENAME = "catalog.json"
METADATA_KEYS = (
    "title",
    "artist",
    "composer",
    "album",
    "project",
    "genre",
    "subgenre",
    "mood",
    "mood_tags",
    "bpm",
    "key",
    "duration",
    "description",
)


def _normalize_reference_path(value):
    if not isinstance(value, str):
        return None

    normalized = posixpath.normpath(value.replace("\\", "/").strip())
    if normalized in {"", "."} or normalized.startswith("../"):
        return None

    return normalized.lstrip("./")


def _extract_audio_references(data):
    references = set()

    for key in ("file_path", "file", "wav", "mp3"):
        normalized = _normalize_reference_path(data.get(key))
        if normalized and Path(normalized).suffix.lower() in AUDIO_EXTENSIONS:
            references.add(normalized)

    files = data.get("files")
    if isinstance(files, dict):
        for value in files.values():
            normalized = _normalize_reference_path(value)
            if normalized and Path(normalized).suffix.lower() in AUDIO_EXTENSIONS:
                references.add(normalized)

    return references


def _load_json_file(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def _build_metadata_index(root, output_path):
    exact_index = {}

    for json_path in sorted(root.rglob("*.json"), key=lambda path: path.relative_to(root).as_posix()):
        if json_path.resolve() == output_path.resolve():
            continue

        data = _load_json_file(json_path)
        if not isinstance(data, dict):
            continue

        references = _extract_audio_references(data)
        if not references:
            continue

        source = json_path.relative_to(root).as_posix()
        for reference in sorted(references):
            exact_index.setdefault(reference, []).append((source, data))

    return exact_index


def _merge_metadata(matches):
    metadata = {}

    for _, data in matches:
        for key in METADATA_KEYS:
            value = data.get(key)
            if value in (None, "", [], {}):
                continue
            metadata.setdefault(key, value)

    return metadata


def build_catalog(root):
    output_path = root / CATALOG_FILENAME
    exact_metadata_index = _build_metadata_index(root, output_path)
    tracks = []
    seen_paths = set()
    audio_paths = sorted(
        root.rglob("*"),
        key=lambda item: (
            item.relative_to(root).as_posix().casefold(),
            item.relative_to(root).as_posix(),
        ),
    )

    for path in audio_paths:
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue

        relative_path = path.relative_to(root).as_posix()
        if relative_path in seen_paths:
            continue

        seen_paths.add(relative_path)
        metadata_matches = exact_metadata_index.get(relative_path, [])

        track = {
            "filename": path.name,
            "relative_path": relative_path,
            "extension": path.suffix.lower(),
            "size_bytes": path.stat().st_size,
        }

        merged_metadata = _merge_metadata(metadata_matches)
        if merged_metadata:
            track["metadata"] = merged_metadata

        if metadata_matches:
            track["metadata_sources"] = [source for source, _ in metadata_matches]

        tracks.append(track)

    return {"tracks": tracks}


def write_catalog(root):
    catalog = build_catalog(root)
    output_path = root / CATALOG_FILENAME
    output_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    return catalog


def main():
    root = Path.cwd()
    catalog = write_catalog(root)
    print(f"Wrote {len(catalog['tracks'])} tracks to {CATALOG_FILENAME}")


if __name__ == "__main__":
    main()
