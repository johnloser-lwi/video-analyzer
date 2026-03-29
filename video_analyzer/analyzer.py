"""FFprobe-based video metadata extraction."""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .utils import format_duration, format_file_size


@dataclass
class VideoMetadata:
    """Holds extracted metadata for a single video file."""
    filename: str = ""
    filepath: str = ""
    media_type: str = "video"  # "video", "image", or "gif"
    file_size: int = 0
    file_size_human: str = ""
    file_modified_time: float = 0.0
    duration: float = 0.0
    duration_formatted: str = ""
    resolution_w: int = 0
    resolution_h: int = 0
    video_codec: str = ""
    audio_codec: str = ""
    bitrate: int = 0
    framerate: str = ""
    container_format: str = ""
    creation_time: str = ""
    # AI fields (populated separately)
    scene_description: str = ""
    key_objects: str = ""
    actions: str = ""
    setting: str = ""
    screen_text: str = ""
    content_summary: str = ""


def check_ffprobe() -> bool:
    """Check if ffprobe is available on the system."""
    try:
        subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def extract_metadata(filepath: Path) -> Optional[VideoMetadata]:
    """
    Extract video metadata using ffprobe.

    Returns a VideoMetadata object, or None if extraction fails.
    """
    if not filepath.exists():
        return None

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(filepath),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            return None

        probe_data = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        return None

    # Extract format-level info
    fmt = probe_data.get("format", {})
    streams = probe_data.get("streams", [])

    # Find video and audio streams
    video_stream = None
    audio_stream = None
    for stream in streams:
        codec_type = stream.get("codec_type", "")
        if codec_type == "video" and video_stream is None:
            video_stream = stream
        elif codec_type == "audio" and audio_stream is None:
            audio_stream = stream

    # Build metadata
    stat = filepath.stat()
    duration = float(fmt.get("duration", 0))

    meta = VideoMetadata(
        filename=filepath.name,
        filepath=str(filepath),
        file_size=stat.st_size,
        file_size_human=format_file_size(stat.st_size),
        file_modified_time=stat.st_mtime,
        duration=duration,
        duration_formatted=format_duration(duration),
        container_format=fmt.get("format_name", ""),
        bitrate=int(fmt.get("bit_rate", 0)),
        creation_time=fmt.get("tags", {}).get("creation_time", ""),
    )

    if video_stream:
        meta.resolution_w = int(video_stream.get("width", 0))
        meta.resolution_h = int(video_stream.get("height", 0))
        meta.video_codec = video_stream.get("codec_name", "")

        # Parse framerate from r_frame_rate (e.g., "30000/1001")
        r_frame_rate = video_stream.get("r_frame_rate", "0/1")
        try:
            num, den = r_frame_rate.split("/")
            fps = float(num) / float(den)
            meta.framerate = f"{fps:.2f}"
        except (ValueError, ZeroDivisionError):
            meta.framerate = r_frame_rate

    if audio_stream:
        meta.audio_codec = audio_stream.get("codec_name", "")

    return meta


def extract_image_metadata(filepath: Path) -> Optional[VideoMetadata]:
    """
    Extract image metadata using ffprobe.

    Returns a VideoMetadata object with image-relevant fields populated.
    """
    if not filepath.exists():
        return None

    stat = filepath.stat()
    media_type = "gif" if filepath.suffix.lower() in (".gif", ".apng") else "image"

    meta = VideoMetadata(
        filename=filepath.name,
        filepath=str(filepath),
        media_type=media_type,
        file_size=stat.st_size,
        file_size_human=format_file_size(stat.st_size),
        file_modified_time=stat.st_mtime,
        container_format=filepath.suffix.lstrip(".").lower(),
    )

    # Try ffprobe for resolution and codec info
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(filepath),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            probe_data = json.loads(result.stdout)
            streams = probe_data.get("streams", [])
            fmt = probe_data.get("format", {})

            for stream in streams:
                if stream.get("codec_type") == "video":
                    meta.resolution_w = int(stream.get("width", 0))
                    meta.resolution_h = int(stream.get("height", 0))
                    meta.video_codec = stream.get("codec_name", "")

                    # For GIFs, get duration if available
                    if media_type == "gif":
                        dur = float(fmt.get("duration", 0))
                        meta.duration = dur
                        meta.duration_formatted = format_duration(dur)
                    break

            meta.container_format = fmt.get("format_name", meta.container_format)
    except Exception:
        pass

    return meta
