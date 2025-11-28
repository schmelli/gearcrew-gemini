"""Architect Tasks - Safe graph update tasks"""
from crewai import Task
from typing import List

def create_architect_tasks(manager, cypher_validator, relationship_gardener) -> List[Task]:
    """Create Graph Architects tasks"""

    validate_task = Task(
        description="Validate Cypher code for safety and correctness. Check syntax, patterns, ontology compliance.",
        expected_output="Validation report: APPROVED/REJECTED with reasons",
        agent=cypher_validator
    )

    integrity_task = Task(
        description="Check graph integrity post-update. Find orphaned nodes, verify relationships, suggest fixes.",
        expected_output="Integrity report with statistics and auto-fixes applied",
        agent=relationship_gardener,
        context=[validate_task]
    )

    return [validate_task, integrity_task]
