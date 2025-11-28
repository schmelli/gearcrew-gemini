# CrewAI Research Findings: Hierarchical & Async Capabilities (2025)

**Research Date**: 2025-11-28
**CrewAI Version**: v1.0.0a1 (September 30, 2025)

## Executive Summary

CrewAI provides robust support for building multi-team agent systems with:
- ✅ **Flows** for event-driven multi-crew orchestration
- ✅ **Hierarchical processes** for manager-worker delegation
- ✅ **Async execution** at both task and crew levels
- ✅ **State management** with persistence
- ✅ **Custom tools** for external integrations

## Key Capabilities for Our Gear Collection System

### 1. Flows: Multi-Crew Orchestration

Flows enable event-driven coordination between multiple crews with state management.

**Key Features**:
- `@start()`: Entry point(s) - can have multiple for parallel execution
- `@listen(method)`: Triggers when specified method completes
- `@router(method)`: Conditional branching based on output
- `and_(m1, m2)`: Wait for ALL methods to complete
- `or_(m1, m2)`: Trigger when ANY method completes
- State persistence with `@persist` decorator

**Example Architecture**:
```python
from crewai.flow.flow import Flow, listen, start, router, and_, or_
from pydantic import BaseModel
from typing import Set, List, Dict

class GearCollectionState(BaseModel):
    visited_sources: Set[str] = set()
    discovered_brands: List[str] = []
    discovered_products: List[Dict] = []
    collected_insights: List[Dict] = []
    graph_updates: int = 0

class GearCollectionFlow(Flow[GearCollectionState]):

    @start()
    def continuous_scan(self):
        """Gear-heads team continuously scans sources"""
        result = GearHeadsCrew().crew().kickoff()
        return result.raw

    @listen(continuous_scan)
    def filter_discoveries(self, discoveries):
        """Filter out already-known items using state"""
        new_items = [
            item for item in discoveries
            if item['id'] not in self.state.visited_sources
        ]
        self.state.visited_sources.update(item['id'] for item in new_items)
        return new_items

    @listen(filter_discoveries)
    def curate_and_research(self, new_items):
        """Curators verify and research missing data"""
        return CuratorsCrew().crew().kickoff(inputs={"items": new_items})

    @listen(curate_and_research)
    def update_graph(self, curated_data):
        """Update GearGraph with verified data"""
        result = GraphLoaderCrew().crew().kickoff(inputs={"data": curated_data})
        self.state.graph_updates += 1
        return result
```

### 2. Hierarchical Process: Manager-Worker Teams

Hierarchical process enables manager agents to coordinate specialized workers.

**Two Configuration Options**:

**Option A: Auto-created Manager**
```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, extractor, validator],
    tasks=[research_task, extract_task, validate_task],
    process=Process.hierarchical,
    manager_llm="gpt-4o",  # CrewAI creates manager automatically
    planning=True
)
```

**Option B: Custom Manager (Recommended for fine control)**
```python
from crewai import Agent

# Gear-heads Team Manager
gear_heads_manager = Agent(
    role="Gear Discovery Coordinator",
    goal="Coordinate continuous scanning of gear sources and handoff discoveries to Curators",
    backstory="""You manage a team of gear enthusiasts who continuously scan:
    - YouTube reviews and gear videos
    - Manufacturer websites and product pages
    - Outdoor gear blogs and reviews
    - Reddit and forum discussions

    Your process:
    1. Assign source scanning to specialized agents (YouTube, Websites, Forums)
    2. Collect discoveries (brands, products, insights)
    3. Validate discovery quality (ensure complete metadata)
    4. Handoff to Curators team for verification

    CRITICAL: You must delegate work, not do it yourself. Your workers have the tools.""",
    allow_delegation=True,  # ESSENTIAL for manager role
    llm="gemini-2.5-pro"
)

# Curators Team Manager
curators_manager = Agent(
    role="Data Verification Coordinator",
    goal="Verify discoveries against GearGraph and autonomously research missing data",
    backstory="""You manage data curators who:
    1. Check if discovered brands/products already exist in GearGraph
    2. Identify missing or incomplete information
    3. Autonomously research missing data from authoritative sources
    4. Document all sources and research steps
    5. Prepare verified data for graph loading

    Quality standards:
    - All product weights must be verified from manufacturer
    - All URLs must be valid and direct to product page
    - All insights must cite original source

    Delegate research tasks to specialists. Track all sources meticulously.""",
    allow_delegation=True,
    llm="gemini-2.5-pro"
)
```

