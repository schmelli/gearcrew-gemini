# Multi-Team Gear Collection Architecture

**Project**: GearCrew-Gemini Async Hierarchical System
**Design Date**: 2025-11-28
**Status**: Design Phase

## Vision

Build an autonomous, multi-team agent system that continuously discovers and curates outdoor gear knowledge into the GearGraph database with minimal human intervention.

## Team Structure

### Team 1: "Gear-heads" (Discovery Team)

**Mission**: Continuously scan the web for gear-related content like experienced REI/Globetrotter sales staff obsessed with outdoor equipment.

**Team Composition**:
- **Manager**: Discovery Coordinator
- **Workers**:
  - YouTube Scanner (video reviews, gear demos)
  - Website Scanner (manufacturer sites, product pages)
  - Blog Scanner (outdoor blogs, review sites)
  - Reddit/Forum Scanner (r/Ultralight, r/CampingGear discussions)

**Responsibilities**:
1. Scan assigned sources continuously
2. Extract gear mentions (brands, products, insights)
3. Capture metadata (source URL, date, context)
4. Handoff discoveries to Curators team
5. Track visited sources (avoid duplication)

**Key Behavior**: Like a gear-obsessed enthusiast who can't stop browsing gear content, constantly finding new products and sharing discoveries with colleagues.

### Team 2: "Curators" (Verification & Research Team)

**Mission**: Verify discoveries against GearGraph, autonomously research missing data, and prepare high-quality updates.

**Team Composition**:
- **Manager**: Data Verification Coordinator
- **Workers**:
  - Graph Verifier (checks what exists in GearGraph)
  - Autonomous Researcher (fills missing data from authoritative sources)
  - Data Validator (ensures quality and completeness)
  - Source Citation Agent (maintains research documentation)

**Responsibilities**:
1. Receive discoveries from Gear-heads
2. Query GearGraph to check existing data
3. Identify gaps (missing brands, incomplete products, new insights)
4. Autonomously research missing information:
   - Manufacturer websites for official specs
   - Review sites for real-world data
   - Multiple sources for verification
5. Document all sources and research steps
6. Prepare verified Cypher code for graph updates

**Key Behavior**: Like meticulous librarians who verify every fact, cross-reference sources, and maintain impeccable documentation.

### Team 3: "Graph Architects" (Database Team)

**Mission**: Execute verified graph updates safely and maintain database integrity.

**Team Composition**:
- **Manager**: Database Gatekeeper
- **Workers**:
  - Cypher Validator (reviews generated code)
  - Graph Loader (executes updates)
  - Relationship Gardener (maintains connections, finds orphans)

**Responsibilities**:
1. Validate Cypher code from Curators
2. Execute approved updates
3. Verify node creation and relationships
4. Monitor for orphaned nodes
5. Suggest connection improvements

## System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    GearCollectionFlow                           │
│              (Master Orchestrator with State)                   │
└───────┬──────────────┬────────────────┬────────────┬────────────┘
        │              │                │            │
    [START]       [LISTEN]          [LISTEN]     [LISTEN]
        │              │                │            │
   ┌────▼──────┐  ┌───▼──────┐   ┌────▼─────┐  ┌──▼───────┐
   │ Gear-heads│  │ Curators │   │  Graph   │  │  Monitor │
   │   Crew    │  │   Crew   │   │Architects│  │   Crew   │
   │           │  │          │   │   Crew   │  │          │
   │[Parallel] │  │[Parallel]│   │[Sequential│  │[Periodic]│
   │ Scanners  │  │Researchers│   │  Load]   │  │  Health  │
   └───────────┘  └──────────┘   └──────────┘  └──────────┘
        │              │                │
        │              │                │
   ┌────▼──────────────▼────────────────▼────┐
   │         Shared Services                 │
   ├─────────────────────────────────────────┤
   │ • Source Registry (visited URLs)        │
   │ • Discovery Queue (pending items)       │
   │ • Research Log (source citations)       │
   │ • GearGraph Tools (find/execute)        │
   │ • Firecrawl Tools (extract/scrape)      │
   │ • Web Search                            │
   └─────────────────────────────────────────┘
