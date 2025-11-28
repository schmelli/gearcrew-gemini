# Complete Implementation Roadmap: All 6 Phases

**Project**: GearCrew-Gemini Multi-Team Async System
**Total Duration**: 6-8 weeks
**Status**: Planning Phase

---

## 📋 Phase Overview

| Phase | Name | Duration | Dependencies | Status |
|-------|------|----------|--------------|--------|
| 1 | Foundation | 3-4 days | None | ⏭️ Next |
| 2 | Gear-heads Team | 5-7 days | Phase 1 | Planned |
| 3 | Curators Team | 5-7 days | Phases 1, 2 | Planned |
| 4 | Graph Architects | 3-4 days | Phases 1-3 | Planned |
| 5 | Flow Integration | 5-7 days | Phases 1-4 | Planned |
| 6 | Production Hardening | 5-7 days | Phases 1-5 | Planned |

---

# Phase 1: Foundation (3-4 days)

## Goals
✅ Build core infrastructure
✅ Create shared tools and state management
✅ Establish data models
✅ Set up testing framework

## Deliverables

### 1. Data Models (`src/models/`)

**`flow_state.py`** - Shared state for Flows
```python
class GearCollectionState(BaseModel):
    visited_sources: Set[str]
    pending_discoveries: List[str]
    research_in_progress: Dict[str, str]
    graph_nodes_created: int
    quality_threshold: float = 0.95
    # ... full implementation in phase_1_foundation.md
```

**`discovery.py`** - Discovery data structures
```python
class DiscoveryType(Enum):
    BRAND = "brand"
    PRODUCT = "product"
    INSIGHT = "insight"

class Discovery(BaseModel):
    discovery_id: str
    discovery_type: DiscoveryType
    name: str
    source_url: HttpUrl
    discovered_by: str
    # ... see phase_1_foundation.md
```

**`research.py`** - Research logging structures
```python
class ResearchLog(BaseModel):
    research_id: str
    discovery_id: str
    sources: List[ResearchSource]
    completeness_score: float
    overall_confidence: ConfidenceLevel
    # ... see phase_1_foundation.md
```

### 2. Core Tools (`src/tools/`)

**`source_registry_tool.py`** - Track visited URLs (SQLite)
- Actions: check, add, list, stats
- Prevents duplicate scanning
- Tracks source types and discovery counts

**`discovery_queue_tool.py`** - Manage discovery pipeline (SQLite)
- Actions: enqueue, dequeue, peek, status, update
- Priority-based queue
- Buffer between teams

**`research_log_tool.py`** - Document research (SQLite)
- Actions: log, retrieve, complete, validate
- Source citations
- Quality scoring

### 3. Testing

**All tools tested with**:
- Unit tests for each tool
- Integration tests with temp databases
- Coverage for all actions/methods

## Success Criteria
- [ ] All 3 data model files created and tested
- [ ] All 3 tools implemented and passing tests
- [ ] SQLite databases auto-create in `data/` directory
- [ ] Test suite runs cleanly
- [ ] Documentation complete

**Detailed Guide**: See `docs/implementation_plans/phase_1_foundation.md`

---

# Phase 2: Gear-heads Team (5-7 days)

## Goals
✅ Build discovery team with hierarchical structure
✅ Implement 4 specialized scanner agents
✅ Enable parallel async scanning
✅ Integrate with Phase 1 tools

## Architecture

```
Discovery Coordinator (Manager)
    ├── YouTube Scanner (async)
    ├── Website Scanner (async)
    ├── Blog Scanner (async)
    └── Reddit Scanner (async)
         └── All use Source Registry + Discovery Queue
```

## Deliverables

### 1. Manager Agent (`src/agents/discovery_manager.py`)

```python
from crewai import Agent

discovery_manager = Agent(
    role="Gear Discovery Coordinator",
    goal="Coordinate continuous scanning and handoff discoveries to Curators",
    backstory="""You manage gear enthusiasts who scan:
    - YouTube: New reviews and gear videos
    - Websites: Manufacturer product pages
    - Blogs: Outdoor gear reviews
    - Reddit: r/Ultralight, r/CampingGear discussions

    DELEGATION STRATEGY:
    1. Identify source type from input
    2. Assign to appropriate scanner:
       - YouTube URLs → YouTube Scanner
       - Manufacturer domains → Website Scanner
       - Blog/review sites → Blog Scanner
       - Reddit/forum → Reddit Scanner
    3. Validate discoveries have complete metadata
    4. Register sources in Source Registry
    5. Enqueue discoveries for Curators

    You delegate - workers have the tools.""",
    allow_delegation=True,  # CRITICAL
    llm=get_gemini_pro(),
    verbose=True
)
```

