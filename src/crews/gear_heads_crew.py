"""
Gear-heads Crew - The discovery team for continuous gear scanning

This crew continuously monitors web sources for outdoor gear content,
extracts product information and insights, and hands off discoveries
to the Curators team for research and verification.
"""
from crewai import Crew, Process
from typing import Dict, Any

from src.agents.discovery_manager import create_discovery_manager
from src.agents.scanners import create_scanner_agents
from src.tasks.discovery_tasks import create_discovery_tasks


class GearHeadsCrew:
    """
    The Gear-heads discovery team.

    Uses hierarchical process with a manager coordinating
    four specialized scanner agents running in parallel.
    """

    def __init__(self):
        """Initialize the Gear-heads crew with agents and tasks"""
        # Create manager
        self.manager = create_discovery_manager()

        # Create scanner agents
        scanners = create_scanner_agents()
        self.youtube_scanner = scanners[0]
        self.website_scanner = scanners[1]
        self.blog_scanner = scanners[2]
        self.reddit_scanner = scanners[3]

        # Create tasks
        self.tasks = create_discovery_tasks(
            manager=self.manager,
            youtube_scanner=self.youtube_scanner,
            website_scanner=self.website_scanner,
            blog_scanner=self.blog_scanner,
            reddit_scanner=self.reddit_scanner
        )

    def crew(self) -> Crew:
        """
        Create the Crew instance with hierarchical process.

        Returns:
            Configured Crew ready for execution
        """
        return Crew(
            agents=[
                # NOTE: Manager is NOT included here when using hierarchical process
                # with custom manager_agent - it's provided separately below
                self.youtube_scanner,
                self.website_scanner,
                self.blog_scanner,
                self.reddit_scanner
            ],
            tasks=self.tasks,
            process=Process.hierarchical,  # Manager delegates to workers
            manager_agent=self.manager,  # Use our custom manager
            memory=True,  # Remember past scans and decisions
            verbose=True,  # Detailed logging
            max_rpm=100,  # Rate limiting for API calls
        )

    def kickoff(self, inputs: Dict[str, Any] = None) -> Dict:
        """
        Start the discovery process.

        Args:
            inputs: Optional input parameters
                - search_terms: List of additional search terms
                - target_sources: Specific sources to scan
                - days_back: How many days of content to scan (default: 7)
                - max_discoveries: Maximum discoveries to queue (default: 100)

        Returns:
            Discovery report with statistics and queued items
        """
        default_inputs = {
            "days_back": 7,
            "max_discoveries": 100,
            "search_terms": [
                "ultralight backpacking gear",
                "tent review",
                "sleeping bag review",
                "backpack review",
                "hiking gear 2025",
            ],
            "target_manufacturers": [
                "Durston Gear",
                "Zpacks",
                "Hyperlite Mountain Gear",
                "NEMO Equipment",
                "Big Agnes",
            ]
        }

        # Merge with provided inputs
        if inputs:
            default_inputs.update(inputs)

        # Execute the crew
        result = self.crew().kickoff(inputs=default_inputs)

        return result

    def kickoff_async(self, inputs: Dict[str, Any] = None):
        """
        Start the discovery process asynchronously.

        Args:
            inputs: Optional input parameters (same as kickoff)

        Returns:
            Future object for async execution
        """
        default_inputs = {
            "days_back": 7,
            "max_discoveries": 100,
        }

        if inputs:
            default_inputs.update(inputs)

        return self.crew().kickoff_async(inputs=default_inputs)


# Convenience function for quick crew creation
def create_gear_heads_crew() -> GearHeadsCrew:
    """
    Create and return a new Gear-heads crew instance.

    Returns:
        Configured GearHeadsCrew ready for execution
    """
    return GearHeadsCrew()


# Example usage
if __name__ == "__main__":
    # Create crew
    crew = create_gear_heads_crew()

    # Run discovery
    print("Starting Gear-heads discovery crew...")
    result = crew.kickoff()

    print("\n" + "="*70)
    print("DISCOVERY COMPLETE")
    print("="*70)
    print(result)
