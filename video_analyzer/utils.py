"""Utility functions for file discovery, filtering, and formatting."""

import os
from pathlib import Path
from typing import List

# Supported video file extensions
VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
    ".webm", ".m4v", ".mpg", ".mpeg", ".ts", ".3gp",
    ".mts", ".m2ts", ".vob", ".ogv", ".rm", ".rmvb",
}

# Supported image file extensions
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif",
    ".webp", ".heic", ".heif", ".raw", ".cr2", ".nef",
    ".arw", ".dng", ".svg", ".ico",
}

# Supported animated image extensions
GIF_EXTENSIONS = {
    ".gif", ".apng",
}

# All supported media extensions
ALL_MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS | GIF_EXTENSIONS


def classify_media_type(filepath: Path) -> str:
    """Classify a file as 'video', 'image', or 'gif' based on extension."""
    ext = filepath.suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        return "video"
    elif ext in GIF_EXTENSIONS:
        return "gif"
    elif ext in IMAGE_EXTENSIONS:
        return "image"
    return "unknown"


def discover_media_files(
    folder: str,
    recursive: bool = True,
) -> List[Path]:
    """
    Discover video, image, and GIF files in the given folder.

    - Filters by ALL_MEDIA_EXTENSIONS.
    - Skips any file or directory whose name contains 'proxy' (case-insensitive).
    - Optionally recurses into subdirectories.

    Returns a sorted list of Path objects.
    """
    folder_path = Path(folder).resolve()
    if not folder_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {folder_path}")

    results: List[Path] = []

    if recursive:
        for root, dirs, files in os.walk(folder_path):
            # Filter out directories containing 'proxy' in their name
            dirs[:] = [
                d for d in dirs
                if "proxy" not in d.lower()
            ]

            for filename in files:
                if "proxy" in filename.lower():
                    continue
                filepath = Path(root) / filename
                if filepath.suffix.lower() in ALL_MEDIA_EXTENSIONS:
                    results.append(filepath)
    else:
        for filepath in folder_path.iterdir():
            if not filepath.is_file():
                continue
            if "proxy" in filepath.name.lower():
                continue
            if filepath.suffix.lower() in ALL_MEDIA_EXTENSIONS:
                results.append(filepath)

    return sorted(results)


def format_file_size(size_bytes: int) -> str:
    """Convert bytes to a human-readable string (e.g., '1.23 GB')."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.2f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.2f} GB"


def format_duration(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    if seconds is None or seconds < 0:
        return "00:00:00"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_relative_path(filepath: Path, base_folder: Path) -> str:
    """Get the relative path from base_folder to filepath."""
    try:
        return str(filepath.relative_to(base_folder))
    except ValueError:
        return str(filepath)
