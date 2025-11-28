"""Relationship Gardener - Maintains graph integrity"""
from crewai import Agent
from src.config import get_gemini_flash
from src.tools.geargraph_tools import GearGraphTools

def create_relationship_gardener() -> Agent:
    """Create Graph Integrity Specialist"""
    tools = GearGraphTools()

    return Agent(
        role="Graph Integrity Specialist",
        goal="Monitor and maintain graph relationships post-update",
        backstory="""You ensure graph health after updates.

        POST-UPDATE CHECKS:
        - Find orphaned Insight nodes
        - Verify expected relationships exist
        - Suggest improvements

        AUTO-FIX orphaned Insights by linking to products or General category.""",
        tools=[tools.execute_cypher, tools.find_similar_nodes],
        llm=get_gemini_flash(),
        verbose=True,
        max_iter=10,
    )
