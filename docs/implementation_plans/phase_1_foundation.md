# Phase 1: Foundation - Detailed Implementation Plan

**Duration**: 3-4 days
**Goal**: Build core infrastructure for state management, source tracking, and inter-team communication

## Overview

This phase establishes the foundational tools and data structures that all three teams will use. No agents or crews yet - just the supporting infrastructure.

## File Structure

```
gearcrew-gemini/
├── src/
│   ├── tools/
│   │   ├── source_registry_tool.py        # NEW: Track visited URLs
│   │   ├── discovery_queue_tool.py        # NEW: Queue for discoveries
│   │   ├── research_log_tool.py           # NEW: Research documentation
│   │   └── geargraph_tools.py             # EXISTING: Keep as-is
│   ├── models/
│   │   ├── __init__.py                    # NEW
│   │   ├── flow_state.py                  # NEW: Pydantic state models
│   │   ├── discovery.py                   # NEW: Discovery data models
│   │   └── research.py                    # NEW: Research data models
│   └── config.py                          # EXISTING: Keep as-is
├── data/
│   ├── source_registry.db                 # NEW: SQLite database (auto-created)
│   ├── discovery_queue.db                 # NEW: SQLite database (auto-created)
│   └── research_log.db                    # NEW: SQLite database (auto-created)
└── tests/
    ├── test_source_registry.py            # NEW
    ├── test_discovery_queue.py            # NEW
    └── test_research_log.py               # NEW
```

---

## Step 1: Create Data Models (src/models/)

### 1.1 Create `src/models/__init__.py`

```python
"""
Data models for multi-team gear collection system
"""
from .flow_state import GearCollectionState
from .discovery import Discovery, DiscoveryType
from .research import ResearchLog, SourceType, ConfidenceLevel

__all__ = [
    'GearCollectionState',
    'Discovery',
    'DiscoveryType',
    'ResearchLog',
    'SourceType',
    'ConfidenceLevel'
]
```

### 1.2 Create `src/models/flow_state.py`

```python
"""
Flow state management for the gear collection system.
Defines the shared state used across all teams via CrewAI Flows.
"""
from pydantic import BaseModel, Field
from typing import Set, List, Dict, Optional
from datetime import datetime

class GearCollectionState(BaseModel):
    """
    Shared state for the GearCollectionFlow.
    All methods in the Flow can access and modify this state.
    """

    # Source tracking
    visited_sources: Set[str] = Field(
        default_factory=set,
        description="URLs that have been scanned (to avoid duplicates)"
    )
    last_scan_time: Dict[str, datetime] = Field(
        default_factory=dict,
        description="Last scan timestamp for each source type (youtube, website, etc.)"
    )

    # Discovery tracking
    pending_discoveries: List[str] = Field(
        default_factory=list,
        description="Discovery IDs waiting for curation"
    )
    discoveries_today: int = Field(
        default=0,
        description="Number of items discovered today"
    )

    # Research tracking
    research_in_progress: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of discovery_id -> researcher_agent_name"
    )
    research_completed: Set[str] = Field(
        default_factory=set,
        description="Discovery IDs that have been fully researched"
    )
    verifications_today: int = Field(
        default=0,
        description="Number of items verified today"
    )

    # Graph update tracking
    graph_updates_pending: List[str] = Field(
        default_factory=list,
        description="Discovery IDs with Cypher code ready to execute"
    )
    graph_nodes_created: int = Field(
        default=0,
        description="Total nodes created in GearGraph"
    )
    graph_relationships_created: int = Field(
        default=0,
        description="Total relationships created in GearGraph"
    )

    # Quality metrics
    errors_encountered: List[Dict] = Field(
        default_factory=list,
        description="Error log with timestamps and details"
    )
    quality_scores: List[float] = Field(
        default_factory=list,
        description="Data completeness scores (0.0-1.0)"
    )

    # Configuration
    max_parallel_scans: int = Field(
        default=4,
        description="Maximum number of concurrent source scans"
    )
    max_parallel_research: int = Field(
        default=3,
        description="Maximum number of concurrent research tasks"
    )
    quality_threshold: float = Field(
        default=0.95,
        description="Minimum data completeness required (0.0-1.0)"
    )

    # Session info
    session_start: Optional[datetime] = Field(
        default=None,
        description="When the current flow session started"
    )
    total_cycles: int = Field(
        default=0,
        description="Number of discovery-research-update cycles completed"
    )

    class Config:
        # Allow arbitrary types (for datetime)
        arbitrary_types_allowed = True


class TeamMetrics(BaseModel):
    """Metrics for a specific team's performance"""
    team_name: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_duration_seconds: float = 0.0
    last_active: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True
```

