"""End-to-end campaign orchestration script for the image workflow."""

from __future__ import annotations

import argparse
import logging
import re
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set
from urllib.parse import urlparse

import requests
from sqlmodel import Session

from database import engine
from schemas import ImageData
from steps.evaluate_image_groups import ImageAnalysisResult, analyze_image_differences
from steps.generate_new_prompt import build_enhanced_prompt
from steps.generate_step import FluxBatchSession, FluxGenerationError, print_concise_summary
from steps.get_analytics import get_analytics
from steps.search_new_assets import DEFAULT_TOP_K, search_new_assets
from steps.select_top_images import select_top_images


logger = logging.getLogger(__name__)

DEFAULT_IMAGES_PER_GROUP = 5
DEFAULT_TOP_N = 2
DEFAULT_ITERATIONS = 2


def _results_to_images(group: str, raw_images: List[Dict[str, Any]]) -> List[ImageData]:
    images: List[ImageData] = []
    for idx, result in enumerate(raw_images, start=1):
        image_id = str(result.get("request_id") or f"{group}-{idx}")
        file_name = str(result.get("image_url") or f"generated_{image_id}.png")
        asset_tags = [
            f"{asset_class}:{asset.get('name') or asset.get('id')}"
            for asset_class, asset in result.get("assets", {}).items()
        ]
        metadata_tags = asset_tags + [f"target_group:{group}"]
        images.append(
            ImageData(
                id=image_id,
                file_name=file_name,
                metadata_tags=metadata_tags,
                final_prompt=str(result.get("prompt", "")),
            )
        )
    return images


def _attach_analytics(images: List[ImageData]) -> List[ImageData]:
    analytics = get_analytics(images)
    analytics_map = {item.id: item for item in analytics}
    enriched: List[ImageData] = []
    for image in images:
        enriched.append(image.model_copy(update={"analytics": analytics_map[image.id]}))
    return enriched


def _build_asset_search_prompt(images: Sequence[ImageData], top_ids: set[str]) -> str:
    fragments: List[str] = []
    for image in images:
        if image.id not in top_ids:
            continue
        if image.final_prompt:
            fragments.append(image.final_prompt)
        if image.metadata_tags:
            fragments.append(", ".join(image.metadata_tags))
    return " ".join(fragment for fragment in fragments if fragment).strip()


def _get_top_ids(analytics_list: Sequence) -> set[str]:
    return {item.id for item in analytics_list}


def _summarize_group(
    group: str,
    iteration_label: str,
    analysis: ImageAnalysisResult,
    new_prompt: str,
    saved_paths: Sequence[str],
) -> None:
    tags = analysis.get('differentiation_tags', []) or []
    truncated_insight = _truncate_text(analysis.get('differentiation_text', ''))
    prompt_preview = _truncate_text(new_prompt, limit=160)
    logger.info(
        "[%s | %s] tags=%s | files_saved=%s",
        group,
        iteration_label,
        ', '.join(tags[:4]),
        len(saved_paths),
    )
    print(f"\n--- {group} · {iteration_label} ---")
    print(f"Next prompt preview: {prompt_preview}")
    if tags:
        print(f"Key tags: {', '.join(tags[:5])}")
    if truncated_insight:
        print(f"Insight (truncated): {truncated_insight}")


@contextmanager
def _maybe_db_session():
    try:
        with Session(engine) as session:
            yield session
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] Skipping database-backed asset search: {exc}")
        yield None


def _search_assets_safe(db_session: Session | None, prompt: str, top_k: int):
    if db_session is None or top_k <= 0:
        return []
    try:
        return search_new_assets(
            session=db_session,
            prompt=prompt,
            top_k=top_k,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] Asset search failed, continuing without new references: {exc}")
        return []


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return slug.strip("-") or "group"


def _truncate_text(text: str, limit: int = 280) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _prepare_output_root(output_dir: str | None) -> Path:
    if output_dir:
        base = Path(output_dir)
    else:
        base = Path(__file__).resolve().parents[1] / "generated_images"
    base.mkdir(parents=True, exist_ok=True)
    timestamp_dir = base / datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    timestamp_dir.mkdir(parents=True, exist_ok=True)
    return timestamp_dir


