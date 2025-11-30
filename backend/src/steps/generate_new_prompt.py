"""Utility helpers for crafting refined prompts after analytics review."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, Sequence

try:
	from ..models import Asset
except ImportError:  # pragma: no cover - fallback for standalone execution
	from models import Asset  # type: ignore
from .evaluate_image_groups import ImageAnalysisResult


logger = logging.getLogger(__name__)


def _get_attr(source: Any, key: str, default: Any = None) -> Any:
	if isinstance(source, Mapping):
		return source.get(key, default)
	return getattr(source, key, default)


def _describe_asset(asset: Any, score: float | None = None) -> str:
	asset_type_val = _get_attr(asset, 'asset_type', 'asset')
	if hasattr(asset_type_val, 'value'):
		asset_type_val = asset_type_val.value
	name = _get_attr(asset, 'name', _get_attr(asset, 'file_name', 'unknown'))
	tags = _get_attr(asset, 'tags', []) or []
	details: list[str] = []
	if tags:
		details.append(f"tags={', '.join(tags[:3])}")
	if score is not None:
		details.append(f"similarity={score:.2f}")
	suffix = f" ({'; '.join(details)})" if details else ""
	return f"{asset_type_val}: {name}{suffix}"


def build_enhanced_prompt(
	base_prompt: str,
	target_group: str,
	analysis: ImageAnalysisResult,
	similar_assets: Sequence[tuple[Any, float]] | None = None,
	extra_constraints: str | None = None,
) -> str:
	"""Merge base prompt, analytics insights, and asset cues."""

	sections: list[str] = []
	base = base_prompt.strip()
	if base:
		sections.append(base)

	tags = analysis.get('differentiation_tags') or []
	if tags:
		sections.append(
			f"Highlight elements that resonate with {target_group}: {', '.join(tags)}."
		)

	text = analysis.get('differentiation_text')
	if text:
		sections.append(text.strip())

	if similar_assets:
		asset_brief = ', '.join(
			_describe_asset(asset, score) for asset, score in similar_assets
		)
		sections.append(
			f"Incorporate inspiration from the following assets: {asset_brief}."
		)

	if extra_constraints:
		sections.append(extra_constraints.strip())

	prompt = ' '.join(section for section in sections if section)
	logger.info(
		"Built enhanced prompt for %s (sections=%s)", target_group, len(sections)
	)
	return prompt


__all__ = ["build_enhanced_prompt"]