**Test**: Create `tests/test_flow_state.py`
```python
from src.models.flow_state import GearCollectionState
from datetime import datetime

def test_flow_state_initialization():
    state = GearCollectionState()
    assert len(state.visited_sources) == 0
    assert state.discoveries_today == 0
    assert state.quality_threshold == 0.95

def test_flow_state_updates():
    state = GearCollectionState()
    state.visited_sources.add("https://example.com")
    state.discoveries_today += 1
    assert len(state.visited_sources) == 1
    assert state.discoveries_today == 1
```

### 1.3 Create `src/models/discovery.py`

```python
"""
Data models for discoveries made by the Gear-heads team.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

class DiscoveryType(str, Enum):
    """Types of discoveries that can be made"""
    BRAND = "brand"
    PRODUCT = "product"
    INSIGHT = "insight"
    CATEGORY = "category"

class SourceType(str, Enum):
    """Types of sources where discoveries are made"""
    YOUTUBE = "youtube"
    WEBSITE = "website"
    BLOG = "blog"
    REDDIT = "reddit"
    FORUM = "forum"
    OTHER = "other"

class Discovery(BaseModel):
    """
    A single discovery from the Gear-heads team.
    This could be a brand, product, insight, or category.
    """
    # Identity
    discovery_id: str = Field(
        ...,
        description="Unique identifier for this discovery"
    )
    discovery_type: DiscoveryType = Field(
        ...,
        description="Type of discovery (brand, product, insight, category)"
    )

    # Content
    name: str = Field(
        ...,
        description="Name of the discovered entity"
    )
    context: str = Field(
        ...,
        description="Surrounding context where this was discovered"
    )
    partial_data: Dict = Field(
        default_factory=dict,
        description="Any partial data extracted (specs, attributes, etc.)"
    )

    # Source information
    source_url: HttpUrl = Field(
        ...,
        description="URL where this was discovered"
    )
    source_type: SourceType = Field(
        ...,
        description="Type of source (youtube, website, blog, etc.)"
    )
    source_title: Optional[str] = Field(
        None,
        description="Title of the source (video title, page title, etc.)"
    )

    # Metadata
    discovered_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this was discovered"
    )
    discovered_by: str = Field(
        ...,
        description="Name of the scanner agent that found this"
    )

    # Status tracking
    status: str = Field(
        default="pending",
        description="Status: pending, researching, verified, loaded, error"
    )
    priority: int = Field(
        default=5,
        description="Priority 1-10 (10 = highest priority)"
    )

    # Quality indicators
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in the discovery (0.0-1.0)"
    )
    needs_research: bool = Field(
        default=True,
        description="Whether this needs further research by Curators"
    )

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            HttpUrl: lambda v: str(v)
        }


class BrandDiscovery(Discovery):
    """Specific model for brand discoveries"""
    discovery_type: DiscoveryType = DiscoveryType.BRAND
    website: Optional[HttpUrl] = None
    description: Optional[str] = None


class ProductDiscovery(Discovery):
    """Specific model for product discoveries"""
    discovery_type: DiscoveryType = DiscoveryType.PRODUCT
    brand: str = Field(..., description="Brand name")
    product_family: Optional[str] = None
    estimated_price: Optional[str] = None
    estimated_weight: Optional[str] = None


class InsightDiscovery(Discovery):
    """Specific model for insight/tip discoveries"""
    discovery_type: DiscoveryType = DiscoveryType.INSIGHT
    summary: str = Field(..., description="Short summary of the insight")
    related_products: List[str] = Field(default_factory=list)
```

