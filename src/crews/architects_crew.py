"""Graph Architects Crew - Safe graph updates"""
from crewai import Crew, Process
from typing import Dict, Any

from src.agents.gatekeeper_manager import create_gatekeeper_manager
from src.agents.architects import create_architect_agents
from src.tasks.architect_tasks import create_architect_tasks

class ArchitectsCrew:
    """Graph Architects - safe graph update team"""

    def __init__(self):
        self.manager = create_gatekeeper_manager()
        architects = create_architect_agents()
        self.cypher_validator = architects[0]
        self.relationship_gardener = architects[1]

        self.tasks = create_architect_tasks(
            manager=self.manager,
            cypher_validator=self.cypher_validator,
            relationship_gardener=self.relationship_gardener
        )

    def crew(self) -> Crew:
        return Crew(
            agents=[self.cypher_validator, self.relationship_gardener],
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self.manager,
            memory=True,
            verbose=True,
            max_rpm=100,
        )

    def kickoff(self, inputs: Dict[str, Any] = None) -> Dict:
        return self.crew().kickoff(inputs=inputs or {})

def create_architects_crew() -> ArchitectsCrew:
    return ArchitectsCrew()