### 2. Scanner Agents (`src/agents/scanners/`)

**YouTube Scanner** - Scans video transcripts and descriptions
```python
youtube_scanner = Agent(
    role="YouTube Gear Video Scanner",
    goal="Extract gear mentions from YouTube reviews and demos",
    backstory="""You watch gear review videos and extract:
    - Product names and brands mentioned
    - Specs stated in video (weight, price, features)
    - Practical tips and insights
    - Links in video description

    Use Source Registry to avoid re-scanning videos.
    Use Discovery Queue to hand off findings.""",
    tools=[
        source_registry,
        discovery_queue,
        youtube_transcript_tool,  # NEW: Extract transcripts
        firecrawl_scrape          # For video descriptions
    ],
    llm=get_gemini_flash(),  # Faster for simple extraction
    verbose=True
)
```

**Website Scanner** - Crawls manufacturer sites
```python
website_scanner = Agent(
    role="Manufacturer Website Scanner",
    goal="Extract product data from official manufacturer pages",
    backstory="""You visit manufacturer websites to find:
    - New product releases
    - Product specifications
    - Official prices and weights
    - Product images and URLs

    Priority sources: Durston Gear, Zpacks, Hyperlite Mountain Gear,
    NEMO, Big Agnes, Western Mountaineering, Enlightened Equipment, etc.

    Use Source Registry to track visited pages.
    Use Firecrawl Extract for structured data.""",
    tools=[
        source_registry,
        discovery_queue,
        firecrawl_extract,  # EXISTING from Phase 1
        firecrawl_scrape,
        search_tool         # EXISTING
    ],
    llm=get_gemini_flash(),
    verbose=True
)
```

**Blog Scanner** - Reads gear blogs and reviews
```python
blog_scanner = Agent(
    role="Outdoor Gear Blog Scanner",
    goal="Extract gear reviews and comparisons from outdoor blogs",
    backstory="""You read outdoor gear blogs for:
    - Gear reviews and comparisons
    - Field reports and trip reports
    - Gear recommendations
    - Real-world usage insights

    Key blogs: OutdoorGearLab, SectionHiker, The Trek, Halfway Anywhere,
    Darwin on the Trail, etc.

    Extract product mentions and practical tips.""",
    tools=[source_registry, discovery_queue, firecrawl_scrape, search_tool],
    llm=get_gemini_flash(),
    verbose=True
)
```

**Reddit Scanner** - Monitors forums
```python
reddit_scanner = Agent(
    role="Reddit/Forum Gear Scanner",
    goal="Monitor r/Ultralight and outdoor forums for gear discussions",
    backstory="""You monitor:
    - r/Ultralight
    - r/CampingGear
    - r/WildernessBackpacking
    - WhiteBlaze forums
    - Backpacking Light forums

    Extract:
    - User gear recommendations
    - Product experiences and reviews
    - Common issues and solutions
    - Budget alternatives

    Focus on high-value discussions (50+ upvotes/replies).""",
    tools=[source_registry, discovery_queue, reddit_api_tool, search_tool],
    llm=get_gemini_flash(),
    verbose=True
)
```

### 3. NEW Tool: YouTube Transcript Tool

```python
# src/tools/youtube_transcript_tool.py
from youtube_transcript_api import YouTubeTranscriptApi

class YouTubeTranscriptTool(BaseTool):
    """Extract transcripts from YouTube videos"""
    def _run(self, video_url: str) -> str:
        video_id = extract_video_id(video_url)
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return format_transcript(transcript)
```

### 4. Discovery Tasks (`src/tasks/discovery_tasks.py`)