**IMPORTANT LIMITATION**: Manager agents CANNOT have tools directly. Workaround: Create assistant agents with tools that managers delegate to.

### 3. Async Execution: Parallel Processing

**Task-Level Async** (parallel tasks within a crew):
```python
from crewai import Task

# Multiple sources scanned in parallel
youtube_scan = Task(
    description="Scan YouTube for new gear reviews",
    agent=youtube_scanner,
    async_execution=True  # Runs without blocking
)

website_scan = Task(
    description="Scan manufacturer websites for new products",
    agent=website_scanner,
    async_execution=True
)

reddit_scan = Task(
    description="Scan r/Ultralight for gear discussions",
    agent=reddit_scanner,
    async_execution=True
)

# Synchronization task waits for ALL async tasks
aggregate_discoveries = Task(
    description="Aggregate all discoveries from sources",
    agent=aggregator,
    context=[youtube_scan, website_scan, reddit_scan]  # Waits for all three
)
```

**Crew-Level Async** (parallel crews):
```python
import asyncio

async def run_parallel_teams():
    results = await asyncio.gather(
        gear_heads_crew.kickoff_async(),
        curators_crew.kickoff_async(),
        graph_loader_crew.kickoff_async()
    )
    return results

# Execute multiple crews concurrently
results = asyncio.run(run_parallel_teams())
```

### 4. State Management & Source Registry

**Custom Tool for Visited Sources Registry**:
```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import sqlite3

class SourceRegistryInput(BaseModel):
    action: str = Field(..., description="Action: 'check', 'add', 'list'")
    url: str = Field(None, description="Source URL")

class SourceRegistryTool(BaseTool):
    name: str = "Source Registry"
    description: str = "Track visited sources to avoid duplication. Actions: check (is URL visited?), add (mark URL as visited), list (show all)"
    args_schema: type[BaseModel] = SourceRegistryInput

    def __init__(self, db_path: str = "./gear_sources.db"):
        super().__init__()
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS visited_sources (
                url TEXT PRIMARY KEY,
                source_type TEXT,  -- youtube, website, blog, reddit
                visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                items_discovered INTEGER DEFAULT 0,
                status TEXT DEFAULT 'processed'
            )
        """)
        conn.commit()
        conn.close()

    def _run(self, action: str, url: str = None) -> str:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if action == "check":
            cursor.execute("SELECT status, visited_at FROM visited_sources WHERE url = ?", (url,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return f"VISITED: {url} on {row[1]} (status: {row[0]})"
            return f"NEW: {url} not in registry"

        elif action == "add":
            cursor.execute(
                "INSERT OR REPLACE INTO visited_sources (url, status) VALUES (?, 'processed')",
                (url,)
            )
            conn.commit()
            conn.close()
            return f"REGISTERED: {url}"

        elif action == "list":
            cursor.execute("SELECT url, source_type, visited_at FROM visited_sources ORDER BY visited_at DESC LIMIT 50")
            sources = cursor.fetchall()
            conn.close()
            return f"Recent sources: {sources}"

        conn.close()
        return "Invalid action. Use: check, add, or list"
```