```

## Detailed Workflow

### 1. Discovery Phase (Gear-heads Crew)

**Manager Decision Logic**:
```python
"""You delegate scanning tasks based on source type:
1. If YouTube URLs detected → assign to YouTube Scanner
2. If manufacturer domains detected → assign to Website Scanner
3. If blog/review site → assign to Blog Scanner
4. If Reddit/forum → assign to Forum Scanner

For each discovery, ensure:
- Complete metadata captured (URL, title, date, context)
- Source registered in registry to avoid re-scanning
- Valid brand/product names extracted
- Sufficient context for Curators to verify

Handoff to Curators only when discoveries are complete and documented."""
```

**Parallel Async Tasks**:
- YouTube Scanner: Scans new gear review videos
- Website Scanner: Checks manufacturer product pages
- Blog Scanner: Reads outdoor gear blogs and reviews
- Reddit Scanner: Monitors r/Ultralight, r/CampingGear

**Output Format**:
```json
{
  "discoveries": [
    {
      "type": "brand",
      "name": "Durston Gear",
      "source_url": "https://youtube.com/watch?v=...",
      "source_type": "youtube",
      "context": "Mentioned in review of 2025 ultralight tents",
      "discovered_at": "2025-11-28T10:30:00Z"
    },
    {
      "type": "product",
      "brand": "Durston Gear",
      "product_name": "X-Mid Pro 2",
      "partial_specs": {
        "weight": "mentioned as '28oz'",
        "type": "tent"
      },
      "source_url": "https://youtube.com/watch?v=...",
      "source_type": "youtube",
      "context": "Detailed review comparing to competitors",
      "discovered_at": "2025-11-28T10:30:00Z"
    },
    {
      "type": "insight",
      "summary": "Pitch inner first for better ventilation",
      "content": "Reviewer recommends pitching the inner tent first in humid conditions...",
      "related_products": ["X-Mid Pro 2"],
      "source_url": "https://youtube.com/watch?v=...",
      "discovered_at": "2025-11-28T10:30:00Z"
    }
  ]
}
```

### 2. Verification & Research Phase (Curators Crew)

**Manager Decision Logic**:
```python
"""For each discovery from Gear-heads:
1. Assign to Graph Verifier: Check if brand/product exists in GearGraph
   - If complete → mark as 'verified', skip research
   - If missing/incomplete → proceed to step 2

2. Assign to Autonomous Researcher: Gather missing data
   - For brands: official website, description, founding year
   - For products: weight, price, materials, specs, official URL, images
   - For insights: verify accuracy, find additional context

   Research priority:
   a) Manufacturer website (highest authority)
   b) Authorized retailers (REI, Backcountry, etc.)
   c) Reputable review sites (OutdoorGearLab, Section Hiker)

   CRITICAL: Document every source. Use Firecrawl Extract for structured data.

3. Assign to Data Validator: Ensure completeness
   - All required fields present
   - Units standardized (grams, ounces, USD)
   - URLs valid and direct
   - No contradictions between sources

4. Assign to Source Citation Agent: Create research log
   - List all sources consulted
   - Note any conflicts found
   - Document confidence level (verified vs. reported)

Handoff to Graph Architects only when data is complete and verified."""
```

**Parallel Research Tasks** (for each discovery):
- Graph Verifier: Queries GearGraph for existing data
- Autonomous Researcher: Searches authoritative sources
- Data Validator: Checks completeness and consistency
- Citation Agent: Documents research trail

**Output Format**:
```json
{
  "verified_data": [
    {
      "entity_type": "Product",
      "brand": "Durston Gear",
      "product_name": "X-Mid Pro 2",
      "verified_specs": {
        "weightGrams": 794,
        "weightOunces": 28,
        "priceUSD": 379.00,
        "capacity": "2 Person",
        "type": "Tent",
        "material": "20D silnylon",
        "productUrl": "https://durstongear.com/products/x-mid-pro-2",
        "imageUrl": "https://durstongear.com/.../x-mid-pro-2.jpg"
      },
      "research_log": {
        "sources": [
          {
            "url": "https://durstongear.com/products/x-mid-pro-2",
            "type": "manufacturer",
            "data_found": ["weight", "price", "materials", "images"],
            "confidence": "verified"
          },
          {
            "url": "https://www.outdoorgearlab.com/reviews/x-mid-pro-2",
            "type": "review",
            "data_found": ["real_world_weight", "user_feedback"],
            "confidence": "corroborated"
          }
        ],
        "verified_at": "2025-11-28T11:15:00Z",
        "verified_by": "Autonomous Researcher + Data Validator"
      },
      "cypher_code": "MERGE (brand:Brand {name: 'Durston Gear'})\\nMERGE (family:ProductFamily {name: 'X-Mid Pro'})\\nMERGE (item:GearItem {name: 'X-Mid Pro 2'})\\n  SET item.weightGrams = 794,\\n      item.weightOunces = 28,\\n      item.priceUSD = 379.00,\\n      item.capacity = '2 Person',\\n      item.type = 'Tent',\\n      item.material = '20D silnylon',\\n      item.productUrl = 'https://durstongear.com/products/x-mid-pro-2',\\n      item.imageUrl = 'https://durstongear.com/.../x-mid-pro-2.jpg'\\nMERGE (brand)-[:MANUFACTURES]->(family)\\nMERGE (item)-[:IS_VARIANT_OF]->(family)"
    }
  ]
}
```

### 3. Graph Update Phase (Graph Architects Crew)

**Manager Decision Logic**:
```python
"""Execute verified updates safely:
1. Assign to Cypher Validator: Review generated code
   - Check for syntax errors
   - Verify MERGE usage (not CREATE for duplicates)
   - Ensure relationship patterns correct
   - Validate property types

2. Assign to Graph Loader: Execute approved code
   - Run Cypher query via ExecuteCypherTool
   - Log execution with reason
   - Capture any errors

3. Assign to Relationship Gardener: Post-update health check
   - Check for orphaned Insight nodes
   - Verify all relationships created
   - Suggest improvements (e.g., connect related products)

Report statistics: nodes created, relationships added, errors encountered."""
```

### 4. Monitoring Phase (Periodic Health Checks)

**Continuous Monitoring Tasks**:
- Check for orphaned nodes
- Verify relationship integrity
- Track discovery rate (items/hour)
- Monitor error rates
- Alert on anomalies

## State Management

### Flow State Schema

```python
from pydantic import BaseModel
from typing import Set, List, Dict
from datetime import datetime

