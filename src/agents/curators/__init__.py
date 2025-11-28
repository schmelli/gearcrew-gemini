"""
Curator agents for the data verification and research team
"""
from .graph_verifier import create_graph_verifier
from .autonomous_researcher import create_autonomous_researcher
from .data_validator import create_data_validator
from .source_citation_agent import create_citation_agent

def create_curator_agents():
    """Create all curator agents"""
    return [
        create_graph_verifier(),
        create_autonomous_researcher(),
        create_data_validator(),
        create_citation_agent(),
    ]

__all__ = [
    'create_graph_verifier',
    'create_autonomous_researcher',
    'create_data_validator',
    'create_citation_agent',
    'create_curator_agents',
]