```python
from crewai import Task

# Parallel scanning tasks (async_execution=True)
youtube_scan_task = Task(
    description="""Scan YouTube for new gear review videos.
    1. Search for recent uploads (past week)
    2. Check Source Registry - skip visited videos
    3. Extract product mentions from transcripts
    4. Create Discovery objects for each finding
    5. Enqueue discoveries
    6. Register video URLs as visited""",
    expected_output="List of discoveries with source citations",
    agent=youtube_scanner,
    async_execution=True  # Runs in parallel
)

website_scan_task = Task(
    description="""Scan manufacturer websites for new products.
    Target sites: Durston, Zpacks, HMG, NEMO, Big Agnes
    ...""",
    expected_output="List of product discoveries",
    agent=website_scanner,
    async_execution=True
)

blog_scan_task = Task(
    description="""Scan outdoor gear blogs...""",
    agent=blog_scanner,
    async_execution=True
)

reddit_scan_task = Task(
    description="""Monitor r/Ultralight...""",
    agent=reddit_scanner,
    async_execution=True
)

# Aggregation task (waits for all scanners)
aggregate_task = Task(
    description="""Aggregate discoveries from all scanners.
    1. Wait for all scanners to complete
    2. Collect all Discovery objects
    3. Remove duplicates (same product found in multiple sources)
    4. Prioritize by source reliability
    5. Generate summary statistics
    6. Hand off to Curators team""",
    expected_output="Aggregated discovery report with statistics",
    agent=discovery_manager,
    context=[youtube_scan_task, website_scan_task, blog_scan_task, reddit_scan_task]
)
```

### 5. Crew Definition (`src/crews/gear_heads_crew.py`)

```python
from crewai import Crew, Process

class GearHeadsCrew:
    """The Gear-heads discovery team"""

    def __init__(self):
        self.manager = create_discovery_manager()
        self.scanners = create_scanner_agents()
        self.tasks = create_discovery_tasks()

    def crew(self) -> Crew:
        return Crew(
            agents=[self.manager] + self.scanners,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self.manager,  # Use custom manager
            memory=True,  # Remember past scans
            verbose=True
        )

    def kickoff(self, inputs: dict = None):
        """Start discovery process"""
        return self.crew().kickoff(inputs=inputs or {})
```

## Testing Strategy

```python
# tests/test_gear_heads_crew.py
def test_youtube_scanner():
    """Test YouTube scanner with sample video"""
    scanner = create_youtube_scanner()
    result = scanner.execute_task(
        task="Scan this video: https://youtube.com/watch?v=test",
        context="Test video about ultralight tents"
    )
    assert "discoveries" in result

def test_discovery_manager_delegation():
    """Test manager delegates to correct scanner"""
    manager = create_discovery_manager()
    # Manager should assign YouTube URL to YouTube scanner
    ...

def test_parallel_scanning():
    """Test all scanners run in parallel"""
    crew = GearHeadsCrew().crew()
    start = time.time()
    result = crew.kickoff()
    duration = time.time() - start
    # Should complete faster than sequential (< 4x single scan time)
    assert duration < expected_sequential_time
```

## Success Criteria
- [ ] Manager agent delegates correctly based on source type
- [ ] All 4 scanner agents implemented and working
- [ ] Async parallel execution confirmed (faster than sequential)
- [ ] Source Registry integration working (no duplicate scans)
- [ ] Discovery Queue integration working (findings queued)
- [ ] Tests passing
- [ ] Sample run discovers 10+ items from mixed sources

---

# Phase 3: Curators Team (5-7 days)

## Goals
✅ Build verification and research team
✅ Implement autonomous research capability
✅ Integrate with GearGraph for verification
✅ Generate validated Cypher code

## Architecture

```
Data Verification Coordinator (Manager)
    ├── Graph Verifier (check existing data)
    ├── Autonomous Researcher (fill missing data)
    ├── Data Validator (ensure quality)
    └── Source Citation Agent (document sources)
```

## Deliverables

### 1. Manager Agent (`src/agents/curators_manager.py`)

