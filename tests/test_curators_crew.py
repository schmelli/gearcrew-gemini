"""
Tests for Curators Crew - Phase 3 validation
"""
import os, sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test Phase 3 imports"""
    from src.agents.curators_manager import create_curators_manager
    from src.agents.curators import create_curator_agents
    from src.tasks.curation_tasks import create_curation_tasks
    from src.crews.curators_crew import CuratorsCrew

def test_create_curators_manager():
    """Test manager creation"""
    from src.agents.curators_manager import create_curators_manager
    manager = create_curators_manager()
    assert manager.role == "Data Verification Coordinator"
    assert manager.allow_delegation == True

def test_create_curator_agents():
    """Test curator agents"""
    from src.agents.curators import create_curator_agents
    curators = create_curator_agents()
    assert len(curators) == 4

def test_curators_crew_init():
    """Test crew initialization"""
    from src.crews.curators_crew import CuratorsCrew
    crew = CuratorsCrew()
    assert crew.manager is not None
    assert len(crew.tasks) == 4

def test_curators_crew_creation():
    """Test crew object"""
    from src.crews.curators_crew import CuratorsCrew
    from crewai import Crew, Process
    crew = CuratorsCrew()
    c = crew.crew()
    assert isinstance(c, Crew)
    assert len(c.agents) == 4
    assert c.process == Process.hierarchical

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
