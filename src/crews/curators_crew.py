"""
Curators Crew - The data verification and research team
"""
from crewai import Crew, Process
from typing import Dict, Any

from src.agents.curators_manager import create_curators_manager
from src.agents.curators import create_curator_agents
from src.tasks.curation_tasks import create_curation_tasks


class CuratorsCrew:
    """
    The Curators verification and research team.

    Uses hierarchical process for coordinated data curation.
    """

    def __init__(self):
        """Initialize the Curators crew"""
        self.manager = create_curators_manager()

        curators = create_curator_agents()
        self.graph_verifier = curators[0]
        self.autonomous_researcher = curators[1]
        self.data_validator = curators[2]
        self.citation_agent = curators[3]

        self.tasks = create_curation_tasks(
            manager=self.manager,
            graph_verifier=self.graph_verifier,
            autonomous_researcher=self.autonomous_researcher,
            data_validator=self.data_validator,
            citation_agent=self.citation_agent
        )

    def crew(self) -> Crew:
        """Create Crew instance"""
        return Crew(
            agents=[
                self.graph_verifier,
                self.autonomous_researcher,
                self.data_validator,
                self.citation_agent
            ],
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self.manager,
            memory=True,
            verbose=True,
            max_rpm=100,
        )

    def kickoff(self, inputs: Dict[str, Any] = None) -> Dict:
        """Start curation process"""
        return self.crew().kickoff(inputs=inputs or {})


def create_curators_crew() -> CuratorsCrew:
    """Create Curators crew"""
    return CuratorsCrew()
