"""
Discovery Queue Tool - Manage queue of discoveries waiting for curation.
Acts as a buffer between Gear-heads and Curators teams.
"""
import sqlite3
import json
from typing import Type, Optional, Dict
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from datetime import datetime
import os

class DiscoveryQueueInput(BaseModel):
    """Input schema for Discovery Queue Tool"""
    action: str = Field(
        ...,
        description="Action: 'enqueue' (add discovery), 'dequeue' (get next), 'peek' (view without removing), 'status' (queue stats), 'update' (update discovery status)"
    )
    discovery_data: Optional[Dict] = Field(
        None,
        description="Discovery data (JSON) for 'enqueue' action"
    )
    discovery_id: Optional[str] = Field(
        None,
        description="Discovery ID for 'update' action"
    )
    new_status: Optional[str] = Field(
        None,
        description="New status for 'update' action (pending, researching, verified, loaded, error)"
    )
    priority: Optional[int] = Field(
        None,
        description="Priority 1-10 (10=highest) for 'enqueue' action"
    )

class DiscoveryQueueTool(BaseTool):
    """
    Manage queue of discoveries from Gear-heads awaiting curation by Curators.

    Actions:
    - enqueue: Add a new discovery to the queue
    - dequeue: Get the next highest-priority discovery
    - peek: View next discovery without removing it
    - status: Get queue statistics
    - update: Update the status of a discovery
    """
    name: str = "Discovery Queue"
    description: str = """Manage the queue of discoveries waiting for curation.

    Gear-heads use 'enqueue' to add discoveries.
    Curators use 'dequeue' to get the next discovery to work on.
    Use 'peek' to see what's next without claiming it.
    Use 'status' to check queue depth and distribution.
    Use 'update' to change a discovery's status."""

    args_schema: Type[BaseModel] = DiscoveryQueueInput
    db_path: str = Field(default="./data/discovery_queue.db")

    def __init__(self, db_path: str = "./data/discovery_queue.db", **kwargs):
        """Initialize the tool and create database if needed"""
        super().__init__(db_path=db_path, **kwargs)

        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create database schema"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS discovery_queue (
                discovery_id TEXT PRIMARY KEY,
                discovery_type TEXT NOT NULL,
                discovery_data TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 5,
                enqueued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                claimed_at TIMESTAMP,
                claimed_by TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes for efficient querying
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_priority
            ON discovery_queue(status, priority DESC, enqueued_at)
        """)

        conn.commit()
        conn.close()

    def _run(self, action: str, discovery_data: Optional[Dict] = None,
             discovery_id: Optional[str] = None, new_status: Optional[str] = None,
             priority: Optional[int] = None) -> str:
        """Execute the requested action"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if action == "enqueue":
                if not discovery_data:
                    return "ERROR: discovery_data required for 'enqueue' action"

                disc_id = discovery_data.get('discovery_id')
                disc_type = discovery_data.get('discovery_type', 'unknown')

                if not disc_id:
                    return "ERROR: discovery_data must include 'discovery_id'"

                # Check if already exists
                cursor.execute("SELECT status FROM discovery_queue WHERE discovery_id = ?", (disc_id,))
                existing = cursor.fetchone()

                if existing:
                    return f"DUPLICATE: Discovery {disc_id} already in queue (status: {existing[0]})"

                # Insert new discovery
                cursor.execute("""
                    INSERT INTO discovery_queue (discovery_id, discovery_type, discovery_data, priority, status)
                    VALUES (?, ?, ?, ?, 'pending')
                """, (disc_id, disc_type, json.dumps(discovery_data), priority or 5))

                conn.commit()
                return f"ENQUEUED: {disc_id} ({disc_type}, priority={priority or 5})"

            elif action == "dequeue":
                # Get highest priority pending discovery
                cursor.execute("""
                    SELECT discovery_id, discovery_type, discovery_data, priority
                    FROM discovery_queue
                    WHERE status = 'pending'
                    ORDER BY priority DESC, enqueued_at ASC
                    LIMIT 1
                """)
                row = cursor.fetchone()

                if not row:
                    return "EMPTY: No pending discoveries in queue"

                disc_id, disc_type, data, prio = row

                # Mark as claimed (researching)
                cursor.execute("""
                    UPDATE discovery_queue
                    SET status = 'researching',
                        claimed_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE discovery_id = ?
                """, (disc_id,))

                conn.commit()

                # Return the discovery data
                return f"DEQUEUED: {disc_id}\nType: {disc_type}\nPriority: {prio}\nData: {data}"

            elif action == "peek":
                # View next without claiming
                cursor.execute("""
                    SELECT discovery_id, discovery_type, priority, enqueued_at
                    FROM discovery_queue
                    WHERE status = 'pending'
                    ORDER BY priority DESC, enqueued_at ASC
                    LIMIT 5
                """)
                rows = cursor.fetchall()

                if not rows:
                    return "EMPTY: No pending discoveries in queue"

                result = f"Next {len(rows)} discoveries in queue:\n"
                for disc_id, disc_type, prio, enqueued in rows:
                    result += f"\n  {disc_id} [{disc_type}] (priority={prio}, added={enqueued})"

                return result

            elif action == "status":
                # Get queue statistics
                cursor.execute("""
                    SELECT status, COUNT(*), AVG(priority)
                    FROM discovery_queue
                    GROUP BY status
                """)
                by_status = cursor.fetchall()

                cursor.execute("""
                    SELECT discovery_type, COUNT(*)
                    FROM discovery_queue
                    WHERE status = 'pending'
                    GROUP BY discovery_type
                """)
                by_type = cursor.fetchall()

                result = "Discovery Queue Status:\n"
                if by_status:
                    result += "\nBy status:\n"
                    for status, count, avg_prio in by_status:
                        result += f"  {status}: {count} items (avg priority: {avg_prio:.1f})\n"

                if by_type:
                    result += "\nPending by type:\n"
                    for disc_type, count in by_type:
                        result += f"  {disc_type}: {count} items\n"

                if not by_status:
                    result += "\nQueue is empty"

                return result

            elif action == "update":
                if not discovery_id or not new_status:
                    return "ERROR: discovery_id and new_status required for 'update' action"

                cursor.execute("""
                    UPDATE discovery_queue
                    SET status = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE discovery_id = ?
                """, (new_status, discovery_id))

                if cursor.rowcount == 0:
                    conn.rollback()
                    return f"ERROR: Discovery {discovery_id} not found in queue"

                conn.commit()
                return f"UPDATED: {discovery_id} status changed to '{new_status}'"

            else:
                return f"ERROR: Unknown action '{action}'. Use: enqueue, dequeue, peek, status, update"

        finally:
            conn.close()
