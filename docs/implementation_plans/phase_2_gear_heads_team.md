# Phase 2: Gear-heads Team - Detailed Implementation Plan

**Duration**: 5-7 days
**Goal**: Build the discovery team with hierarchical manager and parallel scanner agents
**Prerequisites**: Phase 1 complete (foundation tools working)

## Overview

The Gear-heads team continuously scans web sources for gear-related content. This phase implements:
- Manager agent (Discovery Coordinator)
- 4 specialized scanner agents (YouTube, Website, Blog, Reddit)
- Hierarchical crew structure
- Async parallel scanning
- Integration with Phase 1 tools

## File Structure

```
gearcrew-gemini/
├── src/
│   ├── crews/
│   │   ├── __init__.py                    # NEW
│   │   └── gear_heads_crew.py             # NEW: Main crew definition
│   ├── agents/
│   │   ├── __init__.py                    # NEW
│   │   ├── discovery_manager.py           # NEW: Manager agent
│   │   └── scanners/
│   │       ├── __init__.py                # NEW
│   │       ├── youtube_scanner.py         # NEW
│   │       ├── website_scanner.py         # NEW
│   │       ├── blog_scanner.py            # NEW
│   │       └── reddit_scanner.py          # NEW
│   └── tasks/
│       ├── __init__.py                    # NEW
│       └── discovery_tasks.py             # NEW: Task definitions
└── tests/
    └── test_gear_heads_crew.py            # NEW