def _save_images_to_disk(
    raw_images: List[Dict[str, Any]],
    destination: Path,
    iteration_label: str,
) -> List[str]:
    saved_paths: List[str] = []
    destination.mkdir(parents=True, exist_ok=True)
    for idx, image in enumerate(raw_images, start=1):
        url = image.get("image_url")
        if not url:
            continue
        suffix = Path(urlparse(url).path).suffix or ".png"
        file_name = f"{iteration_label}_{idx:02d}{suffix}"
        target_path = destination / file_name
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            target_path.write_bytes(response.content)
            saved_paths.append(str(target_path))
            logger.debug("Saved %s to %s", url, target_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to save image %s: %s", url, exc)
    return saved_paths


def _collect_asset_preferences_from_results(
    raw_images: List[Dict[str, Any]],
    preferred_image_ids: Set[str],
) -> Dict[str, Set[str]]:
    preferences: Dict[str, Set[str]] = defaultdict(set)
    for image in raw_images:
        request_id = str(image.get("request_id"))
        if request_id not in preferred_image_ids:
            continue
        for asset_class, asset in image.get("assets", {}).items():
            asset_id = asset.get("id")
            if asset_id:
                preferences[asset_class].add(asset_id)
    return preferences


def _normalize_class_name(name: str, available_classes: Set[str]) -> str | None:
    candidates = [name, name.lower()]
    if name.endswith("s"):
        candidates.append(name[:-1])
    else:
        candidates.append(f"{name}s")
    for candidate in candidates:
        if candidate in available_classes:
            return candidate
    return None


def _collect_asset_preferences_from_similar(
    similar_assets: Sequence[tuple[Any, float]],
    available_classes: Set[str],
) -> Dict[str, Set[str]]:
    preferences: Dict[str, Set[str]] = defaultdict(set)
    for asset, _score in similar_assets:
        asset_type = getattr(asset, "asset_type", None)
        if asset_type is None:
            continue
        class_name = asset_type.value if hasattr(asset_type, "value") else str(asset_type)
        normalized = _normalize_class_name(str(class_name), available_classes)
        file_name = getattr(asset, "file_name", "")
        asset_id = Path(file_name).stem if file_name else None
        if normalized and asset_id:
            preferences[normalized].add(asset_id)
    return preferences


def _merge_preference_maps(
    available_classes: Set[str],
    *maps: Dict[str, Set[str]],
) -> Dict[str, Set[str]]:
    merged: Dict[str, Set[str]] = defaultdict(set)
    for pref_map in maps:
        for cls, ids in pref_map.items():
            normalized = _normalize_class_name(cls, available_classes)
            if not normalized:
                continue
            merged[normalized].update(ids)
    return {cls: ids for cls, ids in merged.items() if ids}


def run_campaign(
    assets_dir: str,
    base_prompt: str,
    target_groups: Sequence[str],
    images_per_group: int = DEFAULT_IMAGES_PER_GROUP,
    top_n: int = DEFAULT_TOP_N,
    search_top_k: int = DEFAULT_TOP_K,
    iterations: int = DEFAULT_ITERATIONS,
    output_dir: str | None = None,
) -> Dict[str, dict]:
    session = FluxBatchSession(assets_dir)
    available_classes = set(session.assets.keys())
    campaign_results: Dict[str, dict] = {}
    run_output_root = _prepare_output_root(output_dir)
    logger.info("Saving generated assets under %s", run_output_root)

    total_iterations = max(1, iterations)

    with _maybe_db_session() as db_session:
        for group in target_groups:
            group_slug = _slugify(group)
            group_dir = run_output_root / group_slug
            group_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Starting group '%s' (output=%s)", group, group_dir)

            preferred_assets: Dict[str, Set[str]] | None = None
            prompt_for_iteration = base_prompt
            iteration_records: List[dict] = []

            for iteration_idx in range(total_iterations):
                iteration_label = f"iter_{iteration_idx + 1}"
                logger.info(
                    "[%s | %s] Generating %s images", group, iteration_label, images_per_group
                )
                raw_images = session.generate_images_for_group(
                    base_prompt=prompt_for_iteration,
                    target_group=group,
                    num_images=images_per_group,
                    preferred_asset_ids=preferred_assets,
                )
                print_concise_summary({f"{group} ({iteration_label})": raw_images})

                saved_files = _save_images_to_disk(
                    raw_images,
                    group_dir / iteration_label,
                    iteration_label,
                )

                images = _results_to_images(group, raw_images)
                enriched_images = _attach_analytics(images)

                top_analytics = select_top_images(enriched_images, top_n=top_n)
                top_ids = _get_top_ids(top_analytics)

                analysis = analyze_image_differences(enriched_images, top_n=top_n)

                search_prompt = _build_asset_search_prompt(enriched_images, top_ids)
                prompt_for_search = search_prompt or prompt_for_iteration
                similar_assets = _search_assets_safe(
                    db_session=db_session,
                    prompt=prompt_for_search,
                    top_k=search_top_k,
                )

                preferences_from_results = _collect_asset_preferences_from_results(
                    raw_images,
                    top_ids,
                )
                preferences_from_similar = _collect_asset_preferences_from_similar(
                    similar_assets,
                    available_classes,
                )
                preferred_assets = _merge_preference_maps(
                    available_classes,
                    preferences_from_results,
                    preferences_from_similar,
                ) or None

                next_prompt = build_enhanced_prompt(
                    base_prompt=base_prompt,
                    target_group=group,
                    analysis=analysis,
                    similar_assets=similar_assets,
                    extra_constraints="Keep outputs suitable for paid social ads.",
                )

                prefs_snapshot = (
                    {cls: sorted(ids) for cls, ids in preferred_assets.items()}
                    if preferred_assets
                    else None
                )

                iteration_records.append(
                    {
                        "label": iteration_label,
                        "prompt_used": prompt_for_iteration,
                        "raw_images": raw_images,
                        "images": enriched_images,
                        "top_analytics": top_analytics,
                        "analysis": analysis,
                        "similar_assets": similar_assets,
                        "saved_files": saved_files,
                        "next_prompt": next_prompt,
                        "preferred_assets_for_next": prefs_snapshot,
                    }
                )

                _summarize_group(
                    group,
                    iteration_label,
                    analysis,
                    next_prompt,
                    saved_files,
                )

                if iteration_idx < total_iterations - 1:
                    prompt_for_iteration = next_prompt

            campaign_results[group] = {
                "iterations": iteration_records,
                "output_dir": str(group_dir),
                "final_prompt": prompt_for_iteration,
            }

    campaign_results["_output_root"] = str(run_output_root)
    return campaign_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the campaign pipeline")
    default_assets_dir = Path(__file__).resolve().parents[1] / "assets_folder"
    parser.add_argument(
        "--assets-dir",
        default=str(default_assets_dir),
        help="Directory containing asset class folders",
    )
    parser.add_argument(
        "--base-prompt",
        required=False,
        default="<provide base prompt>",
        help="Base prompt describing the campaign look",
    )
    parser.add_argument(
        "--target-groups",
        nargs="+",
        default=[
            "Gen Z streetwear enthusiasts",
            "Minimalist business professionals",
            "Outdoor techwear fans",
        ],
        help="List of target groups",
    )
    parser.add_argument(
        "--images-per-group",
        type=int,
        default=DEFAULT_IMAGES_PER_GROUP,
        help="Number of images to generate per target group",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=DEFAULT_TOP_N,
        help="Number of top images to analyze",
    )
    parser.add_argument(
        "--search-top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help="How many similar assets to retrieve via embedding search",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help="Total number of generation passes per group (default: 2).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for saving generated images (default: backend/generated_images)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    try:
        run_campaign(
            assets_dir=args.assets_dir,
            base_prompt=args.base_prompt,
            target_groups=args.target_groups,
            images_per_group=args.images_per_group,
            top_n=args.top_n,
            search_top_k=args.search_top_k,
            iterations=args.iterations,
            output_dir=args.output_dir,
        )
    except FluxGenerationError as exc:
        print(f"Flux generation failed: {exc}")
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()
