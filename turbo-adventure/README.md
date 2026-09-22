# Turbo Adventure metadata tools

The `turbo-adventure` folder contains track metadata plus two small helper scripts in `logic_tools/`:

- `extract_metadata.py` writes `metadata/latest_metadata.json` from the newest track metadata file.
- `sync_metadata_builder.py` writes `metadata/sync_metadata.json` as a compact sync-ready index of the tracked songs.

## Usage

From the repository root:

```bash
python turbo-adventure/logic_tools/extract_metadata.py
python turbo-adventure/logic_tools/sync_metadata_builder.py
```

The scripts use the checked-in JSON metadata files in `turbo-adventure/metadata` and only rely on the Python standard library.