```python
curators_manager = Agent(
    role="Data Verification Coordinator",
    goal="Verify discoveries and research missing data autonomously",
    backstory="""You coordinate data curation:

    WORKFLOW:
    1. Receive discovery from queue
    2. Assign to Graph Verifier:
       - Check if brand/product exists in GearGraph
       - If complete → skip to validation
       - If missing/incomplete → proceed to research

    3. Assign to Autonomous Researcher:
       - Priority: manufacturer website (highest authority)
       - Secondary: authorized retailers (REI, Backcountry)
       - Tertiary: review sites (OutdoorGearLab, SectionHiker)
       - Extract: weight, price, materials, specs, URLs, images

    4. Assign to Data Validator:
       - Verify all required fields present
       - Check units standardized
       - Ensure URLs valid
       - No contradictions between sources

    5. Assign to Source Citation Agent:
       - Document all sources consulted
       - Note conflicts found
       - Calculate confidence level

    6. Generate Cypher code if validated
    7. Handoff to Graph Architects

    CRITICAL: Document everything. Never load unverified data.""",
    allow_delegation=True,
    llm=get_gemini_pro(),
    verbose=True
)
```

### 2. Worker Agents (`src/agents/curators/`)

**Graph Verifier**
```python
graph_verifier = Agent(
    role="GearGraph Data Verifier",
    goal="Check what data already exists in GearGraph",
    backstory="""You query GearGraph to determine:
    - Does this brand exist?
    - Does this product exist?
    - What data is missing or incomplete?

    Use Find Similar Nodes tool to check for:
    - Exact matches
    - Fuzzy matches (typos, variations)
    - Related products

    Report findings: NEW, INCOMPLETE, or COMPLETE""",
    tools=[find_similar_nodes_tool],  # EXISTING from GearGraphTools
    llm=get_gemini_flash(),
    verbose=True
)
```

**Autonomous Researcher**
```python
autonomous_researcher = Agent(
    role="Autonomous Gear Data Researcher",
    goal="Research missing data from authoritative sources",
    backstory="""You autonomously research gear data:

    RESEARCH PROTOCOL:
    1. Start with manufacturer website (official source)
       - Use Firecrawl Extract for structured data
       - Extract: specs, price, weight, materials, images
       - Confidence: VERIFIED

    2. Cross-reference with retailers
       - REI, Backcountry, Moosejaw
       - Verify price and availability
       - Confidence: CORROBORATED

    3. Check review sites if needed
       - OutdoorGearLab, SectionHiker
       - Real-world weights, user feedback
       - Confidence: REPORTED

    4. Document EVERY source in Research Log
       - URL, source type, data found
       - Timestamp and confidence level

    REQUIRED FIELDS:
    - name, brand, weight (grams + ounces)
    - price (USD), type, productUrl, imageUrl

    OPTIONAL BUT VALUABLE:
    - materials, capacity, dimensions, R-value, etc.

    Never fabricate data. If not found, mark as missing.""",
    tools=[
        research_log_tool,        # NEW from Phase 1
        firecrawl_extract,        # EXISTING
        firecrawl_scrape,         # EXISTING
        search_tool               # EXISTING
    ],
    llm=get_gemini_pro(),  # Needs strong reasoning
    verbose=True
)
```

**Data Validator**
```python
data_validator = Agent(
    role="Data Quality Validator",
    goal="Ensure data completeness and consistency",
    backstory="""You validate research results:

    QUALITY CHECKS:
    1. Completeness:
       - All required fields present?
       - At least 85% of optional fields filled?

    2. Consistency:
       - Weight in both grams AND ounces?
       - Values make sense? (tent can't weigh 1oz)
       - URLs valid and accessible?

    3. Standardization:
       - Units consistent (grams, USD)
       - Formats correct (numbers not strings)

    4. Source Quality:
       - At least one VERIFIED source?
       - Multiple sources agree?
       - Conflicts documented?

    PASS criteria: ≥85% complete, no contradictions, ≥1 verified source
    FAIL: Request more research or flag for human review""",
    tools=[research_log_tool],
    llm=get_gemini_flash(),
    verbose=True
)
```

**Source Citation Agent**
```python
citation_agent = Agent(
    role="Research Documentation Specialist",
    goal="Maintain meticulous source citations",
    backstory="""You create audit trails:

    For each research session, document:
    1. All sources consulted (URLs, types)
    2. Data found from each source
    3. Conflicts or discrepancies
    4. Confidence assessment
    5. Research duration

    Output format:
    ```
    Research Log for [Product]
    Sources (3):
      1. [VERIFIED] https://manufacturer.com - weight, price, materials
      2. [CORROBORATED] https://rei.com - price, availability
      3. [REPORTED] https://outdoorgearlab.com - real-world weight

    Findings: All data verified. Minor discrepancy in weight
              (manufacturer: 28oz, field test: 29oz) - within tolerance.

    Completeness: 95% (missing: dimensions)
    Confidence: VERIFIED
    Ready for graph load: YES
    ```

    Use Research Log tool to persist all documentation.""",
    tools=[research_log_tool],
    llm=get_gemini_flash(),
    verbose=True
)
```

