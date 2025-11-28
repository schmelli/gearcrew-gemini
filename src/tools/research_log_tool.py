"""
Research Log Tool - Document all research steps and sources.
Maintains audit trail of what was researched and where information came from.
"""
import sqlite3
import json
from typing import Type, Optional, Dict, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from datetime import datetime
import os

class ResearchLogInput(BaseModel):
    """Input schema for Research Log Tool"""
    action: str = Field(
        ...,
        description="Action: 'log' (record step), 'retrieve' (get history), 'complete' (mark done), 'validate' (check quality)"
    )
    discovery_id: Optional[str] = Field(
        None,
        description="Discovery ID being researched"
    )
    research_id: Optional[str] = Field(
        None,
        description="Research session ID"
    )
    source_url: Optional[str] = Field(
        None,
        description="URL of source consulted"
    )
    source_type: Optional[str] = Field(
        None,
        description="Type: manufacturer, retailer, review_site, blog, forum"
    )
    data_found: Optional[List[str]] = Field(
        None,
        description="List of data fields found from this source"
    )
    confidence: Optional[str] = Field(
        None,
        description="Confidence level: verified, corroborated, reported, uncertain"
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes about this research step"
    )

class ResearchLogTool(BaseTool):
    """
    Document research steps and maintain source citations.

    Actions:
    - log: Record a research step (source consulted, data found)
    - retrieve: Get full research history for a discovery
    - complete: Mark research as complete and calculate quality score
    - validate: Check if research meets quality standards
    """
    name: str = "Research Log"
    description: str = """Document all research steps with source citations.

    Use 'log' every time you consult a source during research.
    Use 'retrieve' to see what research has already been done.
    Use 'complete' when research is finished.
    Use 'validate' to check if research quality is sufficient."""

    args_schema: Type[BaseModel] = ResearchLogInput
    db_path: str = Field(default="./data/research_log.db")

    def __init__(self, db_path: str = "./data/research_log.db", **kwargs):
        """Initialize the tool and create database"""
        super().__init__(db_path=db_path, **kwargs)

        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create database schema"""
        conn = sqlite3.connect(self.db_path)

        # Research sessions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS research_sessions (
                research_id TEXT PRIMARY KEY,
                discovery_id TEXT NOT NULL,
                researcher_agent TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT DEFAULT 'in_progress',
                completeness_score REAL,
                overall_confidence TEXT
            )
        """)

        # Research steps table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS research_steps (
                step_id INTEGER PRIMARY KEY AUTOINCREMENT,
                research_id TEXT NOT NULL,
                discovery_id TEXT NOT NULL,
                source_url TEXT NOT NULL,
                source_type TEXT,
                data_found TEXT,
                confidence TEXT,
                notes TEXT,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (research_id) REFERENCES research_sessions(research_id)
            )
        """)

        # Indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_research_discovery
            ON research_sessions(discovery_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_steps_research
            ON research_steps(research_id)
        """)

        conn.commit()
        conn.close()

    def _run(self, action: str, discovery_id: Optional[str] = None,
             research_id: Optional[str] = None, source_url: Optional[str] = None,
             source_type: Optional[str] = None, data_found: Optional[List[str]] = None,
             confidence: Optional[str] = None, notes: Optional[str] = None) -> str:
        """Execute the requested action"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if action == "log":
                if not research_id or not discovery_id or not source_url:
                    return "ERROR: research_id, discovery_id, and source_url required for 'log' action"

                # Ensure research session exists
                cursor.execute("SELECT status FROM research_sessions WHERE research_id = ?", (research_id,))
                session = cursor.fetchone()

                if not session:
                    # Create new session
                    cursor.execute("""
                        INSERT INTO research_sessions (research_id, discovery_id, status)
                        VALUES (?, ?, 'in_progress')
                    """, (research_id, discovery_id))

                # Log the research step
                cursor.execute("""
                    INSERT INTO research_steps
                    (research_id, discovery_id, source_url, source_type, data_found, confidence, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    research_id,
                    discovery_id,
                    source_url,
                    source_type or 'other',
                    json.dumps(data_found) if data_found else None,
                    confidence or 'uncertain',
                    notes
                ))

                conn.commit()

                return f"LOGGED: Research step for {discovery_id}\n  Source: {source_url} ({source_type})\n  Data found: {len(data_found or [])} fields\n  Confidence: {confidence}"

            elif action == "retrieve":
                if not discovery_id:
                    return "ERROR: discovery_id required for 'retrieve' action"

                # Get all research sessions for this discovery
                cursor.execute("""
                    SELECT research_id, started_at, completed_at, status, completeness_score
                    FROM research_sessions
                    WHERE discovery_id = ?
                    ORDER BY started_at DESC
                """, (discovery_id,))
                sessions = cursor.fetchall()

                if not sessions:
                    return f"NO RESEARCH: No research found for discovery {discovery_id}"

                result = f"Research History for {discovery_id}:\n"

                for res_id, started, completed, status, score in sessions:
                    result += f"\n  Research ID: {res_id}"
                    result += f"\n    Started: {started}"
                    result += f"\n    Status: {status}"
                    if completed:
                        result += f"\n    Completed: {completed}"
                    if score:
                        result += f"\n    Completeness: {score:.1%}"

                    # Get steps for this session
                    cursor.execute("""
                        SELECT source_url, source_type, data_found, confidence, logged_at
                        FROM research_steps
                        WHERE research_id = ?
                        ORDER BY logged_at
                    """, (res_id,))
                    steps = cursor.fetchall()

                    result += f"\n    Steps: {len(steps)}"
                    for url, src_type, data, conf, logged in steps:
                        data_list = json.loads(data) if data else []
                        result += f"\n      - [{src_type}] {url} ({len(data_list)} fields, {conf})"

                return result

            elif action == "complete":
                if not research_id:
                    return "ERROR: research_id required for 'complete' action"

                # Calculate completeness score
                cursor.execute("""
                    SELECT data_found FROM research_steps WHERE research_id = ?
                """, (research_id,))
                steps = cursor.fetchall()

                if not steps:
                    return f"ERROR: No research steps found for {research_id}"

                # Collect all unique fields found
                all_fields = set()
                for (data,) in steps:
                    if data:
                        fields = json.loads(data)
                        all_fields.update(fields)

                # Required fields for a complete product
                required_fields = {
                    'name', 'brand', 'weight', 'price', 'productUrl', 'imageUrl', 'type'
                }

                completeness = len(all_fields & required_fields) / len(required_fields)

                # Determine overall confidence
                cursor.execute("""
                    SELECT confidence FROM research_steps
                    WHERE research_id = ?
                """, (research_id,))
                confidences = [row[0] for row in cursor.fetchall()]

                if 'verified' in confidences:
                    overall_conf = 'verified'
                elif 'corroborated' in confidences:
                    overall_conf = 'corroborated'
                elif 'reported' in confidences:
                    overall_conf = 'reported'
                else:
                    overall_conf = 'uncertain'

                # Update session
                cursor.execute("""
                    UPDATE research_sessions
                    SET status = 'completed',
                        completed_at = CURRENT_TIMESTAMP,
                        completeness_score = ?,
                        overall_confidence = ?
                    WHERE research_id = ?
                """, (completeness, overall_conf, research_id))

                conn.commit()

                return f"COMPLETED: Research {research_id}\n  Completeness: {completeness:.1%}\n  Confidence: {overall_conf}\n  Fields found: {', '.join(sorted(all_fields))}"

            elif action == "validate":
                if not research_id:
                    return "ERROR: research_id required for 'validate' action"

                cursor.execute("""
                    SELECT completeness_score, overall_confidence, status
                    FROM research_sessions
                    WHERE research_id = ?
                """, (research_id,))
                session = cursor.fetchone()

                if not session:
                    return f"ERROR: Research session {research_id} not found"

                score, conf, status = session

                if status != 'completed':
                    return f"INCOMPLETE: Research {research_id} not yet completed"

                # Quality thresholds
                min_completeness = 0.85  # 85% of required fields
                acceptable_confidence = ['verified', 'corroborated']

                if score >= min_completeness and conf in acceptable_confidence:
                    return f"VALID: Research {research_id} meets quality standards\n  Completeness: {score:.1%}\n  Confidence: {conf}"
                else:
                    issues = []
                    if score < min_completeness:
                        issues.append(f"Low completeness ({score:.1%} < {min_completeness:.1%})")
                    if conf not in acceptable_confidence:
                        issues.append(f"Low confidence ({conf})")

                    return f"INVALID: Research {research_id} does not meet standards\n  Issues: {', '.join(issues)}"

            else:
                return f"ERROR: Unknown action '{action}'. Use: log, retrieve, complete, validate"

        finally:
            conn.close()