class GearCollectionState(BaseModel):
    # Source tracking
    visited_sources: Set[str] = set()
    last_scan_time: Dict[str, datetime] = {}

    # Discovery tracking
    pending_discoveries: List[Dict] = []
    verified_items: List[Dict] = []

    # Research tracking
    research_in_progress: Dict[str, str] = {}  # item_id -> researcher_agent
    research_completed: Set[str] = set()

    # Graph tracking
    graph_updates_pending: List[Dict] = []
    graph_nodes_created: int = 0
    graph_relationships_created: int = 0

    # Quality metrics
    errors_encountered: List[Dict] = []
    discoveries_today: int = 0
    verifications_today: int = 0

    # Configuration
    max_parallel_scans: int = 4
    max_parallel_research: int = 3
    quality_threshold: float = 0.95  # Require 95% data completeness
```

### Shared Tools

**1. Source Registry Tool**
```python
class SourceRegistryTool(BaseTool):
    """Track visited sources in SQLite database"""
    # check: Is this URL already visited?
    # add: Mark URL as visited
    # list: Show recent sources
```

**2. Discovery Queue Tool**
```python
class DiscoveryQueueTool(BaseTool):
    """Manage pending discoveries"""
    # enqueue: Add discovery to queue
    # dequeue: Get next discovery for curation
    # peek: View queue status without removing
```

**3. Research Log Tool**
```python
class ResearchLogTool(BaseTool):
    """Document all research steps and sources"""
    # log: Record research step with source citation
    # retrieve: Get research history for an item
    # validate: Check if research meets quality standards
```

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Create docs/ directory structure
- [ ] Implement SourceRegistryTool with SQLite backend
- [ ] Implement DiscoveryQueueTool
- [ ] Implement ResearchLogTool
- [ ] Create GearCollectionState Pydantic model
- [ ] Set up basic Flow structure

### Phase 2: Gear-heads Team (Week 2)
- [ ] Create Gear-heads manager agent
- [ ] Implement YouTube Scanner agent
- [ ] Implement Website Scanner agent
- [ ] Implement Blog Scanner agent
- [ ] Implement Reddit Scanner agent
- [ ] Configure hierarchical crew with async tasks
- [ ] Test parallel scanning

### Phase 3: Curators Team (Week 3)
- [ ] Create Curators manager agent
- [ ] Implement Graph Verifier agent
- [ ] Implement Autonomous Researcher agent
- [ ] Implement Data Validator agent
- [ ] Implement Source Citation agent
- [ ] Configure hierarchical crew
- [ ] Test verification workflow

### Phase 4: Graph Architects Team (Week 4)
- [ ] Create Graph Architects manager agent
- [ ] Implement Cypher Validator agent
- [ ] Implement Graph Loader agent (reuse existing)
- [ ] Implement Relationship Gardener agent
- [ ] Configure crew
- [ ] Test graph update workflow

### Phase 5: Flow Integration (Week 5)
- [ ] Connect Gear-heads → Curators via Flow
- [ ] Connect Curators → Graph Architects
- [ ] Implement state persistence
- [ ] Add conditional routing (e.g., skip research if complete)
- [ ] Test end-to-end flow

### Phase 6: Production Hardening (Week 6)
- [ ] Add error handling and recovery
- [ ] Implement human escalation triggers
- [ ] Add monitoring dashboard
- [ ] Performance optimization
- [ ] Documentation

## Success Metrics

- **Discovery Rate**: Items discovered per hour
- **Verification Rate**: % of discoveries successfully verified
- **Data Completeness**: Average % of required fields populated
- **Source Diversity**: Number of unique sources used
- **Research Efficiency**: Time from discovery to graph update
- **Error Rate**: Failed updates / total updates
- **Human Interventions**: Escalations requiring human review

## Next Steps

1. ✅ Research completed
2. 🔄 Architecture design (current)
3. ⏭️ Implement foundation (Phase 1)
4. ⏭️ Build Gear-heads team (Phase 2)
5. ⏭️ Build Curators team (Phase 3)
