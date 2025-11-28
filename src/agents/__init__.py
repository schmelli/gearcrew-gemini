"""
Agent definitions for GearCrew multi-team system
"""
from .discovery_manager import create_discovery_manager
from .scanners import create_scanner_agents

__all__ = [
    'create_discovery_manager',
    'create_scanner_agents',
]
