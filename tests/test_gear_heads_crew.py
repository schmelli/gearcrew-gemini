"""
Tests for Gear-heads Crew - Phase 2 validation

These tests verify the structure and initialization of the
Gear-heads discovery team components.
"""
import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test imports
def test_imports():
    """Test that all Phase 2 modules can be imported"""
    # Agents
    from src.agents.discovery_manager import create_discovery_manager
    from src.agents.scanners.youtube_scanner import create_youtube_scanner
    from src.agents.scanners.website_scanner import create_website_scanner
    from src.agents.scanners.blog_scanner import create_blog_scanner
    from src.agents.scanners.reddit_scanner import create_reddit_scanner
    from src.agents.scanners import create_scanner_agents

    # Tasks
    from src.tasks.discovery_tasks import create_discovery_tasks

    # Crew
    from src.crews.gear_heads_crew import GearHeadsCrew, create_gear_heads_crew

    assert True  # If we got here, imports succeeded


def test_create_discovery_manager():
    """Test Discovery Manager agent creation"""
    from src.agents.discovery_manager import create_discovery_manager

    manager = create_discovery_manager()

    assert manager is not None
    assert manager.role == "Gear Discovery Coordinator"
    assert manager.allow_delegation == True
    assert "coordinate" in manager.goal.lower() or "coordinator" in manager.role.lower()


def test_create_scanner_agents():
    """Test scanner agent creation"""
    from src.agents.scanners import create_scanner_agents

    scanners = create_scanner_agents()

    assert len(scanners) == 4
    assert scanners[0].role == "YouTube Gear Video Scanner"
    assert scanners[1].role == "Manufacturer Website Scanner"
    assert scanners[2].role == "Outdoor Gear Blog Scanner"
    assert scanners[3].role == "Reddit/Forum Gear Scanner"


def test_youtube_scanner_has_tools():
    """Test YouTube scanner has required tools"""
    from src.agents.scanners.youtube_scanner import create_youtube_scanner

    scanner = create_youtube_scanner()

    assert scanner is not None
    assert len(scanner.tools) >= 2  # source_registry, discovery_queue at minimum
    assert scanner.role == "YouTube Gear Video Scanner"


def test_website_scanner_has_tools():
    """Test Website scanner has required tools"""
    from src.agents.scanners.website_scanner import create_website_scanner

    scanner = create_website_scanner()

    assert scanner is not None
    assert len(scanner.tools) >= 2
    assert scanner.role == "Manufacturer Website Scanner"


def test_blog_scanner_has_tools():
    """Test Blog scanner has required tools"""
    from src.agents.scanners.blog_scanner import create_blog_scanner

    scanner = create_blog_scanner()

    assert scanner is not None
    assert len(scanner.tools) >= 2
    assert scanner.role == "Outdoor Gear Blog Scanner"


def test_reddit_scanner_has_tools():
    """Test Reddit scanner has required tools"""
    from src.agents.scanners.reddit_scanner import create_reddit_scanner

    scanner = create_reddit_scanner()

    assert scanner is not None
    assert len(scanner.tools) >= 2
    assert scanner.role == "Reddit/Forum Gear Scanner"


def test_create_discovery_tasks():
    """Test discovery tasks creation"""
    from src.agents.discovery_manager import create_discovery_manager
    from src.agents.scanners import create_scanner_agents
    from src.tasks.discovery_tasks import create_discovery_tasks

    manager = create_discovery_manager()
    scanners = create_scanner_agents()

    tasks = create_discovery_tasks(
        manager=manager,
        youtube_scanner=scanners[0],
        website_scanner=scanners[1],
        blog_scanner=scanners[2],
        reddit_scanner=scanners[3]
    )

    assert len(tasks) == 5  # 4 scanner tasks + 1 aggregate task

    # First 4 should be async
    assert tasks[0].async_execution == True  # YouTube
    assert tasks[1].async_execution == True  # Website
    assert tasks[2].async_execution == True  # Blog
    assert tasks[3].async_execution == True  # Reddit

    # Last task is aggregation (not async, waits for others)
    assert tasks[4].context is not None  # Has context from other tasks
    assert len(tasks[4].context) == 4  # Depends on all 4 scanner tasks


def test_gear_heads_crew_initialization():
    """Test Gear-heads crew can be initialized"""
    from src.crews.gear_heads_crew import GearHeadsCrew

    crew_instance = GearHeadsCrew()

    assert crew_instance.manager is not None
    assert crew_instance.youtube_scanner is not None
    assert crew_instance.website_scanner is not None
    assert crew_instance.blog_scanner is not None
    assert crew_instance.reddit_scanner is not None
    assert len(crew_instance.tasks) == 5


def test_gear_heads_crew_creation():
    """Test crew object creation"""
    from src.crews.gear_heads_crew import GearHeadsCrew
    from crewai import Crew, Process

    crew_instance = GearHeadsCrew()
    crew = crew_instance.crew()

    assert isinstance(crew, Crew)
    assert len(crew.agents) == 4  # 4 scanners (manager separate in hierarchical)
    assert len(crew.tasks) == 5  # 4 scanner tasks + 1 aggregate
    assert crew.process == Process.hierarchical
    assert crew.manager_agent is not None
    assert crew.manager_agent == crew_instance.manager


def test_create_gear_heads_crew_function():
    """Test convenience function for crew creation"""
    from src.crews.gear_heads_crew import create_gear_heads_crew

    crew = create_gear_heads_crew()

    assert crew is not None
    assert hasattr(crew, 'kickoff')
    assert hasattr(crew, 'kickoff_async')


def test_crew_default_inputs():
    """Test crew default input parameters"""
    from src.crews.gear_heads_crew import GearHeadsCrew

    crew_instance = GearHeadsCrew()

    # This should not raise an error
    # Note: We won't actually execute (no API keys in test)
    assert crew_instance is not None


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("Running Phase 2: Gear-heads Crew Tests")
    print("="*70)

    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])
