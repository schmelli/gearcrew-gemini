"""
Flow state management for the gear collection system.
Defines the shared state used across all teams via CrewAI Flows.
"""
from pydantic import BaseModel, Field
from typing import Set, List, Dict, Optional
from datetime import datetime

class GearCollectionState(BaseModel):
    """
    Shared state for the GearCollectionFlow.
    All methods in the Flow can access and modify this state.
    """

    # Source tracking
    visited_sources: Set[str] = Field(
        default_factory=set,
        description="URLs that have been scanned (to avoid duplicates)"
    )
    last_scan_time: Dict[str, datetime] = Field(
        default_factory=dict,
        description="Last scan timestamp for each source type (youtube, website, etc.)"
    )

    # Discovery tracking
    pending_discoveries: List[str] = Field(
        default_factory=list,
        description="Discovery IDs waiting for curation"
    )
    discoveries_today: int = Field(
        default=0,
        description="Number of items discovered today"
    )

    # Research tracking
    research_in_progress: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of discovery_id -> researcher_agent_name"
    )
    research_completed: Set[str] = Field(
        default_factory=set,
        description="Discovery IDs that have been fully researched"
    )
    verifications_today: int = Field(
        default=0,
        description="Number of items verified today"
    )

    # Graph update tracking
    graph_updates_pending: List[str] = Field(
        default_factory=list,
        description="Discovery IDs with Cypher code ready to execute"
    )
    graph_nodes_created: int = Field(
        default=0,
        description="Total nodes created in GearGraph"
    )
    graph_relationships_created: int = Field(
        default=0,
        description="Total relationships created in GearGraph"
    )

    # Quality metrics
    errors_encountered: List[Dict] = Field(
        default_factory=list,
        description="Error log with timestamps and details"
    )
    quality_scores: List[float] = Field(
        default_factory=list,
        description="Data completeness scores (0.0-1.0)"
    )

    # Configuration
    max_parallel_scans: int = Field(
        default=4,
        description="Maximum number of concurrent source scans"
    )
    max_parallel_research: int = Field(
        default=3,
        description="Maximum number of concurrent research tasks"
    )
    quality_threshold: float = Field(
        default=0.95,
        description="Minimum data completeness required (0.0-1.0)"
    )

    # Session info
    session_start: Optional[datetime] = Field(
        default=None,
        description="When the current flow session started"
    )
    total_cycles: int = Field(
        default=0,
        description="Number of discovery-research-update cycles completed"
    )

    class Config:
        # Allow arbitrary types (for datetime)
        arbitrary_types_allowed = True
        # Allow sets to be serialized
        json_encoders = {
            set: list,
            datetime: lambda v: v.isoformat() if v else None
        }


class TeamMetrics(BaseModel):
    """Metrics for a specific team's performance"""
    team_name: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_duration_seconds: float = 0.0
    last_active: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
