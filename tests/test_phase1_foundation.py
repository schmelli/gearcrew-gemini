"""
Comprehensive tests for Phase 1 Foundation
Tests all data models and tools
"""
import os
import sys
import tempfile
import pytest
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import models
from src.models.flow_state import GearCollectionState, TeamMetrics
from src.models.discovery import Discovery, DiscoveryType, SourceType, ProductDiscovery, InsightDiscovery
from src.models.research import ResearchLog, ResearchSource, ConfidenceLevel
from src.models.research import SourceType as ResearchSourceType

# Import tools
from src.tools.source_registry_tool import SourceRegistryTool
from src.tools.discovery_queue_tool import DiscoveryQueueTool
from src.tools.research_log_tool import ResearchLogTool


# ============================================================================
# DATA MODEL TESTS
# ============================================================================

def test_gear_collection_state():
    """Test GearCollectionState initialization and updates"""
    state = GearCollectionState()

    # Test initial state
    assert len(state.visited_sources) == 0
    assert state.discoveries_today == 0
    assert state.quality_threshold == 0.95
    assert state.max_parallel_scans == 4

    # Test state updates
    state.visited_sources.add("https://example.com/video1")
    state.visited_sources.add("https://example.com/video2")
    state.discoveries_today += 5
    state.graph_nodes_created += 10

    assert len(state.visited_sources) == 2
    assert state.discoveries_today == 5
    assert state.graph_nodes_created == 10


def test_team_metrics():
    """Test TeamMetrics model"""
    metrics = TeamMetrics(team_name="Gear-heads")
    assert metrics.team_name == "Gear-heads"
    assert metrics.tasks_completed == 0

    metrics.tasks_completed = 10
    metrics.tasks_failed = 2
    assert metrics.tasks_completed == 10
    assert metrics.tasks_failed == 2


def test_discovery_model():
    """Test Discovery base model"""
    discovery = Discovery(
        discovery_id="test-001",
        discovery_type=DiscoveryType.PRODUCT,
        name="Test Tent",
        context="Found in a YouTube review video",
        source_url="https://youtube.com/watch?v=test123",
        source_type=SourceType.YOUTUBE,
        discovered_by="youtube_scanner"
    )

    assert discovery.discovery_id == "test-001"
    assert discovery.discovery_type == DiscoveryType.PRODUCT
    assert discovery.name == "Test Tent"
    assert discovery.status == "pending"
    assert discovery.confidence == 0.5
    assert discovery.priority == 5
    assert discovery.needs_research == True


def test_product_discovery():
    """Test ProductDiscovery specialized model"""
    product = ProductDiscovery(
        discovery_id="prod-001",
        name="X-Mid 2P",
        brand="Durston Gear",
        context="Ultralight tent review comparing to competitors",
        source_url="https://youtube.com/watch?v=test456",
        source_type=SourceType.YOUTUBE,
        discovered_by="youtube_scanner",
        estimated_weight="28oz",
        product_family="X-Mid"
    )

    assert product.discovery_type == DiscoveryType.PRODUCT
    assert product.brand == "Durston Gear"
    assert product.product_family == "X-Mid"
    assert product.estimated_weight == "28oz"


def test_insight_discovery():
    """Test InsightDiscovery specialized model"""
    insight = InsightDiscovery(
        discovery_id="insight-001",
        name="Pitch fly first in rain",
        summary="Pitch fly first in rain",
        context="Reviewer mentioned this tip in setup demo",
        source_url="https://youtube.com/watch?v=test789",
        source_type=SourceType.YOUTUBE,
        discovered_by="youtube_scanner",
        related_products=["X-Mid 2P", "X-Mid 1P"]
    )

    assert insight.discovery_type == DiscoveryType.INSIGHT
    assert insight.summary == "Pitch fly first in rain"
    assert len(insight.related_products) == 2


def test_research_source():
    """Test ResearchSource model"""
    source = ResearchSource(
        url="https://durstongear.com/products/x-mid-2p",
        source_type=ResearchSourceType.MANUFACTURER,
        data_found=["weight", "price", "materials", "dimensions"],
        confidence=ConfidenceLevel.VERIFIED,
        notes="Official manufacturer product page"
    )

    assert source.source_type == ResearchSourceType.MANUFACTURER
    assert len(source.data_found) == 4
    assert source.confidence == ConfidenceLevel.VERIFIED
    assert "Official" in source.notes


def test_research_log():
    """Test ResearchLog model"""
    log = ResearchLog(
        discovery_id="disc-001",
        research_id="res-001",
        overall_confidence=ConfidenceLevel.VERIFIED,
        completeness_score=0.95,
        researched_by="autonomous_researcher"
    )

    assert log.discovery_id == "disc-001"
    assert log.completeness_score == 0.95
    assert log.overall_confidence == ConfidenceLevel.VERIFIED
    assert log.ready_for_load == False

    # Test adding sources
    log.sources.append(ResearchSource(
        url="https://example.com/product",
        source_type=ResearchSourceType.MANUFACTURER,
        data_found=["weight", "price"],
        confidence=ConfidenceLevel.VERIFIED
    ))

    assert len(log.sources) == 1