### 3. Curation Tasks (`src/tasks/curation_tasks.py`)

```python
verify_task = Task(
    description="""Check GearGraph for existing data on this discovery.
    Use Find Similar Nodes to search for:
    - Exact brand/product name matches
    - Similar names (fuzzy matching)
    Report: NEW, INCOMPLETE (missing fields), or COMPLETE""",
    expected_output="Verification report with existing data status",
    agent=graph_verifier
)

research_task = Task(
    description="""Research missing data autonomously.
    1. Start with manufacturer website
    2. Cross-reference retailers
    3. Check review sites if needed
    4. Log every source consulted
    5. Extract all available specs
    Priority: weight, price, productUrl, imageUrl""",
    expected_output="Complete product data with source citations",
    agent=autonomous_researcher,
    context=[verify_task]  # Wait for verification
)

validate_task = Task(
    description="""Validate research quality.
    Check: completeness ≥85%, no contradictions, ≥1 verified source
    Calculate quality score""",
    expected_output="Validation report with pass/fail and quality score",
    agent=data_validator,
    context=[research_task]
)

citation_task = Task(
    description="""Document complete research trail.
    Create research log with all sources, findings, confidence""",
    expected_output="Formatted research log ready for audit",
    agent=citation_agent,
    context=[research_task, validate_task]
)

cypher_generation_task = Task(
    description="""Generate Cypher code for graph update.
    Based on validated data:
    1. Create MERGE statements (not CREATE - avoid duplicates)
    2. Separate ProductFamily and GearItem
    3. Include all relationships (MANUFACTURES, IS_VARIANT_OF)
    4. Add Insight nodes with HAS_TIP relationships
    5. Follow Architect agent patterns from existing system

    Include source citations as node properties.""",
    expected_output="Valid Cypher code ready for execution",
    agent=curators_manager,  # Manager generates final code
    context=[citation_task]
)
```

### 4. Crew Definition (`src/crews/curators_crew.py`)

```python
class CuratorsCrew:
    def __init__(self):
        self.manager = create_curators_manager()
        self.workers = create_curator_agents()
        self.tasks = create_curation_tasks()

    def crew(self) -> Crew:
        return Crew(
            agents=[self.manager] + self.workers,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self.manager,
            memory=True,
            verbose=True
        )
```

## Testing

```python
def test_graph_verification():
    """Test checking existing data in GearGraph"""
    verifier = create_graph_verifier()
    result = verifier.check_product("Durston X-Mid 2P")
    assert "exists" in result or "missing" in result

def test_autonomous_research():
    """Test researching a real product"""
    researcher = create_autonomous_researcher()
    result = researcher.research_product("Zpacks Arc Haul Ultra")
    assert "weight" in result
    assert "sources" in result

def test_research_logging():
    """Test research documentation"""
    log = create_research_log()
    log.log_source(url="https://zpacks.com/...", data_found=["weight", "price"])
    log.complete()
    assert log.completeness_score > 0.8
```

## Success Criteria
- [ ] Graph Verifier correctly identifies existing/missing data
- [ ] Autonomous Researcher finds data from 3+ source types
- [ ] Research Log documents all sources consulted
- [ ] Data Validator catches incomplete/inconsistent data
- [ ] Generated Cypher code follows correct patterns
- [ ] Tests passing
- [ ] Sample run: discover → verify → research → validate → generate Cypher

---

# Phase 4: Graph Architects Team (3-4 days)

## Goals
✅ Build safe graph update team
✅ Validate and execute Cypher code
✅ Maintain graph integrity
✅ Monitor for orphaned nodes

## Architecture

```
Database Gatekeeper (Manager)
    ├── Cypher Validator (review code)
    ├── Graph Loader (execute updates) [REUSE EXISTING]
    └── Relationship Gardener (maintain integrity)
```

