# dutcheyy909-svg-music-catalog
repo for music-catalog
music-catalog/
{
  "README": {
    "title": "Dutcheyy Studio Music Catalog",
    "repository": "dutcheyy909-svg/music-catalog",
    "description": "A structured music catalog repository for managing Dutcheyy Studio music assets, production metadata, sync materials, lyrics, release information, workflows, and project files.",
    "purpose": [
      "Organize music catalog assets",
      "Track song and project metadata",
      "Store sync cue information",
      "Document vocal chains",
      "Manage stem metadata",
      "Store lyrics",
      "Document studio workflows",
      "Track releases",
      "Organize active and archived projects"
    ],
    "folder_structure": {
      "sync_cues": "Sync licensing cues, briefs, placements, usage notes, and cue metadata.",
      "vocal_chains": "Vocal recording, mixing, plugin, routing, and processing chain documentation.",
      "stems_metadata": "Metadata for instrumental, vocal, drum, bass, FX, and other stems.",
      "lyrics": "Song lyrics, lyric versions, clean edits, and lyric metadata.",
      "workflows": "Studio processes, production workflows, checklists, export procedures, and operating documentation.",
      "releases": "Release metadata, distribution information, dates, versions, artwork references, and platform details.",
      "projects": "Individual song, EP, album, client, production, and collaboration project records."
    },
    "recommended_file_formats": {
      "metadata": [
        ".json",
        ".yaml",
        ".csv"
      ],
      "documentation": [
        ".md",
        ".txt"
      ],
      "lyrics": [
        ".md",
        ".txt"
      ]
    },
    "repository_guidelines": [
      "Use consistent file and folder naming conventions.",
      "Prefer lowercase snake_case for machine-readable filenames.",
      "Do not commit passwords, API keys, tokens, or private credentials.",
      "Keep metadata structured and easy to search.",
      "Document significant project changes.",
      "Avoid committing large audio files unless Git LFS or another approved storage method is configured.",
      "Preserve original identifiers such as ISRC, UPC, catalog numbers, version names, and release dates when available."
    ],
    "example_project_structure": {
      "projects/example_song": [
        "metadata.json",
        "lyrics.md",
        "stems.json",
        "vocal_chain.json",
        "sync_cues.json",
        "notes.md"
      ]
    },
    "example_metadata": {
      "title": "Example Song",
      "artist": "Artist Name",
      "version": "master",
      "status": "in_progress",
      "bpm": 120,
      "key": "C minor",
      "isrc": null,
      "release_date": null
    },
    "git": {
      "default_branch": "main",
      "example_commit": "Add music catalog folder structure",
      "note": "Empty directories are not tracked by Git. Add a .gitkeep file when a directory needs to exist before content is added."
    },
    "maintainer": "Dutcheyy Studio"
  }
}
