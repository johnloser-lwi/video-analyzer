"""Thumbnail generation and caching for videos, images, and GIFs."""

import hashlib
import subprocess
from pathlib import Path
from typing import Optional

from PIL import Image

THUMB_WIDTH = 240
THUMB_HEIGHT = 160
THUMB_DIR = ".thumbnails"


def get_thumbnail_dir(db_folder: Path) -> Path:
    """Get (and create) the thumbnail cache directory for a database folder."""
    thumb_dir = db_folder / THUMB_DIR
    thumb_dir.mkdir(exist_ok=True)
    return thumb_dir


def _thumb_filename(filepath: str) -> str:
    """Generate a unique thumbnail filename from the full file path."""
    h = hashlib.md5(filepath.encode()).hexdigest()[:12]
    return f"{h}.jpg"


def get_cached_thumbnail(filepath: str, db_folder: Path) -> Optional[Path]:
    """Return the cached thumbnail path if it exists."""
    thumb_dir = get_thumbnail_dir(db_folder)
    thumb_path = thumb_dir / _thumb_filename(filepath)
    if thumb_path.exists() and thumb_path.stat().st_size > 0:
        return thumb_path
    return None


def generate_thumbnail(
    filepath: str,
    db_folder: Path,
    media_type: str = "video",
) -> Optional[Path]:
    """
    Generate a thumbnail for a media file and cache it.

    - Videos: extract a frame at 10% via FFmpeg
    - Images/GIFs: resize via Pillow

    Returns the path to the cached thumbnail, or None on failure.
    """
    source = Path(filepath)
    if not source.exists():
        return None

    thumb_dir = get_thumbnail_dir(db_folder)
    thumb_path = thumb_dir / _thumb_filename(filepath)

    # Return cached if exists
    if thumb_path.exists() and thumb_path.stat().st_size > 0:
        return thumb_path

    try:
        if media_type == "video":
            return _generate_video_thumbnail(source, thumb_path)
        else:
            return _generate_image_thumbnail(source, thumb_path)
    except Exception:
        return None


def _generate_video_thumbnail(source: Path, thumb_path: Path) -> Optional[Path]:
    """Extract a frame from a video at 10% duration and save as thumbnail."""
    try:
        # Get duration
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(source),
            ],
            capture_output=True, text=True, timeout=15,
        )
        duration = float(result.stdout.strip()) if result.stdout.strip() else 5
        timestamp = max(duration * 0.1, 0.5)

        # Extract frame
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", str(timestamp),
                "-i", str(source),
                "-vframes", "1",
                "-vf", f"scale={THUMB_WIDTH}:{THUMB_HEIGHT}:force_original_aspect_ratio=increase,crop={THUMB_WIDTH}:{THUMB_HEIGHT}",
                "-q:v", "5",
                str(thumb_path),
            ],
            capture_output=True, text=True, timeout=20,
        )

        if thumb_path.exists() and thumb_path.stat().st_size > 0:
            return thumb_path
    except Exception:
        pass
    return None


def _generate_image_thumbnail(source: Path, thumb_path: Path) -> Optional[Path]:
    """Resize an image/GIF to thumbnail size via Pillow."""
    try:
        with Image.open(source) as img:
            # Convert to RGB for JPEG output
            if img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Crop to center aspect ratio then resize
            img_ratio = img.width / img.height
            thumb_ratio = THUMB_WIDTH / THUMB_HEIGHT

            if img_ratio > thumb_ratio:
                # Image is wider — crop sides
                new_w = int(img.height * thumb_ratio)
                left = (img.width - new_w) // 2
                img = img.crop((left, 0, left + new_w, img.height))
            else:
                # Image is taller — crop top/bottom
                new_h = int(img.width / thumb_ratio)
                top = (img.height - new_h) // 2
                img = img.crop((0, top, img.width, top + new_h))

            img = img.resize((THUMB_WIDTH, THUMB_HEIGHT), Image.LANCZOS)
            img.save(str(thumb_path), "JPEG", quality=80)

        if thumb_path.exists():
            return thumb_path
    except Exception:
        pass
    return None
