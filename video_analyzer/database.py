"""SQLite database management for the video catalog."""

import csv
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .analyzer import VideoMetadata

# Database filename (stored alongside the videos)
DB_FILENAME = "video_catalog.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL UNIQUE,
    relative_path TEXT NOT NULL,
    media_type TEXT NOT NULL DEFAULT 'video',
    file_size INTEGER NOT NULL,
    file_size_human TEXT,
    file_modified_time REAL NOT NULL,
    duration REAL,
    duration_formatted TEXT,
    resolution_w INTEGER,
    resolution_h INTEGER,
    video_codec TEXT,
    audio_codec TEXT,
    bitrate INTEGER,
    framerate TEXT,
    container_format TEXT,
    creation_time TEXT,
    scene_description TEXT,
    key_objects TEXT,
    actions TEXT,
    setting TEXT,
    screen_text TEXT,
    content_summary TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_filepath ON videos(filepath);
CREATE INDEX IF NOT EXISTS idx_filename ON videos(filename);
"""


class VideoCatalogDB:
    """Manages the SQLite database for the video catalog."""

    def __init__(self, folder: str):
        self.folder = Path(folder).resolve()
        self.db_path = self.folder / DB_FILENAME
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Open the database connection and ensure schema exists."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(CREATE_TABLE_SQL)
        self.conn.executescript(CREATE_INDEX_SQL)
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_existing_entry(self, filepath: str) -> Optional[sqlite3.Row]:
        """Get an existing entry by filepath."""
        cursor = self.conn.execute(
            "SELECT * FROM videos WHERE filepath = ?", (filepath,)
        )
        return cursor.fetchone()

    def needs_analysis(self, filepath: str, file_size: int, file_mtime: float) -> bool:
        """
        Check if a file needs (re-)analysis.

        A file needs analysis if:
        - It's not in the database, OR
        - Its size or modification time has changed
        """
        existing = self.get_existing_entry(filepath)
        if existing is None:
            return True

        return (
            existing["file_size"] != file_size
            or abs(existing["file_modified_time"] - file_mtime) > 1.0
        )

    def upsert_video(self, metadata: VideoMetadata, relative_path: str):
        """Insert or update a video entry."""
        self.conn.execute(
            """
            INSERT INTO videos (
                filename, filepath, relative_path, media_type,
                file_size, file_size_human, file_modified_time,
                duration, duration_formatted,
                resolution_w, resolution_h,
                video_codec, audio_codec,
                bitrate, framerate, container_format, creation_time,
                scene_description, key_objects, actions,
                setting, screen_text, content_summary,
                analyzed_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT(filepath) DO UPDATE SET
                filename = excluded.filename,
                relative_path = excluded.relative_path,
                media_type = excluded.media_type,
                file_size = excluded.file_size,
                file_size_human = excluded.file_size_human,
                file_modified_time = excluded.file_modified_time,
                duration = excluded.duration,
                duration_formatted = excluded.duration_formatted,
                resolution_w = excluded.resolution_w,
                resolution_h = excluded.resolution_h,
                video_codec = excluded.video_codec,
                audio_codec = excluded.audio_codec,
                bitrate = excluded.bitrate,
                framerate = excluded.framerate,
                container_format = excluded.container_format,
                creation_time = excluded.creation_time,
                scene_description = excluded.scene_description,
                key_objects = excluded.key_objects,
                actions = excluded.actions,
                setting = excluded.setting,
                screen_text = excluded.screen_text,
                content_summary = excluded.content_summary,
                analyzed_at = CURRENT_TIMESTAMP
            """,
            (
                metadata.filename, metadata.filepath, relative_path, metadata.media_type,
                metadata.file_size, metadata.file_size_human, metadata.file_modified_time,
                metadata.duration, metadata.duration_formatted,
                metadata.resolution_w, metadata.resolution_h,
                metadata.video_codec, metadata.audio_codec,
                metadata.bitrate, metadata.framerate,
                metadata.container_format, metadata.creation_time,
                metadata.scene_description, metadata.key_objects,
                metadata.actions, metadata.setting,
                metadata.screen_text, metadata.content_summary,
            ),
        )
        self.conn.commit()

    def remove_missing_files(self) -> int:
        """
        Remove entries for files that no longer exist on disk.
        Returns the number of entries removed.
        """
        cursor = self.conn.execute("SELECT id, filepath FROM videos")
        rows = cursor.fetchall()
        removed = 0

        for row in rows:
            if not Path(row["filepath"]).exists():
                self.conn.execute("DELETE FROM videos WHERE id = ?", (row["id"],))
                removed += 1

        if removed > 0:
            self.conn.commit()

        return removed

    def get_all_videos(self) -> List[sqlite3.Row]:
        """Get all video entries."""
        cursor = self.conn.execute(
            "SELECT * FROM videos ORDER BY relative_path"
        )
        return cursor.fetchall()

    def get_video_count(self) -> int:
        """Get the total number of videos in the catalog."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM videos")
        return cursor.fetchone()[0]

    def export_csv(self) -> Path:
        """
        Export the database to a CSV file alongside the DB.
        Returns the path to the CSV file.
        """
        csv_path = self.folder / "video_catalog.csv"
        rows = self.get_all_videos()

        if not rows:
            return csv_path

        columns = rows[0].keys()

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            for row in rows:
                writer.writerow([row[col] for col in columns])

        return csv_path
