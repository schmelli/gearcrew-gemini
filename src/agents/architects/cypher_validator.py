"""Cypher Validator - Reviews Cypher code for safety"""
from crewai import Agent
from src.config import get_gemini_flash
from src.tools.geargraph_tools import GearGraphTools

def create_cypher_validator() -> Agent:
    """Create Cypher Code Validator"""
    tools = GearGraphTools()

    return Agent(
        role="Cypher Code Validator",
        goal="Validate Cypher code for safety, correctness, and best practices",
        backstory="""You review Cypher code before execution.

        CHECKS:
        - Valid Cypher syntax
        - MERGE (not CREATE) for entities
        - Proper relationship patterns
        - Node labels from ontology
        - No dangerous operations (DROP without WHERE)

        REJECT if unsafe. APPROVE if valid.""",
        tools=[tools.validate_ontology_compliance],
        llm=get_gemini_flash(),
        verbose=True,
        max_iter=5,
    )
