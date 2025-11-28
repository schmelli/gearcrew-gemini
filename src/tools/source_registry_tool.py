"""
Source Registry Tool - Track visited URLs to prevent duplicate scanning.
Uses SQLite database for persistence across sessions.
"""
import sqlite3
from typing import Type, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from datetime import datetime
import os

class SourceRegistryInput(BaseModel):
    """Input schema for Source Registry Tool"""
    action: str = Field(
        ...,
        description="Action to perform: 'check' (is URL visited?), 'add' (mark as visited), 'list' (show recent), 'stats' (get statistics)"
    )
    url: Optional[str] = Field(
        None,
        description="URL to check or add (required for 'check' and 'add' actions)"
    )
    source_type: Optional[str] = Field(
        None,
        description="Type of source: youtube, website, blog, reddit, forum"
    )
    items_found: Optional[int] = Field(
        None,
        description="Number of items discovered from this source (for 'add' action)"
    )

class SourceRegistryTool(BaseTool):
    """
    Track visited sources to prevent duplicate scanning.

    Actions:
    - check: Verify if a URL has been visited
    - add: Mark a URL as visited
    - list: Show recently visited sources
    - stats: Get registry statistics
    """
    name: str = "Source Registry"
    description: str = """Track visited sources to avoid duplicate scanning.

    Use 'check' before scanning a source to see if it's already been visited.
    Use 'add' after scanning a source to mark it as visited.
    Use 'list' to see recently visited sources.
    Use 'stats' to get statistics about the registry."""

    args_schema: Type[BaseModel] = SourceRegistryInput
    db_path: str = Field(default="./data/source_registry.db")

    def __init__(self, db_path: str = "./data/source_registry.db", **kwargs):
        """Initialize the tool and create database if needed"""
        super().__init__(db_path=db_path, **kwargs)

        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create database schema if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS visited_sources (
                url TEXT PRIMARY KEY,
                source_type TEXT,
                visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                items_discovered INTEGER DEFAULT 0,
                last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scan_count INTEGER DEFAULT 1,
                status TEXT DEFAULT 'completed'
            )
        """)

        # Create index for faster lookups
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_source_type
            ON visited_sources(source_type)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_visited_at
            ON visited_sources(visited_at DESC)
        """)

        conn.commit()
        conn.close()

    def _run(self, action: str, url: Optional[str] = None,
             source_type: Optional[str] = None, items_found: Optional[int] = None) -> str:
        """Execute the requested action"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if action == "check":
                if not url:
                    return "ERROR: URL required for 'check' action"

                cursor.execute("""
                    SELECT status, visited_at, scan_count, items_discovered
                    FROM visited_sources
                    WHERE url = ?
                """, (url,))
                row = cursor.fetchone()

                if row:
                    status, visited_at, scan_count, items = row
                    return f"VISITED: {url}\n  First visited: {visited_at}\n  Scans: {scan_count}\n  Items found: {items}\n  Status: {status}"
                else:
                    return f"NEW: {url} has not been visited yet"

            elif action == "add":
                if not url:
                    return "ERROR: URL required for 'add' action"

                # Check if already exists
                cursor.execute("SELECT scan_count FROM visited_sources WHERE url = ?", (url,))
                existing = cursor.fetchone()

                if existing:
                    # Update existing record
                    scan_count = existing[0] + 1
                    cursor.execute("""
                        UPDATE visited_sources
                        SET last_scanned = CURRENT_TIMESTAMP,
                            scan_count = ?,
                            items_discovered = items_discovered + ?,
                            source_type = COALESCE(?, source_type)
                        WHERE url = ?
                    """, (scan_count, items_found or 0, source_type, url))
                    conn.commit()
                    return f"UPDATED: {url} (scan #{scan_count}, +{items_found or 0} items)"
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO visited_sources (url, source_type, items_discovered, status)
                        VALUES (?, ?, ?, 'completed')
                    """, (url, source_type or 'unknown', items_found or 0))
                    conn.commit()
                    return f"REGISTERED: {url} ({source_type or 'unknown'}, {items_found or 0} items)"

            elif action == "list":
                limit = 20
                cursor.execute("""
                    SELECT url, source_type, visited_at, items_discovered, scan_count
                    FROM visited_sources
                    ORDER BY visited_at DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()

                if not rows:
                    return "Registry is empty - no sources visited yet"

                result = f"Recently visited sources ({len(rows)}):\n"
                for url, src_type, visited, items, scans in rows:
                    result += f"\n  [{src_type}] {url}\n    Visited: {visited} | Items: {items} | Scans: {scans}"

                return result

            elif action == "stats":
                # Total sources
                cursor.execute("SELECT COUNT(*) FROM visited_sources")
                total = cursor.fetchone()[0]

                # By source type
                cursor.execute("""
                    SELECT source_type, COUNT(*), SUM(items_discovered)
                    FROM visited_sources
                    GROUP BY source_type
                    ORDER BY COUNT(*) DESC
                """)
                by_type = cursor.fetchall()

                # Total items
                cursor.execute("SELECT SUM(items_discovered) FROM visited_sources")
                total_items = cursor.fetchone()[0] or 0

                result = f"Source Registry Statistics:\n"
                result += f"  Total sources visited: {total}\n"
                result += f"  Total items discovered: {total_items}\n"
                result += f"\nBy source type:\n"
                for src_type, count, items in by_type:
                    result += f"  {src_type}: {count} sources, {items or 0} items\n"

                return result

            else:
                return f"ERROR: Unknown action '{action}'. Use: check, add, list, or stats"

        finally:
            conn.close()
