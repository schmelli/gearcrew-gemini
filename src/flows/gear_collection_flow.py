"""
GearCollectionFlow - Orchestrates all crews with event-driven Flows

Uses CrewAI Flows to coordinate:
1. Gear-heads (Discovery) → 2. Curators (Research) → 3. Architects (Graph Load)
"""
from crewai.flow.flow import Flow, listen, start, router, and_, or_
from typing import List, Dict, Any, Optional
import logging

from src.models.flow_state import GearCollectionState
from src.crews.gear_heads_crew import GearHeadsCrew
from src.crews.curators_crew import CuratorsCrew
from src.crews.architects_crew import ArchitectsCrew

logger = logging.getLogger(__name__)


class GearCollectionFlow(Flow[GearCollectionState]):
    """
    Main orchestration Flow for the GearCrew multi-team system.

    Coordinates three crews in sequence with conditional routing:
    - Gear-heads: Discover gear from web sources
    - Curators: Verify and research discoveries
    - Architects: Safely load validated data to graph
    """

    def __init__(self):
        super().__init__()
        self.gear_heads = GearHeadsCrew()
        self.curators = CuratorsCrew()
        self.architects = ArchitectsCrew()

    @start()
    def discover_gear(self) -> Dict[str, Any]:
        """
        Step 1: Gear-heads scan sources in parallel.

        Returns discovery report with products, insights, and sources scanned.
        """
        logger.info("Starting Gear-heads discovery crew...")

        result = self.gear_heads.kickoff(inputs={
            "days_back": 7,
            "max_discoveries": self.state.max_parallel_scans * 25,
        })

        logger.info(f"Discovery complete. Processing results...")
        return {"discoveries": result, "phase": "discovery"}

    @listen(discover_gear)
    def filter_new_discoveries(self, discovery_result: Dict) -> Dict[str, Any]:
        """
        Step 2: Filter out already-processed items.

        Uses state to track visited sources and prevent duplicate work.
        """
        discoveries = discovery_result.get("discoveries", [])

        # Filter items we've already seen
        if isinstance(discoveries, list):
            new_items = [
                d for d in discoveries
                if str(d.get('id', d)) not in self.state.visited_sources
            ]
            # Update state with new items
            for item in new_items:
                item_id = str(item.get('id', item))
                self.state.visited_sources.add(item_id)
                self.state.pending_discoveries.append(item_id)
        else:
            new_items = discoveries

        logger.info(f"Filtered to {len(new_items) if isinstance(new_items, list) else 'N/A'} new discoveries")
        return {"items": new_items, "count": len(new_items) if isinstance(new_items, list) else 1}

    @router(filter_new_discoveries)
    def route_by_volume(self, filtered_result: Dict) -> str:
        """
        Step 3: Route based on discovery volume.

        - batch_process: >50 items, split into batches
        - normal_process: 1-50 items, standard curation
        - idle: 0 items, nothing to do
        """
        count = filtered_result.get("count", 0)

        if count > 50:
            logger.info(f"Routing {count} items to batch_process")
            return "batch_process"
        elif count > 0:
            logger.info(f"Routing {count} items to normal_process")
            return "normal_process"
        else:
            logger.info("No new items, going idle")
            return "idle"

    @listen("normal_process")
    def curate_discoveries(self, filtered_result: Dict) -> Dict[str, Any]:
        """
        Step 4a: Curators verify and research (standard flow).
        """
        items = filtered_result.get("items", [])
        logger.info(f"Curating {len(items) if isinstance(items, list) else 1} discoveries...")

        result = self.curators.kickoff(inputs={"discoveries": items})

        return {"curated_data": result, "batch": False}

    @listen("batch_process")
    def batch_curate(self, filtered_result: Dict) -> Dict[str, Any]:
        """
        Step 4b: Split large batches across multiple curations.
        """
        items = filtered_result.get("items", [])
        logger.info(f"Batch processing {len(items)} discoveries...")

        # Split into batches of 10
        batch_size = 10
        batches = [items[i:i+batch_size] for i in range(0, len(items), batch_size)]

        all_results = []
        for i, batch in enumerate(batches):
            logger.info(f"Processing batch {i+1}/{len(batches)}...")
            result = self.curators.kickoff(inputs={"discoveries": batch})
            all_results.append(result)

        return {"curated_data": all_results, "batch": True, "batch_count": len(batches)}

    @listen("idle")
    def handle_idle(self, filtered_result: Dict) -> Dict[str, Any]:
        """
        Step 4c: Nothing to process, return idle status.
        """
        logger.info("No new discoveries to process. Flow idle.")
        return {"status": "idle", "message": "No new discoveries"}

    @listen(or_(curate_discoveries, batch_curate))
    def load_to_graph(self, curated_result: Dict) -> Dict[str, Any]:
        """
        Step 5: Graph Architects safely load validated data.
        """
        curated_data = curated_result.get("curated_data", {})
        is_batch = curated_result.get("batch", False)

        logger.info("Loading curated data to GearGraph...")

        result = self.architects.kickoff(inputs={
            "data": curated_data,
            "is_batch": is_batch
        })

        # Update state with graph statistics
        nodes = result.get("nodes_created", 0) if isinstance(result, dict) else 0
        rels = result.get("relationships_created", 0) if isinstance(result, dict) else 0

        self.state.graph_nodes_created += nodes

        logger.info(f"Graph load complete. Nodes: {nodes}, Relationships: {rels}")
        return {"load_result": result, "nodes": nodes, "relationships": rels}

    @listen(load_to_graph)
    def generate_report(self, load_result: Dict) -> Dict[str, Any]:
        """
        Step 6: Generate final report with statistics.
        """
        report = {
            "status": "complete",
            "statistics": {
                "sources_visited": len(self.state.visited_sources),
                "discoveries_pending": len(self.state.pending_discoveries),
                "nodes_created_total": self.state.graph_nodes_created,
                "quality_threshold": self.state.quality_threshold,
            },
            "last_load": load_result
        }

        logger.info(f"Flow complete. Report: {report}")
        return report


def run_gear_collection(days_back: int = 7, max_discoveries: int = 100) -> Dict:
    """
    Convenience function to run the GearCollectionFlow.

    Args:
        days_back: How many days of content to scan
        max_discoveries: Maximum discoveries to process

    Returns:
        Flow result with statistics
    """
    flow = GearCollectionFlow()

    # Override state defaults if needed
    flow.state.max_parallel_scans = 4
    flow.state.quality_threshold = 0.85

    result = flow.kickoff()
    return result


# Entry point for direct execution
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_gear_collection()
    print(f"\nFlow Result:\n{result}")
