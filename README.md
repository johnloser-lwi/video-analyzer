# Video Analyzer

Analyze a folder of video files and generate a SQLite catalog with technical metadata **and AI-powered content descriptions**. The database is saved alongside your videos, and subsequent runs only process new or modified files.

## Prerequisites

- **Python 3.10+**
- **FFmpeg / FFprobe** — [Download](https://ffmpeg.org/download.html) or `winget install ffmpeg`
- **Ollama** — [Download](https://ollama.ai) with a vision model:
  ```bash
  ollama pull llava
  ```

## Installation

```bash
cd video-analyzer
pip install -e .
```

## Usage

```bash
# Analyze a folder (recursive by default, skips proxy files/folders)
video-analyzer "D:\My Videos"

# Metadata only (no AI analysis)
video-analyzer "D:\My Videos" --metadata-only

# Force re-analyze everything
video-analyzer "D:\My Videos" --force

# Export to CSV
video-analyzer "D:\My Videos" --export-csv

# Clean up entries for deleted files
video-analyzer "D:\My Videos" --clean

# Use a different vision model
video-analyzer "D:\My Videos" --model llava:13b

# Verbose output
video-analyzer "D:\My Videos" -v

# Non-recursive scan
video-analyzer "D:\My Videos" --no-recursive
```

You can also run it as a Python module:

```bash
python -m video_analyzer "D:\My Videos"
```

## How It Works

1. **Scans** the folder recursively for video files (skips files/folders with "proxy" in the name)
2. **Checks** the local `video_catalog.db` to see which files are new or modified
3. **Extracts metadata** (duration, resolution, codec, bitrate, etc.) via FFprobe
4. **Extracts keyframes** from each video and sends them to Ollama/LLaVA for AI content analysis
5. **Stores** everything in `video_catalog.db` inside the video folder

On subsequent runs, only **new or modified** files are processed.

## Database

The catalog is stored as `video_catalog.db` (SQLite) in the root of the scanned folder. Each video entry contains:

| Field | Description |
|---|---|
| `filename` | File name |
| `filepath` | Absolute path |
| `relative_path` | Path relative to the scanned folder |
| `file_size` / `file_size_human` | Size in bytes and human-readable |
| `duration` / `duration_formatted` | Duration in seconds and HH:MM:SS |
| `resolution_w` × `resolution_h` | Video resolution |
| `video_codec` / `audio_codec` | Codecs used |
| `bitrate` / `framerate` | Bitrate and frame rate |
| `container_format` | Container format (mp4, mkv, etc.) |
| `scene_description` | AI: detailed scene description |
| `key_objects` | AI: detected objects and people |
| `actions` | AI: observed activities |
| `setting` | AI: environment/location type |
| `screen_text` | AI: any visible text |
| `content_summary` | AI: concise 1-2 sentence summary |
| `analyzed_at` | Timestamp of last analysis |

## Supported Formats

`.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.mpg`, `.mpeg`, `.ts`, `.3gp`, `.mts`, `.m2ts`, `.vob`, `.ogv`, `.rm`, `.rmvb`
