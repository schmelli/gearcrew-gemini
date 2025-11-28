"""
Data models for research conducted by the Curators team.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class SourceType(str, Enum):
    """Types of research sources"""
    MANUFACTURER = "manufacturer"
    RETAILER = "retailer"
    REVIEW_SITE = "review_site"
    BLOG = "blog"
    FORUM = "forum"
    OTHER = "other"

class ConfidenceLevel(str, Enum):
    """Confidence levels for research findings"""
    VERIFIED = "verified"           # From manufacturer/official source
    CORROBORATED = "corroborated"   # Multiple sources agree
    REPORTED = "reported"           # Single source, not verified
    UNCERTAIN = "uncertain"         # Conflicting information

class ResearchSource(BaseModel):
    """A single source consulted during research"""
    url: HttpUrl = Field(..., description="URL of the source")
    source_type: SourceType = Field(..., description="Type of source")
    data_found: List[str] = Field(
        default_factory=list,
        description="Fields/data points found from this source"
    )
    confidence: ConfidenceLevel = Field(..., description="Confidence in this source")
    accessed_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(None, description="Additional notes about this source")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            HttpUrl: lambda v: str(v)
        }

class ResearchLog(BaseModel):
    """
    Complete research log for a discovery.
    Created by the Curators team.
    """
    # Identity
    discovery_id: str = Field(..., description="ID of the discovery being researched")
    research_id: str = Field(..., description="Unique ID for this research session")

    # Research details
    sources: List[ResearchSource] = Field(
        default_factory=list,
        description="All sources consulted during research"
    )
    verified_data: Dict = Field(
        default_factory=dict,
        description="Data verified through research"
    )
    conflicts_found: List[str] = Field(
        default_factory=list,
        description="Any conflicting information discovered"
    )
    missing_data: List[str] = Field(
        default_factory=list,
        description="Data points that could not be found"
    )

    # Quality metrics
    overall_confidence: ConfidenceLevel = Field(
        ...,
        description="Overall confidence in the research"
    )
    completeness_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="% of required fields found (0.0-1.0)"
    )

    # Metadata
    researched_by: str = Field(..., description="Name of the researcher agent")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # Output
    cypher_code: Optional[str] = Field(
        None,
        description="Generated Cypher code for graph update"
    )
    ready_for_load: bool = Field(
        default=False,
        description="Whether this is ready to load into the graph"
    )

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
