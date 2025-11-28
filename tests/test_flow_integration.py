"""Tests for Phase 5 - Flow Integration"""
import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_flow_imports():
    """Test flow module imports"""
    from src.flows import GearCollectionFlow, run_gear_collection
    from src.flows.gear_collection_flow import GearCollectionFlow

def test_flow_state_initialization():
    """Test flow initializes with correct state"""
    from src.flows.gear_collection_flow import GearCollectionFlow
    flow = GearCollectionFlow()
    assert flow.state is not None
    assert hasattr(flow.state, 'visited_sources')
    assert hasattr(flow.state, 'pending_discoveries')
    assert hasattr(flow.state, 'quality_threshold')

def test_flow_has_crews():
    """Test flow has all three crews"""
    from src.flows.gear_collection_flow import GearCollectionFlow
    flow = GearCollectionFlow()
    assert flow.gear_heads is not None
    assert flow.curators is not None
    assert flow.architects is not None

def test_flow_methods_exist():
    """Test flow has required step methods"""
    from src.flows.gear_collection_flow import GearCollectionFlow
    flow = GearCollectionFlow()
    assert hasattr(flow, 'discover_gear')
    assert hasattr(flow, 'filter_new_discoveries')
    assert hasattr(flow, 'route_by_volume')
    assert hasattr(flow, 'curate_discoveries')
    assert hasattr(flow, 'load_to_graph')

def test_route_by_volume_logic():
    """Test routing decisions"""
    from src.flows.gear_collection_flow import GearCollectionFlow
    flow = GearCollectionFlow()

    # Test batch routing
    result = flow.route_by_volume({"count": 100})
    assert result == "batch_process"

    # Test normal routing
    result = flow.route_by_volume({"count": 25})
    assert result == "normal_process"

    # Test idle routing
    result = flow.route_by_volume({"count": 0})
    assert result == "idle"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
