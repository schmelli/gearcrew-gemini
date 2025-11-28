"""
Data models for discoveries made by the Gear-heads team.
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

class DiscoveryType(str, Enum):
    """Types of discoveries that can be made"""
    BRAND = "brand"
    PRODUCT = "product"
    INSIGHT = "insight"
    CATEGORY = "category"

class SourceType(str, Enum):
    """Types of sources where discoveries are made"""
    YOUTUBE = "youtube"
    WEBSITE = "website"
    BLOG = "blog"
    REDDIT = "reddit"
    FORUM = "forum"
    OTHER = "other"

class Discovery(BaseModel):
    """
    A single discovery from the Gear-heads team.
    This could be a brand, product, insight, or category.
    """
    # Identity
    discovery_id: str = Field(
        ...,
        description="Unique identifier for this discovery"
    )
    discovery_type: DiscoveryType = Field(
        ...,
        description="Type of discovery (brand, product, insight, category)"
    )

    # Content
    name: str = Field(
        ...,
        description="Name of the discovered entity"
    )
    context: str = Field(
        ...,
        description="Surrounding context where this was discovered"
    )
    partial_data: Dict = Field(
        default_factory=dict,
        description="Any partial data extracted (specs, attributes, etc.)"
    )

    # Source information
    source_url: HttpUrl = Field(
        ...,
        description="URL where this was discovered"
    )
    source_type: SourceType = Field(
        ...,
        description="Type of source (youtube, website, blog, etc.)"
    )
    source_title: Optional[str] = Field(
        None,
        description="Title of the source (video title, page title, etc.)"
    )

    # Metadata
    discovered_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this was discovered"
    )
    discovered_by: str = Field(
        ...,
        description="Name of the scanner agent that found this"
    )

    # Status tracking
    status: str = Field(
        default="pending",
        description="Status: pending, researching, verified, loaded, error"
    )
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Priority 1-10 (10 = highest priority)"
    )

    # Quality indicators
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in the discovery (0.0-1.0)"
    )
    needs_research: bool = Field(
        default=True,
        description="Whether this needs further research by Curators"
    )

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            HttpUrl: lambda v: str(v)
        }


class BrandDiscovery(Discovery):
    """Specific model for brand discoveries"""
    discovery_type: DiscoveryType = DiscoveryType.BRAND
    website: Optional[HttpUrl] = None
    description: Optional[str] = None


class ProductDiscovery(Discovery):
    """Specific model for product discoveries"""
    discovery_type: DiscoveryType = DiscoveryType.PRODUCT
    brand: str = Field(..., description="Brand name")
    product_family: Optional[str] = None
    estimated_price: Optional[str] = None
    estimated_weight: Optional[str] = None


class InsightDiscovery(Discovery):
    """Specific model for insight/tip discoveries"""
    discovery_type: DiscoveryType = DiscoveryType.INSIGHT
    summary: str = Field(..., description="Short summary of the insight")
    related_products: List[str] = Field(default_factory=list)
