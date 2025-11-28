"""Graph Architect agents"""
from .cypher_validator import create_cypher_validator
from .relationship_gardener import create_relationship_gardener

def create_architect_agents():
    """Create architect worker agents"""
    return [
        create_cypher_validator(),
        create_relationship_gardener(),
    ]

__all__ = ['create_cypher_validator', 'create_relationship_gardener', 'create_architect_agents']
