from pydantic import BaseModel


class AnalyticsData(BaseModel):
    id: str
    impressions: int
    clicks: int
    ctr: float
    interactions: int
    interaction_rate: float
    conversions: int
    conversion_rate: float
    cost: float
    avg_cpc: float
    cpm: float
    conversion_value: float
    value_per_conversion: float


class ImageData(BaseModel):
    """Schema for image data that can be passed around."""
    
    id: str
    file_name: str  # path or URL of the image
    metadata_tags: list[str] | None = None  # e.g., ["warm colors", "close-up", "indoor"]
    model_version: str | None = None  # image model version identifier
    
    # Optional text components for the ad
    headline: str | None = None
    description_line1: str | None = None
    description_line2: str | None = None
    
    # Prompt that was used to generate this image
    final_prompt: str | None = None
    
    # Analytics metrics (optional, can be populated later)
    analytics: AnalyticsData | None = None 
