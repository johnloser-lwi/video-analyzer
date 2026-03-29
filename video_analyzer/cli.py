"""CLI entry point for the Video Analyzer tool."""

import argparse
import sys
import time
from pathlib import Path

from . import __version__
from .analyzer import VideoMetadata, check_ffprobe, extract_metadata, extract_image_metadata
from .ai_analyzer import (
    DEFAULT_MODEL,
    analyze_media,
    check_ollama,
    check_vision_model,
)
from .database import VideoCatalogDB
from .utils import (
    classify_media_type,
    discover_media_files,
    format_file_size,
    get_relative_path,
)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="video-analyzer",
        description="Analyze video files in a folder and build a metadata + AI content catalog.",
    )
    parser.add_argument(
        "folder",
        type=str,
        help="Path to the folder containing video files",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't scan subfolders (default: recursive ON)",
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Re-analyze all files, ignoring the existing cache",
    )
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Only extract technical metadata, skip AI content analysis",
    )
    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Export the catalog to a CSV file",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove entries for files that no longer exist",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Ollama vision model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output during analysis",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv=None):
    parser = create_parser()
    args = parser.parse_args(argv)

    folder = Path(args.folder).resolve()
    if not folder.is_dir():
        print(f"Error: '{args.folder}' is not a valid directory.")
        sys.exit(1)

    # ── Pre-flight checks ───────────────────────────────────────────
    print(f"\n{'═' * 60}")
    print(f"  Video Analyzer v{__version__}")
    print(f"{'═' * 60}")
    print(f"  Folder:  {folder}")
    print(f"  Types:   video, image, gif")

    if not check_ffprobe():
        print("\n  ✗  FFprobe not found. Please install FFmpeg first.")
        print("     Download: https://ffmpeg.org/download.html")
        print("     Or run:   winget install ffmpeg")
        sys.exit(1)
    print(f"  FFprobe: ✓ found")

    skip_ai = args.metadata_only
    if not skip_ai:
        if not check_ollama():
            print("\n  ✗  Ollama is not running. Start it with: ollama serve")
            print("     AI content analysis will be skipped.")
            skip_ai = True
        elif not check_vision_model(args.model):
            print(f"\n  ✗  Vision model '{args.model}' not found in Ollama.")
            print(f"     Pull it with: ollama pull {args.model}")
            print("     AI content analysis will be skipped.")
            skip_ai = True
        else:
            print(f"  Ollama:  ✓ {args.model}")

    recursive = not args.no_recursive
    print(f"  Mode:    {'recursive' if recursive else 'top-level only'}")
    if skip_ai:
        print(f"  AI:      disabled")
    print(f"{'═' * 60}\n")

    # ── Discover media files ────────────────────────────────────────
    print("Scanning for media files (video, image, gif)...")
    video_files = discover_media_files(str(folder), recursive=recursive)
    print(f"Found {len(video_files)} media file(s)")

    if not video_files:
        print("No media files found. Nothing to do.")
        return

    # ── Open database & determine work ──────────────────────────────
    with VideoCatalogDB(str(folder)) as db:

        # Clean up missing files if requested
        if args.clean:
            removed = db.remove_missing_files()
            if removed > 0:
                print(f"Cleaned up {removed} stale entries")
            else:
                print("No stale entries to clean")

        # Determine which files need analysis
        if args.force:
            files_to_analyze = video_files
            print(f"Force mode: will analyze all {len(files_to_analyze)} files")
        else:
            files_to_analyze = []
            for vf in video_files:
                stat = vf.stat()
                if db.needs_analysis(str(vf), stat.st_size, stat.st_mtime):
                    files_to_analyze.append(vf)

            existing = len(video_files) - len(files_to_analyze)
            if existing > 0:
                print(f"Skipping {existing} already-cataloged file(s)")
            print(f"Will analyze {len(files_to_analyze)} new/modified file(s)")

        if not files_to_analyze:
            print("\nAll files are up to date! Nothing to analyze.")
        else:
            # ── Analyze files ───────────────────────────────────────
            print()
            total = len(files_to_analyze)
            start_time = time.time()

            for idx, video_path in enumerate(files_to_analyze, 1):
                rel = get_relative_path(video_path, folder)
                print(f"[{idx}/{total}] {rel}")

                # Extract metadata
                media_type = classify_media_type(video_path)
                if args.verbose:
                    print(f"  [{media_type}] Extracting metadata...")
                # Use correct extractor based on media type
                if media_type == "video":
                    metadata = extract_metadata(video_path)
                else:
                    metadata = extract_image_metadata(video_path)

                if metadata is None:
                    print(f"  ⚠ Failed to extract metadata — skipping")
                    continue

                if args.verbose:
                    print(f"  Duration: {metadata.duration_formatted}")
                    print(f"  Resolution: {metadata.resolution_w}×{metadata.resolution_h}")
                    print(f"  Codec: {metadata.video_codec} / {metadata.audio_codec}")
                    print(f"  Size: {metadata.file_size_human}")

                # AI content analysis
                if not skip_ai:
                    if args.verbose:
                        print(f"  Running AI analysis...")
                    ai_result = analyze_media(
                        video_path,
                        media_type=media_type,
                        model=args.model,
                        verbose=args.verbose,
                    )
                    def _to_str(val):
                        """Convert AI result value to string (handles lists)."""
                        if isinstance(val, list):
                            return ", ".join(str(v) for v in val)
                        return str(val) if val else ""

                    metadata.scene_description = _to_str(ai_result.get("scene_description", ""))
                    metadata.key_objects = _to_str(ai_result.get("key_objects", ""))
                    metadata.actions = _to_str(ai_result.get("actions", ""))
                    metadata.setting = _to_str(ai_result.get("setting", ""))
                    metadata.screen_text = _to_str(ai_result.get("screen_text", ""))
                    metadata.content_summary = _to_str(ai_result.get("content_summary", ""))

                    if args.verbose and metadata.content_summary:
                        print(f"  Summary: {metadata.content_summary[:100]}")

                # Save to database
                db.upsert_video(metadata, rel)
                print(f"  ✓ Done")

            elapsed = time.time() - start_time
            print(f"\nAnalyzed {total} file(s) in {elapsed:.1f}s")

        # ── Export CSV if requested ─────────────────────────────────
        if args.export_csv:
            csv_path = db.export_csv()
            print(f"\nExported catalog to: {csv_path}")

        # ── Summary ────────────────────────────────────────────────
        total_count = db.get_video_count()
        print(f"\n{'─' * 60}")
        print(f"  Catalog: {db.db_path}")
        print(f"  Total videos cataloged: {total_count}")
        print(f"{'─' * 60}\n")


if __name__ == "__main__":
    main()