## Deliverables

### 1. Manager Agent

```python
gatekeeper_manager = Agent(
    role="Database Gatekeeper",
    goal="Execute verified updates safely and maintain integrity",
    backstory="""You protect the graph database:

    WORKFLOW:
    1. Receive Cypher code from Curators
    2. Assign to Cypher Validator:
       - Check syntax
       - Verify MERGE usage (not CREATE for duplicates)
       - Ensure relationship patterns correct
       - Validate property types

    3. If validated, assign to Graph Loader:
       - Execute query with logging
       - Capture any errors
       - Record nodes/relationships created

    4. Assign to Relationship Gardener:
       - Check for orphaned Insights
       - Verify all relationships created
       - Suggest connection improvements

    SAFETY RULES:
    - Never execute unvalidated code
    - Always log execution reason
    - Rollback on errors
    - Report statistics""",
    allow_delegation=True,
    llm=get_gemini_pro(),
    verbose=True
)
```

### 2. Worker Agents

**Cypher Validator**
```python
cypher_validator = Agent(
    role="Cypher Code Validator",
    goal="Review and validate Cypher code for safety and correctness",
    backstory="""You review Cypher code for:

    SYNTAX CHECKS:
    - Valid Cypher syntax
    - No SQL injection patterns
    - Proper escaping of strings

    PATTERN CHECKS:
    - MERGE (not CREATE) for brands/products
    - Correct relationship directions
    - Node labels from ontology
    - Property types match schema

    BEST PRACTICES:
    - UNWIND for batch operations
    - Unquoted map keys in Memgraph
    - Consistent variable naming
    - Relationships created in same query as nodes

    REJECT if:
    - DROP or DELETE without WHERE clause
    - CREATE instead of MERGE for entities
    - Missing relationship patterns
    - Invalid property types""",
    tools=[validate_ontology_tool],  # EXISTING
    llm=get_gemini_flash(),
    verbose=True
)
```

**Graph Loader** (Reuse existing agent)
```python
# Already exists in src/agents.py as 'gatekeeper'
# Just wrap it for consistency
graph_loader = existing_gatekeeper_agent
```

**Relationship Gardener**
```python
relationship_gardener = Agent(
    role="Graph Integrity Specialist",
    goal="Monitor and maintain graph relationships",
    backstory="""You ensure graph health:

    POST-UPDATE CHECKS:
    1. Find orphaned Insight nodes:
       ```cypher
       MATCH (i:Insight)
       WHERE NOT (i)-[]-()
       RETURN count(i)
       ```

    2. Verify expected relationships:
       - All GearItems have [:IS_VARIANT_OF] → ProductFamily?
       - All ProductFamilies have [:MANUFACTURES] ← Brand?
       - All Insights have [:HAS_TIP] connections?

    3. Suggest improvements:
       - Products with similar names (potential duplicates)
       - Missing category connections
       - Potential new relationships

    AUTO-FIX orphaned Insights:
    - If Insight mentions product name in content,
      try to link it automatically
    - Otherwise, connect to General category""",
    tools=[execute_cypher_tool, find_similar_nodes_tool],
    llm=get_gemini_flash(),
    verbose=True
)
```

### 3. Tasks

```python
validate_cypher_task = Task(
    description="Validate Cypher code for safety and correctness",
    agent=cypher_validator
)

execute_update_task = Task(
    description="Execute validated Cypher code",
    agent=graph_loader,
    context=[validate_cypher_task]
)

maintain_integrity_task = Task(
    description="Check for orphans and maintain relationships",
    agent=relationship_gardener,
    context=[execute_update_task]
)
```

## Success Criteria
- [ ] Cypher Validator catches invalid code
- [ ] Graph Loader executes safely with logging
- [ ] Relationship Gardener finds and fixes orphans
- [ ] No duplicate nodes created
- [ ] All relationships properly formed

---

# Phase 5: Flow Integration (5-7 days)

## Goals
✅ Connect all teams with CrewAI Flows
✅ Implement event-driven orchestration
✅ Add state persistence
✅ Enable conditional routing

## Architecture