**Test**: Create `tests/test_discovery.py`
```python
from src.models.discovery import Discovery, DiscoveryType, SourceType, ProductDiscovery
from datetime import datetime

def test_discovery_creation():
    discovery = Discovery(
        discovery_id="test-001",
        discovery_type=DiscoveryType.PRODUCT,
        name="Test Tent",
        context="Found in a YouTube review",
        source_url="https://youtube.com/watch?v=test",
        source_type=SourceType.YOUTUBE,
        discovered_by="youtube_scanner"
    )
    assert discovery.name == "Test Tent"
    assert discovery.status == "pending"
    assert discovery.confidence == 0.5

def test_product_discovery():
    product = ProductDiscovery(
        discovery_id="prod-001",
        name="X-Mid 2P",
        brand="Durston Gear",
        context="Ultralight tent review",
        source_url="https://youtube.com/watch?v=test",
        source_type=SourceType.YOUTUBE,
        discovered_by="youtube_scanner",
        estimated_weight="28oz"
    )
    assert product.discovery_type == DiscoveryType.PRODUCT
    assert product.brand == "Durston Gear"
```

### 1.4 Create `src/models/research.py`

```python
"""
Data models for research conducted by the Curators team.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class SourceType(str, Enum):
    """Types of research sources"""
    MANUFACTURER = "manufacturer"
    RETAILER = "retailer"
    REVIEW_SITE = "review_site"
    BLOG = "blog"
    FORUM = "forum"
    OTHER = "other"

class ConfidenceLevel(str, Enum):
    """Confidence levels for research findings"""
    VERIFIED = "verified"           # From manufacturer/official source
    CORROBORATED = "corroborated"   # Multiple sources agree
    REPORTED = "reported"           # Single source, not verified
    UNCERTAIN = "uncertain"         # Conflicting information

class ResearchSource(BaseModel):
    """A single source consulted during research"""
    url: HttpUrl = Field(..., description="URL of the source")
    source_type: SourceType = Field(..., description="Type of source")
    data_found: List[str] = Field(
        default_factory=list,
        description="Fields/data points found from this source"
    )
    confidence: ConfidenceLevel = Field(..., description="Confidence in this source")
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(None, description="Additional notes about this source")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            HttpUrl: lambda v: str(v)
        }

class ResearchLog(BaseModel):
    """
    Complete research log for a discovery.
    Created by the Curators team.
    """
    # Identity
    discovery_id: str = Field(..., description="ID of the discovery being researched")
    research_id: str = Field(..., description="Unique ID for this research session")

    # Research details
    sources: List[ResearchSource] = Field(
        default_factory=list,
        description="All sources consulted during research"
    )
    verified_data: Dict = Field(
        default_factory=dict,
        description="Data verified through research"
    )
    conflicts_found: List[str] = Field(
        default_factory=list,
        description="Any conflicting information discovered"
    )
    missing_data: List[str] = Field(
        default_factory=list,
        description="Data points that could not be found"
    )

    # Quality metrics
    overall_confidence: ConfidenceLevel = Field(
        ...,
        description="Overall confidence in the research"
    )
    completeness_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="% of required fields found (0.0-1.0)"
    )

    # Metadata
    researched_by: str = Field(..., description="Name of the researcher agent")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # Output
    cypher_code: Optional[str] = Field(
        None,
        description="Generated Cypher code for graph update"
    )
    ready_for_load: bool = Field(
        default=False,
        description="Whether this is ready to load into the graph"
    )

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

**Test**: Create `tests/test_research.py`
```python
from src.models.research import ResearchLog, ResearchSource, SourceType, ConfidenceLevel

