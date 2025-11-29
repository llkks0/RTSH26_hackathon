import os
import time
import random
import requests
from typing import Dict, List, Any


BFL_API_KEY = os.environ.get("BFL_API_KEY")
FLUX_ENDPOINT = "https://api.bfl.ai/v1/flux-2-pro"


class FluxGenerationError(Exception):
    pass


def call_flux_generation(prompt: str,
                         width: int = 1024,
                         height: int = 1024,
                         safety_tolerance: int = 2) -> Dict[str, Any]:
    """
    Call FLUX.2 [pro] text-to-image endpoint and return the raw JSON response.
    """
    if not BFL_API_KEY:
        raise FluxGenerationError("BFL_API_KEY environment variable is not set.")

    payload = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "safety_tolerance": safety_tolerance,
    }

    response = requests.post(
        FLUX_ENDPOINT,
        headers={
            "accept": "application/json",
            "x-key": BFL_API_KEY,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )

    if not response.ok:
        raise FluxGenerationError(
            f"FLUX.2 request failed with status {response.status_code}: {response.text}"
        )

    return response.json()


def poll_flux_result(polling_url: str,
                     timeout: float = 120.0,
                     interval: float = 0.5) -> Dict[str, Any]:
    """
    Poll the FLUX.2 polling_url until status is Ready or Failed.
    Returns the final result JSON if Ready.
    """
    if not BFL_API_KEY:
        raise FluxGenerationError("BFL_API_KEY environment variable is not set.")

    start = time.time()
    while True:
        result = requests.get(
            polling_url,
            headers={
                "accept": "application/json",
                "x-key": BFL_API_KEY,
            },
            timeout=60,
        ).json()

        status = result.get("status")

        if status == "Ready":
            return result
        if status == "Failed":
            raise FluxGenerationError(f"FLUX.2 job failed: {result.get('error')}")

        if (time.time() - start) > timeout:
            raise FluxGenerationError("Polling timed out before result was ready.")

        time.sleep(interval)


def select_assets_for_image(
    assets: Dict[str, List[Dict[str, Any]]],
    used_ids_per_class: Dict[str, set]
) -> Dict[str, Dict[str, Any]]:
    """
    For each asset class (e.g. 'jackets', 'pants'), choose one asset.
    Tries to avoid re-using the same asset in that class until all have been used.
    """
    selection: Dict[str, Dict[str, Any]] = {}

    for asset_class, items in assets.items():
        if not items:
            # no assets for this class; skip
            continue

        used_ids = used_ids_per_class.setdefault(asset_class, set())
        available = [a for a in items if a.get("id") not in used_ids]

        # If all assets have been used, reset and allow reuse
        if not available:
            used_ids.clear()
            available = list(items)

        chosen = random.choice(available)
        selection[asset_class] = chosen
        used_ids.add(chosen.get("id"))

    return selection


def build_prompt(base_prompt: str,
                 target_group: str,
                 selected_assets: Dict[str, Dict[str, Any]]) -> str:
    """
    Build the full prompt from base_prompt, target_group, and selected assets.
    Assumes each asset dict has at least a 'name' or 'description' field.
    """
    asset_descriptions = []
    for asset_class, asset in selected_assets.items():
        desc = asset.get("description") or asset.get("name") or asset.get("id")
        asset_descriptions.append(f"{asset_class}: {desc}")

    assets_text = ", ".join(asset_descriptions) if asset_descriptions else ""
    target_text = f"Styled for target group: {target_group}."

    if assets_text:
        return f"{base_prompt} {target_text} Include the following items: {assets_text}"
    else:
        return f"{base_prompt} {target_text}"


def generate_images_for_targets(
    base_prompt: str,
    target_groups: List[str],
    assets: Dict[str, List[Dict[str, Any]]],
    num_images_per_group: int = 5,
    width: int = 1024,
    height: int = 1024,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Core logic:
    - Loop over target groups
    - For each, generate `num_images_per_group` images
    - Each image uses:
        * base_prompt + target_group text
        * one unique asset per asset class
    Returns a dict: target_group -> list of {prompt, assets, image_url, cost, request_id}.
    """
    results: Dict[str, List[Dict[str, Any]]] = {}
    used_ids_per_class: Dict[str, set] = {}

    for target_group in target_groups:
        group_results: List[Dict[str, Any]] = []

        for i in range(num_images_per_group):
            selected_assets = select_assets_for_image(assets, used_ids_per_class)
            prompt = build_prompt(base_prompt, target_group, selected_assets)

            # 1) Kick off generation
            initial = call_flux_generation(
                prompt=prompt,
                width=width,
                height=height,
            )

            polling_url = initial.get("polling_url")
            request_id = initial.get("id")
            cost = initial.get("cost")

            if not polling_url:
                raise FluxGenerationError(
                    f"No polling_url in response for request {request_id}"
                )

            # 2) Poll for the final image URL
            final = poll_flux_result(polling_url=polling_url)
            sample_url = (
                final.get("result", {})
                .get("sample")
            )

            group_results.append(
                {
                    "prompt": prompt,
                    "target_group": target_group,
                    "assets": selected_assets,
                    "image_url": sample_url,
                    "request_id": request_id,
                    "cost": cost,
                }
            )

        results[target_group] = group_results

    return results


def print_concise_summary(results: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Print a short, human-readable summary of all generated images.
    """
    for target_group, images in results.items():
        print(f"\n=== Target group: {target_group} ===")
        for idx, img in enumerate(images, start=1):
            asset_summaries = []
            for cls, asset in img["assets"].items():
                label = asset.get("name") or asset.get("description") or asset.get("id")
                asset_summaries.append(f"{cls}={label}")

            assets_str = "; ".join(asset_summaries)
            cost = img.get("cost")
            cost_str = f" | cost={cost}" if cost is not None else ""
            print(
                f"  [{idx}] URL={img['image_url']} | assets: {assets_str}{cost_str}"
            )


if __name__ == "__main__":
    # Example usage – adapt this to your actual data structures:

    base_prompt = (
        "High-end fashion e-commerce photo, studio lighting, 4k, "
        "clean background, full body shot."
    )

    target_groups = [
        "Gen Z streetwear enthusiasts",
        "Minimalist business professionals",
    ]

    # Example asset structure:
    # Each asset MUST at least have an 'id', and should ideally have 'name' or 'description'
    assets = {
        "jackets": [
            {"id": "j1", "name": "Oversized black bomber jacket"},
            {"id": "j2", "name": "Cream tailored blazer"},
        ],
        "pants": [
            {"id": "p1", "name": "Wide-leg cargo pants"},
            {"id": "p2", "name": "Slim-fit wool trousers"},
        ],
        "shoes": [
            {"id": "s1", "name": "Chunky white sneakers"},
            {"id": "s2", "name": "Black leather loafers"},
        ],
    }

    try:
        results = generate_images_for_targets(
            base_prompt=base_prompt,
            target_groups=target_groups,
            assets=assets,
            num_images_per_group=2,  # 5 images per target group
            width=1024,
            height=1024,
        )
        print_concise_summary(results)
    except FluxGenerationError as e:
        print(f"Error while generating images: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")