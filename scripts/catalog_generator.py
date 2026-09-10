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


def _collect_string_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested_value in value.values():
            yield from _collect_string_values(nested_value)
    elif isinstance(value, list):
        for nested_value in value:
            yield from _collect_string_values(nested_value)


def _load_json_file(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def _build_metadata_index(root, output_path):
    metadata_index = {}

    for json_path in sorted(root.rglob("*.json"), key=lambda path: path.relative_to(root).as_posix()):
        if json_path.resolve() == output_path.resolve():
            continue

        data = _load_json_file(json_path)
        if not isinstance(data, dict):
            continue

        references = set()
        for value in _collect_string_values(data):
            normalized = _normalize_reference_path(value)
            if normalized and Path(normalized).suffix.lower() in AUDIO_EXTENSIONS:
                references.add(normalized.casefold())

        if not references:
            continue

        source = json_path.relative_to(root).as_posix()
        for reference in sorted(references):
            metadata_index.setdefault(reference, []).append((source, data))

    return metadata_index


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
    metadata_index = _build_metadata_index(root, output_path)
    tracks = []
    seen_paths = set()

    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().casefold()):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue

        relative_path = path.relative_to(root).as_posix()
        normalized_path = relative_path.casefold()
        if normalized_path in seen_paths:
            continue

        seen_paths.add(normalized_path)
        metadata_matches = metadata_index.get(normalized_path, [])

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
