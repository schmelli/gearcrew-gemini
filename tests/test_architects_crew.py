"""Tests for Graph Architects Crew - Phase 4"""
import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    from src.agents.gatekeeper_manager import create_gatekeeper_manager
    from src.agents.architects import create_architect_agents
    from src.crews.architects_crew import ArchitectsCrew

def test_manager_creation():
    from src.agents.gatekeeper_manager import create_gatekeeper_manager
    manager = create_gatekeeper_manager()
    assert manager.role == "Database Gatekeeper"
    assert manager.allow_delegation == True

def test_architect_agents():
    from src.agents.architects import create_architect_agents
    architects = create_architect_agents()
    assert len(architects) == 2

def test_crew_init():
    from src.crews.architects_crew import ArchitectsCrew
    crew = ArchitectsCrew()
    assert crew.manager is not None
    assert len(crew.tasks) == 2

def test_crew_creation():
    from src.crews.architects_crew import ArchitectsCrew
    from crewai import Crew
    crew = ArchitectsCrew()
    c = crew.crew()
    assert isinstance(c, Crew)
    assert len(c.agents) == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