# ============================================================================
# TOOL TESTS
# ============================================================================

@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        yield tmp.name
    # Cleanup
    if os.path.exists(tmp.name):
        os.remove(tmp.name)


def test_source_registry_tool(temp_db):
    """Test Source Registry Tool - all actions"""
    tool = SourceRegistryTool(db_path=temp_db)

    # Test check on new URL
    result = tool._run(action="check", url="https://youtube.com/watch?v=test123")
    assert "NEW" in result
    assert "test123" in result

    # Test add
    result = tool._run(
        action="add",
        url="https://youtube.com/watch?v=test123",
        source_type="youtube",
        items_found=5
    )
    assert "REGISTERED" in result or "UPDATED" in result
    assert "5" in result

    # Test check on existing URL
    result = tool._run(action="check", url="https://youtube.com/watch?v=test123")
    assert "VISITED" in result
    assert "5" in result  # Items found

    # Test add again (update)
    result = tool._run(
        action="add",
        url="https://youtube.com/watch?v=test123",
        source_type="youtube",
        items_found=3
    )
    assert "UPDATED" in result or "scan #2" in result

    # Test list
    result = tool._run(action="list")
    assert "youtube" in result
    assert "test123" in result

    # Test stats
    result = tool._run(action="stats")
    assert "Total sources" in result
    assert "youtube" in result


def test_discovery_queue_tool(temp_db):
    """Test Discovery Queue Tool - all actions"""
    tool = DiscoveryQueueTool(db_path=temp_db)

    # Test enqueue
    discovery_data = {
        "discovery_id": "disc-001",
        "discovery_type": "product",
        "name": "Test Tent",
        "brand": "Test Brand"
    }
    result = tool._run(action="enqueue", discovery_data=discovery_data, priority=8)
    assert "ENQUEUED" in result
    assert "disc-001" in result

    # Test duplicate enqueue
    result = tool._run(action="enqueue", discovery_data=discovery_data, priority=8)
    assert "DUPLICATE" in result

    # Test peek
    result = tool._run(action="peek")
    assert "disc-001" in result
    assert "priority=8" in result

    # Test status
    result = tool._run(action="status")
    assert "pending" in result
    assert "1 items" in result

    # Test dequeue
    result = tool._run(action="dequeue")
    assert "DEQUEUED" in result
    assert "disc-001" in result

    # Test peek after dequeue (should be empty)
    result = tool._run(action="peek")
    assert "EMPTY" in result

    # Test update
    result = tool._run(action="update", discovery_id="disc-001", new_status="verified")
    assert "UPDATED" in result


def test_research_log_tool(temp_db):
    """Test Research Log Tool - all actions"""
    tool = ResearchLogTool(db_path=temp_db)

    # Test log
    result = tool._run(
        action="log",
        research_id="res-001",
        discovery_id="disc-001",
        source_url="https://durstongear.com/products/x-mid-2p",
        source_type="manufacturer",
        data_found=["weight", "price", "materials", "dimensions"],
        confidence="verified",
        notes="Official product page"
    )
    assert "LOGGED" in result
    assert "4 fields" in result
    assert "verified" in result

    # Log another step
    result = tool._run(
        action="log",
        research_id="res-001",
        discovery_id="disc-001",
        source_url="https://outdoorgearlab.com/reviews/x-mid-2p",
        source_type="review_site",
        data_found=["real_world_weight", "user_feedback"],
        confidence="corroborated"
    )
    assert "LOGGED" in result

    # Test retrieve
    result = tool._run(action="retrieve", discovery_id="disc-001")
    assert "res-001" in result
    assert "manufacturer" in result
    assert "review_site" in result

    # Test complete
    result = tool._run(action="complete", research_id="res-001")
    assert "COMPLETED" in result
    assert "Completeness" in result
    assert "Confidence" in result

    # Test validate
    result = tool._run(action="validate", research_id="res-001")
    # May be VALID or INVALID depending on completeness
    assert "Research res-001" in result


def test_discovery_queue_priority():
    """Test Discovery Queue priority ordering"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        tool = DiscoveryQueueTool(db_path=db_path)

        # Add discoveries with different priorities
        for i, priority in enumerate([3, 8, 5, 10, 1]):
            discovery = {
                "discovery_id": f"disc-{i:03d}",
                "discovery_type": "product",
                "name": f"Product {i}"
            }
            tool._run(action="enqueue", discovery_data=discovery, priority=priority)

        # Peek should show highest priority first
        result = tool._run(action="peek")
        assert "disc-003" in result  # Priority 10 should be first

        # Dequeue should get priority 10
        result = tool._run(action="dequeue")
        assert "disc-003" in result
        assert "Priority: 10" in result

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("Running Phase 1 Foundation Tests")
    print("="*70)

    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])
