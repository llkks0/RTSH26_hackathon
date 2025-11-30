"""Lightweight Pydantic schemas shared across pipeline steps."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AnalyticsData(BaseModel):
	"""Analytics metrics for a generated image."""

	model_config = ConfigDict(validate_assignment=True)

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
	"""Minimal image representation flowing through the pipeline."""

	model_config = ConfigDict(validate_assignment=True)

	id: str
	file_name: str
	metadata_tags: list[str] | None = None
	final_prompt: str | None = None
	analytics: AnalyticsData | None = None


__all__ = ["AnalyticsData", "ImageData"]
