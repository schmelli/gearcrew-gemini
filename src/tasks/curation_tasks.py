"""
Curation Tasks - Task definitions for the Curators research team
"""
from crewai import Task
from typing import List


def create_curation_tasks(manager, graph_verifier, autonomous_researcher,
                          data_validator, citation_agent) -> List[Task]:
    """
    Create all curation tasks for the Curators crew.

    Sequential tasks for verification, research, validation, and documentation.
    """

    verify_task = Task(
        description="""Check GearGraph for existing data on this discovery.

        1. Query GearGraph for brand and product
        2. Use fuzzy matching for variations
        3. Report existing data completeness
        4. Determine if NEW, INCOMPLETE, or COMPLETE
        5. List missing fields if incomplete

        Output: Verification report with data status""",
        expected_output="Verification report: NEW/INCOMPLETE/COMPLETE with missing fields list",
        agent=graph_verifier
    )

    research_task = Task(
        description="""Research missing data autonomously.

        1. Start with manufacturer website (VERIFIED)
        2. Cross-reference with retailers (CORROBORATED)
        3. Check review sites if needed (REPORTED)
        4. Log EVERY source consulted
        5. Extract all specs: weight, price, materials, URLs, images
        6. Complete research log

        Required fields: name, brand, weight, price, type, productUrl, imageUrl
        Target: ≥85% completeness""",
        expected_output="Complete product data with source citations and ≥85% completeness",
        agent=autonomous_researcher,
        context=[verify_task]
    )

    validate_task = Task(
        description="""Validate research quality.

        Check:
        1. Completeness ≥85%
        2. No contradictions
        3. At least one VERIFIED source
        4. Proper units and formats
        5. Calculate quality score

        Pass criteria: ≥85% complete, ≥1 verified source, no critical conflicts""",
        expected_output="Validation report: PASS/FAIL with quality score and issues",
        agent=data_validator,
        context=[research_task]
    )

    citation_task = Task(
        description="""Document complete research trail.

        Create comprehensive research log:
        1. All sources with URLs and types
        2. Data found from each source
        3. Conflicts and resolutions
        4. Quality metrics
        5. Persistence to Research Log database

        Format: Detailed audit trail ready for review""",
        expected_output="Formatted research log with complete source documentation",
        agent=citation_agent,
        context=[research_task, validate_task]
    )

    return [verify_task, research_task, validate_task, citation_task]