def test_research_source():
    source = ResearchSource(
        url="https://durstongear.com/products/x-mid-2p",
        source_type=SourceType.MANUFACTURER,
        data_found=["weight", "price", "materials"],
        confidence=ConfidenceLevel.VERIFIED
    )
    assert source.source_type == SourceType.MANUFACTURER
    assert len(source.data_found) == 3

def test_research_log():
    log = ResearchLog(
        discovery_id="disc-001",
        research_id="res-001",
        overall_confidence=ConfidenceLevel.VERIFIED,
        completeness_score=0.95,
        researched_by="autonomous_researcher"
    )
    assert log.completeness_score == 0.95
    assert log.ready_for_load == False
```

---

## Step 2: Create Source Registry Tool

### 2.1 Create `src/tools/source_registry_tool.py`

```python
"""
Source Registry Tool - Track visited URLs to prevent duplicate scanning.
Uses SQLite database for persistence across sessions.
"""
import sqlite3
from typing import Type, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, HttpUrl
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

    def __init__(self, db_path: str = "./data/source_registry.db"):
        """Initialize the tool and create database if needed"""
        super().__init__()
        self.db_path = db_path

        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

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
```

**Test**: Create `tests/test_source_registry.py`

```python
import os
import tempfile
from src.tools.source_registry_tool import SourceRegistryTool

def test_source_registry():
    # Use temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        tool = SourceRegistryTool(db_path=db_path)

        # Test check on new URL
        result = tool._run(action="check", url="https://youtube.com/watch?v=test123")
        assert "NEW" in result

        # Test add
        result = tool._run(
            action="add",
            url="https://youtube.com/watch?v=test123",
            source_type="youtube",
            items_found=5
        )
        assert "REGISTERED" in result

        # Test check on existing URL
        result = tool._run(action="check", url="https://youtube.com/watch?v=test123")
        assert "VISITED" in result
        assert "5" in result  # Items found

        # Test list
        result = tool._run(action="list")
        assert "youtube" in result

        # Test stats
        result = tool._run(action="stats")
        assert "Total sources" in result

    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)

if __name__ == "__main__":
    test_source_registry()
    print("✅ All source registry tests passed!")
```

---

## Step 3: Create Discovery Queue Tool

### 3.1 Create `src/tools/discovery_queue_tool.py`

```python
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

    def __init__(self, db_path: str = "./data/discovery_queue.db"):
        """Initialize the tool and create database if needed"""
        super().__init__()
        self.db_path = db_path

        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

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
```

**Test**: Create `tests/test_discovery_queue.py`

```python
import os
import tempfile
import json
from src.tools.discovery_queue_tool import DiscoveryQueueTool

def test_discovery_queue():
    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        tool = DiscoveryQueueTool(db_path=db_path)

        # Test enqueue
        discovery = {
            "discovery_id": "disc-001",
            "discovery_type": "product",
            "name": "Test Tent",
            "brand": "Test Brand"
        }
        result = tool._run(action="enqueue", discovery_data=discovery, priority=8)
        assert "ENQUEUED" in result

        # Test peek
        result = tool._run(action="peek")
        assert "disc-001" in result
        assert "priority=8" in result

        # Test status
        result = tool._run(action="status")
        assert "pending" in result

        # Test dequeue
        result = tool._run(action="dequeue")
        assert "DEQUEUED" in result
        assert "disc-001" in result

        # Test update
        result = tool._run(action="update", discovery_id="disc-001", new_status="verified")
        assert "UPDATED" in result

        # Queue should now be empty
        result = tool._run(action="peek")
        assert "EMPTY" in result

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)

if __name__ == "__main__":
    test_discovery_queue()
    print("✅ All discovery queue tests passed!")