**Flow State for Shared Context**:
```python
from crewai.flow.persistence import persist

@persist  # Auto-saves state to SQLite
class PersistentGearFlow(Flow[GearCollectionState]):
    @start()
    def scan_sources(self):
        # State automatically persisted after each step
        if url not in self.state.visited_sources:
            self.state.visited_sources.add(url)
            # Process new source
        return discoveries
```

### 5. Latest 2025 Features

**Version v1.0.0a1** (September 30, 2025) introduced:

- ✅ **Flow State Persistence**: `@persist` decorator with unique IDs
- ✅ **Partial Flow Resumability**: Resume flows from intermediate points
- ✅ **Flow Visualization**: `flow.plot()` for workflow diagrams
- ✅ **Standalone Agent Execution**: `Agent().kickoff()` without crew
- ✅ **Async Tool Execution**: More efficient parallel tool calls
- ✅ **Thread-Safe Context**: Safe concurrent operations
- ✅ **Mem0 Integration**: User preferences and memory retrieval
- ✅ **Event Emission System**: Track memory, LLM calls, guardrails

## Recommended Architecture for Gear Collection System

```
┌────────────────────────────────────────────────────────────────┐
│                   GearCollectionFlow                           │
│         (Event-driven orchestration with persistence)          │
└──────────────┬─────────────────┬────────────────┬──────────────┘
               │                 │                │
       ┌───────▼────────┐ ┌──────▼──────┐ ┌──────▼──────────┐
       │ Gear-heads     │ │  Curators   │ │  Graph Loader  │
       │ Crew           │ │  Crew       │ │  Crew          │
       │ (Hierarchical) │ │(Hierarchical)│ │ (Hierarchical) │
       └────────────────┘ └─────────────┘ └────────────────┘
               │                 │
       ┌───────┴─────────┐       │
       │  Parallel       │       │
       │  Scanners       │       │
       │  (async)        │       │
       ├─────────────────┤       │
       │ • YouTube       │       │
       │ • Websites      │       │
       │ • Blogs         │       │
       │ • Reddit        │       │
       └─────────────────┘       │
               │                 │
       ┌───────▼─────────────────▼────┐
       │    Shared Services            │
       ├───────────────────────────────┤
       │ • Source Registry (SQLite)    │
       │ • GearGraph Tools             │
       │ • Firecrawl Extract/Scrape    │
       │ • Web Search                  │
       └───────────────────────────────┘
```

## Implementation Strategy

### Phase 1: Core Infrastructure
1. Source Registry Tool (SQLite-based)
2. Flow State Management
3. Basic Gear-heads crew with single scanner

### Phase 2: Parallel Scanning
1. YouTube scanner agent
2. Website scanner agent
3. Blog/Reddit scanner agent
4. Async task execution setup

### Phase 3: Curators Team
1. Graph verification agent
2. Autonomous researcher agent
3. Data validator agent
4. Source citation agent

### Phase 4: Flow Orchestration
1. Connect Gear-heads → Curators via Flow
2. Add conditional routing
3. Implement state persistence
4. Add monitoring and logging

### Phase 5: Production Hardening
1. Error handling and recovery
2. Human escalation for quality issues
3. Performance optimization
4. Observability and metrics

## Sources

- [Sequential Processes - CrewAI](https://docs.crewai.com/how-to/sequential-process)
- [Hierarchical Process - CrewAI](https://docs.crewai.com/how-to/hierarchical-process)
- [Changelog - CrewAI](https://docs.crewai.com/en/changelog)
- [Flows - CrewAI](https://docs.crewai.com/en/concepts/flows)
- [Kickoff Crew Asynchronously - CrewAI](https://docs.crewai.com/how-to/kickoff-async)
- [CrewAI Flow - GeeksforGeeks](https://www.geeksforgeeks.org/artificial-intelligence/crewai-flow/)
- [What are Agentic Flows in CrewAI? - Analytics Vidhya](https://www.analyticsvidhya.com/blog/2024/11/agentic-flows-in-crewai/)
