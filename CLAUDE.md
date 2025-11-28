# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GearGraph is an AI-powered outdoor gear research system that extracts, verifies, and stores hiking gear information into a Memgraph knowledge graph database. The system uses CrewAI agents with Google's Gemini models to process gear reviews, verify data against the web, and maintain a structured ontology-compliant graph database.

## Core Architecture

### Multi-Agent System (CrewAI)

The project implements three distinct agent workflows:

**Research Agents** (`create_research_agents()` in `src/agents.py`):
1. **Profiler** (Context Analyst) - Fast Gemini model - Analyzes source reliability, identifies potential transcription errors
2. **Detective** (Gear Detective) - Pro Gemini model - Extracts entities, queries graph for duplicates, verifies via web search, enriches missing specifications
3. **Hunter** (Wisdom Hunter) - Pro Gemini model - Extracts maintenance tips, usage tricks, and practical knowledge
4. **Architect** (Ontology Architect) - Pro Gemini model - Transforms verified facts into valid Cypher MERGE statements using UNWIND for batch operations

**Operations Agents** (`create_ops_agents()` in `src/agents.py`):
5. **Gatekeeper** (Database Gatekeeper) - Executes approved Cypher with audit logging
6. **Gardener** (Graph Gardener) - Post-import analysis, finds orphans, suggests connections

**Completion Agent** (`create_completion_agent()` in `src/agents.py`):
7. **Data Completer** (Data Completion Specialist) - Pro Gemini model - Finds products with missing information (weight, URLs, images), researches via web/Firecrawl, updates graph with complete data

### Two Execution Modes

1. **CLI Mode** (`main.py`): Terminal-based sequential workflow for text input
2. **Streamlit UI** (`app.py`): Web-based 5-step wizard with review/refinement capabilities

### Data Flow Pattern

```
User Input → Profiler (context) → Detective (entities) + Hunter (insights)
→ User Review/Refinement → Architect (Cypher plan) → Gatekeeper (execution)
→ Gardener (validation) → [OPTIONAL] Data Completer (fill missing data)
```

**Critical Design Patterns:**
- Detective MUST use graph lookup before web search to prevent duplicates
- Architect uses UNWIND for batch operations (never individual MERGEs)
- Cypher map literals use unquoted keys: `[{name: "Tent"}]` NOT `[{"name": "Tent"}]`
- ProductFamily (series) vs GearItem (variant) separation: common specs → Family, specific specs → Item

## Database Architecture

**Technology:** Memgraph (Cypher graph database) with SSL/TLS encryption

**Connection:** Configured in `src/config.py` via environment variables:
- `MEMGRAPH_HOST` - Default: geargraph.gearshack.app
- `MEMGRAPH_PORT` - Default: 7687
- `MEMGRAPH_USER` - Default: memgraph
- `MEMGRAPH_PASSWORD`

**Ontology:** Defined in `geargraph_ontology.ttl` (OWL format, queried via RDFLib)

**Node Structure:**
- `:ProductFamily` - Manufacturer series (e.g., "Nallo")
- `:GearItem` - Specific variants (e.g., "Nallo 2")
- `:OutdoorBrand` - Manufacturers
- `:Insight` - Usage tips, connected via `[:HAS_TIP]` relationship

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env to add:
# - GOOGLE_API_KEY (for Gemini models)
# - SERPER_API_KEY (for web search via Serper.dev)
# - FIRECRAWL_API_KEY (for structured data extraction from websites)
# - Optional: MEMGRAPH_* variables for custom database
```

### Running the Application
```bash
# CLI Mode (sequential workflow)
python main.py

# Streamlit UI (4-step wizard)
streamlit run app.py

# Alternative: Use provided script
./run_app.sh
```

## LLM Configuration

**Models Used:**
- `gemini-2.5-pro` - For reasoning-heavy agents (Detective, Hunter, Architect)
- `gemini-2.5-flash` - For fast operations (Profiler)

**API Configuration:**
- Uses Google AI Studio API (not Vertex AI)
- Explicitly removes `GOOGLE_APPLICATION_CREDENTIALS` in `src/config.py`
- Temperature: 1.0 for all reasoning models (per Gemini documentation)

## Custom Tools (`src/tools/geargraph_tools.py`)

All tools inherit from `crewai.tools.BaseTool` and use Pydantic schemas:

1. **FindSimilarNodesTool** - Case-insensitive graph search to prevent duplicates
2. **ExecuteCypherTool** - Audit-logged query execution
3. **ValidateOntologyTool** - RDFLib-based ontology validation
4. **FirecrawlExtractTool** - LLM-powered structured data extraction from web pages with custom schemas
5. **FirecrawlScrapeTool** - Web page scraping returning clean Markdown content
6. **search_tool** - SerperDevTool wrapper for web searches

**Tool Usage Pattern:**
```python
tool_instance = GearGraphTools.find_similar_nodes
tool_firecrawl = GearGraphTools.firecrawl_extract
# Used in agent definition:
detective = Agent(..., tools=[tool_instance, tool_firecrawl], ...)
```

## Error Handling & Logging

**Audit Log:** All Cypher executions logged to `geargraph_ops.log` with timestamp, reason, and query

**Streamlit Error Handling:**
- JSON parsing in try/except blocks with fallback to raw display
- Task output handling supports both `.raw` attribute and `str()` conversion for CrewAI version compatibility

## Key Constraints

- **Performance:** ALWAYS use `UNWIND` for batch operations in Cypher
- **Syntax:** Memgraph requires unquoted keys in map literals
- **Verification:** Detective agent MUST check graph before web search
- **Ontology Compliance:** Architect can validate labels against `geargraph_ontology.ttl`
- **Duplicate Prevention:** Graph lookups are case-insensitive and bidirectional substring matches
- **Data Completion:** Optional 5th step that automatically finds and fills missing product data (weight, URLs, images)

## New Features (Latest)

### Automatic Data Completion
The system now includes an optional data completion workflow:
- **Step 5 in Streamlit UI** - Runs after graph import
- **Queries graph** for items missing weight, productUrl, or imageUrl
- **Web research** using SerperDev search to find manufacturer pages
- **Structured extraction** using Firecrawl's extract() endpoint with custom schemas
- **Automatic updates** to the graph with validated data
- **Priority:** Weight > Product URL > Image URL

### Firecrawl Integration
Two new tools for web data extraction:
- **FirecrawlExtractTool** - Uses LLM to extract structured data matching JSON schemas (ideal for manufacturer pages)
- **FirecrawlScrapeTool** - Returns clean Markdown for unstructured content (reviews, articles)

**Default Extraction Schema:**
```python
{
    "product_name": string,
    "brand": string,
    "weight_grams": number,
    "weight_ounces": number,
    "material": string,
    "price_usd": number,
    "dimensions": string,
    "product_url": string,
    "image_url": string,
    "description": string,
    "features": array of strings
}
```

## Project Files to Ignore
- `venv/` - Virtual environment
- `geargraph_ops.log` - Execution logs
- `.env` - Secrets (use `.env.example` as template)
- `geargraph-*.json` - Service account credentials (if present)
