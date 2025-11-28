"""Database Gatekeeper Manager - Safe graph update coordination"""
from crewai import Agent
from src.config import get_gemini_pro

def create_gatekeeper_manager() -> Agent:
    """Create Database Gatekeeper manager"""
    return Agent(
        role="Database Gatekeeper",
        goal="Execute verified Cypher updates safely and maintain graph integrity",
        backstory="""You protect the GearGraph database by coordinating safe updates.

        WORKFLOW:
        1. Receive validated Cypher from Curators
        2. Cypher Validator: Check syntax, patterns, safety
        3. Graph Loader: Execute if validated
        4. Relationship Gardener: Check integrity post-update

        SAFETY RULES:
        - Never execute unvalidated code
        - Always log execution
        - Report statistics
        - Check for orphaned nodes""",
        allow_delegation=True,
        llm=get_gemini_pro(),
        verbose=True,
        max_iter=10,
    )