```

---

## Step 4: Create Research Log Tool

### 4.1 Create `src/tools/research_log_tool.py`

```python
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

    def __init__(self, db_path: str = "./data/research_log.db"):
        """Initialize the tool and create database"""
        super().__init__()
        self.db_path = db_path

        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

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

                return f"LOGGED: Research step for {discovery_id}\n  Source: {source_url} ({source_type})\n  Data found: {len(data_found or [])}" fields\n  Confidence: {confidence}"

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
```

**Test**: Create `tests/test_research_log.py`

```python
import os
import tempfile
from src.tools.research_log_tool import ResearchLogTool

def test_research_log():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        tool = ResearchLogTool(db_path=db_path)

        # Test log
        result = tool._run(
            action="log",
            research_id="res-001",
            discovery_id="disc-001",
            source_url="https://durstongear.com/products/x-mid-2p",
            source_type="manufacturer",
            data_found=["weight", "price", "materials"],
            confidence="verified",
            notes="Official product page"
        )
        assert "LOGGED" in result

        # Log another step
        tool._run(
            action="log",
            research_id="res-001",
            discovery_id="disc-001",
            source_url="https://outdoorgearlab.com/reviews/x-mid-2p",
            source_type="review_site",
            data_found=["real_world_weight"],
            confidence="corroborated"
        )

        # Test retrieve
        result = tool._run(action="retrieve", discovery_id="disc-001")
        assert "res-001" in result
        assert "manufacturer" in result

        # Test complete
        result = tool._run(action="complete", research_id="res-001")
        assert "COMPLETED" in result

        # Test validate
        result = tool._run(action="validate", research_id="res-001")
        print(result)  # May be VALID or INVALID depending on completeness

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)

if __name__ == "__main__":
    test_research_log()
    print("✅ All research log tests passed!")
```

---

## Step 5: Run All Tests

Create `tests/run_all_tests.py`:

```python
"""
Run all Phase 1 foundation tests
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_tests():
    print("="*70)
    print("Running Phase 1 Foundation Tests")
    print("="*70)

    tests = [
        ("Flow State", "test_flow_state"),
        ("Discovery Models", "test_discovery"),
        ("Research Models", "test_research"),
        ("Source Registry Tool", "test_source_registry"),
        ("Discovery Queue Tool", "test_discovery_queue"),
        ("Research Log Tool", "test_research_log")
    ]

    passed = 0
    failed = 0

    for name, module in tests:
        print(f"\n{name}...")
        try:
            exec(f"from {module} import test_{module.split('_', 1)[1]}")
            exec(f"test_{module.split('_', 1)[1]}()")
            print(f"  ✅ {name} PASSED")
            passed += 1
        except Exception as e:
            print(f"  ❌ {name} FAILED: {e}")
            failed += 1

    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)

    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
```

---

## Success Criteria

✅ **Phase 1 Complete When**:
1. All data models defined and tested
2. Source Registry Tool working (check, add, list, stats)
3. Discovery Queue Tool working (enqueue, dequeue, peek, status, update)
4. Research Log Tool working (log, retrieve, complete, validate)
5. All tests passing
6. Databases created in `data/` directory
7. Documentation updated

## Next Steps

After completing Phase 1, you'll have:
- ✅ Solid foundation for state management
- ✅ Shared tools all teams can use
- ✅ Data models for discoveries and research
- ✅ Testing infrastructure

Then proceed to **Phase 2: Gear-heads Team** where we'll build the actual scanner agents that use these tools.

---

## Troubleshooting

**Issue**: Import errors when running tests
- **Solution**: Ensure `src/` is in your Python path or run tests from project root

**Issue**: Database permission errors
- **Solution**: Ensure `data/` directory exists and is writable

**Issue**: Pydantic validation errors
- **Solution**: Check that all required fields are provided when creating models

**Issue**: SQLite errors
- **Solution**: Check that database paths are correct and parent directories exist
