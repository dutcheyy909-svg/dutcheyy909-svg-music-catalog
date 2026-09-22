"""Compatibility wrapper for the canonical project data analyzer module."""

import projectdata_analyzer as _analyzer

csv = _analyzer.csv
defaultdict = _analyzer.defaultdict
json = _analyzer.json
librosa = _analyzer.librosa
LOGGER = _analyzer.LOGGER
np = _analyzer.np
Path = _analyzer.Path

__all__ = list(_analyzer.__all__)

for name in __all__:
    globals()[name] = getattr(_analyzer, name)