```python
@persist  # Auto-save state
class GearCollectionFlow(Flow[GearCollectionState]):

    @start()
    def discover_gear(self):
        """Gear-heads scan sources in parallel"""
        return GearHeadsCrew().kickoff()

    @listen(discover_gear)
    def filter_new_discoveries(self, discoveries):
        """Remove already-processed items"""
        new_items = [
            d for d in discoveries
            if d['id'] not in self.state.visited_sources
        ]
        self.state.visited_sources.update(d['id'] for d in new_items)
        return new_items

    @router(filter_new_discoveries)
    def route_by_volume(self, items):
        """Route based on discovery count"""
        if len(items) > 50:
            return "batch_process"
        elif len(items) > 0:
            return "normal_process"
        return "idle"

    @listen("normal_process")
    def curate_discoveries(self, items):
        """Curators verify and research"""
        return CuratorsCrew().kickoff(inputs={"discoveries": items})

    @listen("batch_process")
    def batch_curate(self, items):
        """Split large batches across multiple curators"""
        batches = split_into_batches(items, size=10)
        results = []
        for batch in batches:
            result = CuratorsCrew().kickoff(inputs={"discoveries": batch})
            results.append(result)
        return aggregate_results(results)

    @listen(and_(curate_discoveries, batch_curate))
    def load_to_graph(self, curated_data):
        """Graph Architects safely load data"""
        result = GraphArchitectsCrew().kickoff(inputs={"data": curated_data})
        self.state.graph_nodes_created += result['nodes_created']
        self.state.graph_relationships_created += result['relationships_created']
        return result

    @listen(load_to_graph)
    def monitor_health(self, load_result):
        """Check graph health and report"""
        health_report = check_graph_health()
        if health_report['orphaned_nodes'] > 0:
            fix_orphans()
        return health_report
```

## Deliverables

1. **Main Flow** (`src/flows/gear_collection_flow.py`)
2. **Flow State Management** (using Phase 1 GearCollectionState)
3. **Conditional Routing** (by discovery volume, quality, etc.)
4. **State Persistence** (@persist decorator)
5. **Error Handling** (retry logic, escalation)
6. **Monitoring** (stats, alerts)

## Testing

```python
def test_flow_end_to_end():
    """Test complete flow from discovery to graph load"""
    flow = GearCollectionFlow()
    result = flow.kickoff()
    assert result.state.graph_nodes_created > 0

def test_flow_persistence():
    """Test flow can resume after interruption"""
    flow = GearCollectionFlow()
    flow.kickoff()  # Start
    # Simulate interruption
    flow2 = GearCollectionFlow()  # Resume
    assert flow2.state.visited_sources == flow.state.visited_sources
```

## Success Criteria
- [ ] Flow connects all 3 teams
- [ ] State persists across runs
- [ ] Conditional routing works
- [ ] Parallel crews execute faster than sequential
- [ ] Error handling prevents data loss

---

# Phase 6: Production Hardening (5-7 days)

## Goals
✅ Add error recovery
✅ Implement human escalation
✅ Create monitoring dashboard
✅ Optimize performance
✅ Complete documentation

## Deliverables

### 1. Error Handling

```python
# Retry logic for transient failures
@retry(max_attempts=3, backoff=exponential)
def execute_with_retry(crew, inputs):
    try:
        return crew.kickoff(inputs=inputs)
    except TemporaryError:
        log_error("Retrying after transient failure...")
        raise  # Retry
    except PermanentError as e:
        escalate_to_human(e)
        raise StopRetry  # Don't retry

# Circuit breaker for external services
circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60
)

@circuit_breaker.protect
def call_firecrawl_api(url):
    return firecrawl.extract(url)
```

### 2. Human Escalation

```python
class HumanEscalationTool(BaseTool):
    """Escalate issues to human operators"""

    def _run(self, issue_type: str, details: Dict, priority: str) -> str:
        # Log to database
        escalation_db.log(issue_type, details, priority)

        # Send Slack notification
        slack.send_message(
            channel="#gear-crew-alerts",
            message=f"🚨 {priority} escalation: {issue_type}\n{details}"
        )

        # Wait for human response if CRITICAL
        if priority == "CRITICAL":
            return wait_for_human_approval()

        return "Escalated successfully"

# Use in agents
curators_manager = Agent(
    ...,
    tools=[..., human_escalation_tool],
    backstory="""...
    ESCALATE TO HUMAN when:
    - Data quality < 70%
    - Conflicting sources with no resolution
    - Suspicious/spam content detected
    - Critical errors during research
    """
)
```

