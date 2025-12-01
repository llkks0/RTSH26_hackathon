"""
Asset selection utilities.

Functions for grouping assets by type and selecting random sets.
"""

import random
from collections import defaultdict
from uuid import UUID

from models import Asset, AssetType

from .types import AssetSelectionInput, AssetSelectionOutput, AssetSet


def group_assets_by_type(assets: list[Asset]) -> dict[AssetType, list[Asset]]:
    """
    Group assets by their asset type.

    Args:
        assets: List of assets to group

    Returns:
        Dictionary mapping asset type to list of assets
    """
    grouped: dict[AssetType, list[Asset]] = defaultdict(list)
    for asset in assets:
        grouped[asset.asset_type].append(asset)
    return dict(grouped)


def select_asset_sets(input_data: AssetSelectionInput) -> AssetSelectionOutput:
    """
    Select multiple random sets of assets, one per asset type.

    This function creates N sets of assets, where each set contains exactly one
    asset per asset type. It tries to avoid reusing assets that have been used
    previously (tracked via used_asset_ids), but will reuse if necessary.

    Args:
        input_data: AssetSelectionInput with assets, num_sets, and used_asset_ids

    Returns:
        AssetSelectionOutput with the selected asset sets and grouped assets
    """
    assets_by_type = group_assets_by_type(input_data.assets)

    if not assets_by_type:
        return AssetSelectionOutput(
            asset_sets=[],
            assets_by_type={},
        )

    asset_sets: list[AssetSet] = []
    used_ids_per_type: dict[AssetType, set[UUID]] = defaultdict(set)

    # Initialize with already used IDs
    for asset in input_data.assets:
        if asset.id in input_data.used_asset_ids:
            used_ids_per_type[asset.asset_type].add(asset.id)

    for _ in range(input_data.num_sets):
        selected: dict[AssetType, Asset] = {}

        for asset_type, type_assets in assets_by_type.items():
            if not type_assets:
                continue

            used_ids = used_ids_per_type[asset_type]

            # Find assets not yet used
            available = [a for a in type_assets if a.id not in used_ids]

            if not available:
                # Reset if all assets have been used
                used_ids.clear()
                available = list(type_assets)

            # Select random asset
            chosen = random.choice(available)
            selected[asset_type] = chosen
            used_ids.add(chosen.id)

        if selected:
            asset_sets.append(AssetSet(assets=selected))

    return AssetSelectionOutput(
        asset_sets=asset_sets,
        assets_by_type=assets_by_type,
    )


def select_single_asset_set(
    assets: list[Asset],
    used_asset_ids: set[UUID] | None = None,
) -> AssetSet | None:
    """
    Convenience function to select a single set of assets.

    Args:
        assets: List of assets to select from
        used_asset_ids: Set of asset IDs to deprioritize

    Returns:
        A single AssetSet, or None if no assets available
    """
    input_data = AssetSelectionInput(
        assets=assets,
        num_sets=1,
        used_asset_ids=used_asset_ids or set(),
    )
    output = select_asset_sets(input_data)
    return output.asset_sets[0] if output.asset_sets else None


def get_base_and_reference_assets(
    asset_set: AssetSet,
    base_asset_type: AssetType = AssetType.MODEL,
) -> tuple[Asset | None, list[Asset]]:
    """
    Split an asset set into base and reference assets.

    Args:
        asset_set: The asset set to split
        base_asset_type: Which asset type should be the base (default: MODEL)

    Returns:
        Tuple of (base_asset, reference_assets)
        base_asset is None if the base_asset_type is not in the set
    """
    base_asset = asset_set.assets.get(base_asset_type)

    reference_assets = [
        asset for asset_type, asset in asset_set.assets.items()
        if asset_type != base_asset_type
    ]

    # If no MODEL asset, use the first available as base
    if base_asset is None and asset_set.assets:
        first_type = next(iter(asset_set.assets))
        base_asset = asset_set.assets[first_type]
        reference_assets = [
            asset for asset_type, asset in asset_set.assets.items()
            if asset_type != first_type
        ]

    return base_asset, reference_assets
