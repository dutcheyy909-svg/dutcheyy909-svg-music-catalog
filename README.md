# dutcheyy909-svg-music-catalog

## Overview
A structured music catalog repository for track metadata, release and sync cue schemas, and lightweight automation around generated repository artifacts.

## Repository Layout
- `music-catalog/projects/` contains project metadata schemas, fixtures, and dashboard tooling.
- `turbo-adventure/metadata/` stores track metadata plus derived JSON outputs used by the helper scripts.
- `releases/` and `sync_cues/` provide example payloads and JSON schemas for release and sync licensing data.
- `automation/` contains the README template, structured README data, and the generator script.
- `scripts/` and `tests/` contain repository automation and regression coverage.

## Automation
- Generate the repository README from the repository root with `python automation/scripts/generate-readme.py`.
- Refresh the audio catalog with `python scripts/catalog_generator.py`.
- Rebuild Turbo Adventure derived metadata with `python turbo-adventure/logic_tools/extract_metadata.py` and `python turbo-adventure/logic_tools/sync_metadata_builder.py`.

## Validation
- Run focused README regression checks with `pytest -q tests/test_generate_readme.py tests/test_auto_update_readme_workflow.py`.
- GitHub Actions also validates Python syntax, JSON schemas, and generated artifacts such as `README.md` and `catalog.json`.