### 3. Monitoring Dashboard

```python
# Real-time metrics
class GearCrewMonitor:
    def __init__(self):
        self.metrics = {
            'discoveries_per_hour': Counter(),
            'research_duration': Histogram(),
            'graph_updates_per_hour': Counter(),
            'error_rate': Gauge(),
            'queue_depth': Gauge()
        }

    def track_discovery(self, discovery):
        self.metrics['discoveries_per_hour'].inc()

    def track_research(self, duration):
        self.metrics['research_duration'].observe(duration)

    def get_dashboard_data(self):
        return {
            'discoveries_today': self.state.discoveries_today,
            'verifications_today': self.state.verifications_today,
            'graph_nodes_created': self.state.graph_nodes_created,
            'avg_quality_score': mean(self.state.quality_scores),
            'error_rate': self.metrics['error_rate'].value,
            'queue_depth': discovery_queue.count()
        }
```

### 4. Performance Optimization

```python
# Parallel crew execution
async def run_teams_in_parallel():
    results = await asyncio.gather(
        gear_heads_crew.kickoff_async(),
        curators_crew.kickoff_async(),
        graph_crew.kickoff_async(),
        return_exceptions=True  # Don't fail all if one fails
    )
    return results

# Caching for expensive operations
@lru_cache(maxsize=1000)
def check_graph_for_product(product_name):
    return find_similar_nodes(product_name)

# Batch processing for efficiency
def process_discoveries_in_batches(discoveries, batch_size=10):
    for batch in chunks(discoveries, batch_size):
        process_batch(batch)
```

### 5. Complete Documentation

- [ ] API documentation (all tools, agents, crews)
- [ ] Architecture diagrams (updated with all teams)
- [ ] Deployment guide (Docker, environment setup)
- [ ] Operations manual (monitoring, troubleshooting)
- [ ] User guide (how to run, interpret results)

## Success Criteria
- [ ] Error rate < 5%
- [ ] Human escalations < 10% of discoveries
- [ ] Monitoring dashboard deployed and accessible
- [ ] Performance: 100+ discoveries/hour
- [ ] Documentation complete and reviewed
- [ ] Production deployment successful

---

## Summary: Complete System

After all 6 phases, you'll have:

```
GearCollectionFlow (orchestrator)
    ├── Gear-heads Crew (4 parallel scanners)
    │   └── Outputs: Discoveries → Queue
    ├── Curators Crew (4 research agents)
    │   └── Outputs: Verified data → Cypher code
    ├── Graph Architects Crew (3 safety agents)
    │   └── Outputs: Safe graph updates
    └── Monitoring (health checks, alerts)

Shared Infrastructure:
    ├── Source Registry (SQLite)
    ├── Discovery Queue (SQLite)
    ├── Research Log (SQLite)
    ├── GearGraph (Memgraph)
    └── Flow State (persisted)
```

**Capabilities**:
- ✅ Continuous autonomous scanning (YouTube, websites, blogs, Reddit)
- ✅ Automatic verification against existing data
- ✅ Autonomous research from authoritative sources
- ✅ Quality validation (85%+ completeness requirement)
- ✅ Source citation and audit trails
- ✅ Safe graph updates with integrity checks
- ✅ Error recovery and human escalation
- ✅ Real-time monitoring and metrics
- ✅ Production-ready performance

**Metrics**:
- Discovery rate: 100+ items/hour
- Research quality: 95%+ completeness average
- Error rate: <5%
- Graph integrity: 100% (no orphans)
- Human intervention: <10% of discoveries

---

## Getting Started

1. **Now**: Start with Phase 1 (Foundation) - see `docs/implementation_plans/phase_1_foundation.md`
2. **Next**: Review and execute each phase sequentially
3. **Testing**: Run tests after each phase before proceeding
4. **Iteration**: Refine based on real-world results

**Questions?** Refer to:
- Architecture: `docs/multi_team_architecture.md`
- Research: `docs/crewai_research_findings.md`
- Phase 1 Details: `docs/implementation_plans/phase_1_foundation.md`
