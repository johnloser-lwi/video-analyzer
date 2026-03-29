"""Multi-database keyword search engine."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SearchResult:
    """A single search result from a database."""
    # File info
    filename: str
    filepath: str
    relative_path: str
    media_type: str
    # Metadata
    file_size: int
    file_size_human: str
    duration: float
    duration_formatted: str
    resolution_w: int
    resolution_h: int
    video_codec: str
    audio_codec: str
    bitrate: int
    framerate: str
    container_format: str
    # AI fields
    scene_description: str
    key_objects: str
    actions: str
    setting: str
    screen_text: str
    content_summary: str
    # Source
    db_folder: str  # Which database this came from
    db_name: str    # Human-readable DB name


# Columns to search against for keyword matching
SEARCH_COLUMNS = [
    "filename",
    "scene_description",
    "key_objects",
    "actions",
    "setting",
    "screen_text",
    "content_summary",
]


class SearchEngine:
    """Search across multiple video catalog databases."""

    def __init__(self):
        self.databases: Dict[str, Dict] = {}  # path -> {conn, name, enabled}

    def add_database(self, db_path: str, name: str = None) -> bool:
        """
        Add a database connection.
        Returns True if successful, False if the DB doesn't exist or is invalid.
        """
        path = Path(db_path)
        if not path.exists():
            return False

        db_key = str(path.resolve())
        if db_key in self.databases:
            return True  # Already connected

        try:
            conn = sqlite3.connect(db_key)
            conn.row_factory = sqlite3.Row
            # Verify it has the videos table
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='videos'"
            )
            if cursor.fetchone() is None:
                conn.close()
                return False

            display_name = name or path.parent.name
            self.databases[db_key] = {
                "conn": conn,
                "name": display_name,
                "path": db_key,
                "folder": str(path.parent),
                "enabled": True,
            }
            return True
        except Exception:
            return False

    def remove_database(self, db_path: str):
        """Remove a database connection."""
        db_key = str(Path(db_path).resolve())
        if db_key in self.databases:
            try:
                self.databases[db_key]["conn"].close()
            except Exception:
                pass
            del self.databases[db_key]

    def toggle_database(self, db_path: str, enabled: bool):
        """Enable or disable a database for searching."""
        db_key = str(Path(db_path).resolve())
        if db_key in self.databases:
            self.databases[db_key]["enabled"] = enabled

    def get_databases(self) -> List[Dict]:
        """Get list of all connected databases with their info."""
        result = []
        for key, info in self.databases.items():
            count = 0
            try:
                cursor = info["conn"].execute("SELECT COUNT(*) FROM videos")
                count = cursor.fetchone()[0]
            except Exception:
                pass
            result.append({
                "path": info["path"],
                "name": info["name"],
                "folder": info["folder"],
                "enabled": info["enabled"],
                "count": count,
            })
        return result

    def search(self, query: str = "") -> List[SearchResult]:
        """
        Search across all enabled databases.

        Empty query returns all entries.
        Multiple words are treated as AND (all must match).
        """
        results = []
        keywords = query.strip().split() if query.strip() else []

        for db_key, info in self.databases.items():
            if not info["enabled"]:
                continue

            try:
                results.extend(
                    self._search_single_db(info, keywords)
                )
            except Exception:
                continue

        # Sort by relevance (filename matches first, then by filename)
        if keywords:
            results.sort(key=lambda r: (
                -sum(1 for k in keywords if k.lower() in r.filename.lower()),
                r.filename.lower(),
            ))
        else:
            results.sort(key=lambda r: r.filename.lower())

        return results

    def _search_single_db(
        self, db_info: Dict, keywords: List[str]
    ) -> List[SearchResult]:
        """Search a single database."""
        conn = db_info["conn"]

        if not keywords:
            # Return all entries
            cursor = conn.execute("SELECT * FROM videos ORDER BY filename")
        else:
            # Build WHERE clause: all keywords must match at least one column
            conditions = []
            params = []
            for keyword in keywords:
                col_conditions = [f"{col} LIKE ?" for col in SEARCH_COLUMNS]
                conditions.append(f"({' OR '.join(col_conditions)})")
                params.extend([f"%{keyword}%"] * len(SEARCH_COLUMNS))

            where = " AND ".join(conditions)
            cursor = conn.execute(
                f"SELECT * FROM videos WHERE {where} ORDER BY filename",
                params,
            )

        rows = cursor.fetchall()
        results = []

        for row in rows:
            try:
                results.append(SearchResult(
                    filename=row["filename"] or "",
                    filepath=row["filepath"] or "",
                    relative_path=row["relative_path"] or "",
                    media_type=row["media_type"] if "media_type" in row.keys() else "video",
                    file_size=row["file_size"] or 0,
                    file_size_human=row["file_size_human"] or "",
                    duration=row["duration"] or 0,
                    duration_formatted=row["duration_formatted"] or "",
                    resolution_w=row["resolution_w"] or 0,
                    resolution_h=row["resolution_h"] or 0,
                    video_codec=row["video_codec"] or "",
                    audio_codec=row["audio_codec"] or "",
                    bitrate=row["bitrate"] or 0,
                    framerate=row["framerate"] or "",
                    container_format=row["container_format"] or "",
                    scene_description=row["scene_description"] or "",
                    key_objects=row["key_objects"] or "",
                    actions=row["actions"] or "",
                    setting=row["setting"] or "",
                    screen_text=row["screen_text"] or "",
                    content_summary=row["content_summary"] or "",
                    db_folder=db_info["folder"],
                    db_name=db_info["name"],
                ))
            except Exception:
                continue

        return results

    def close_all(self):
        """Close all database connections."""
        for info in self.databases.values():
            try:
                info["conn"].close()
            except Exception:
                pass
        self.databases.clear()
