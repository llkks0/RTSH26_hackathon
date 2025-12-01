import base64
import logging
import os
import random
import time
from pathlib import Path
from typing import Any

import requests

BFL_API_KEY = os.environ.get("BFL_API_KEY")
FLUX_ENDPOINT = "https://api.bfl.ai/v1/flux-2-pro"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"}


logger = logging.getLogger(__name__)


class FluxGenerationError(Exception):
    """Custom exception raised when FLUX.2 image generation/editing fails."""
    pass


def encode_image_to_base64(path: str) -> str:
    """
    Read a local image file and return a base64-encoded string (no data URI prefix).

    Parameters
    ----------
    path : str
        Absolute or relative path to the image file.

    Returns
    -------
    str
        Base64-encoded contents of the image file.
    """
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_flux_edit(
    prompt: str,
    input_image_b64: str,
    reference_images_b64: list[str] | None = None,
    width: int = 1024,
    height: int = 1024,
    safety_tolerance: int = 2,
) -> dict[str, Any]:
    """
    Call FLUX.2 [pro] image editing endpoint.

    Parameters
    ----------
    prompt : str
        Text prompt describing the edit to apply to the input image.
    input_image_b64 : str
        Base64-encoded main input image (no data URI prefix), used as 'input_image'.
    reference_images_b64 : list of str, optional
        Base64-encoded reference images. These will be attached as 'input_image_2',
        'input_image_3', ... (up to 7 references).
    width : int, optional
        Output width in pixels (multiple of 16). Default is 1024.
    height : int, optional
        Output height in pixels (multiple of 16). Default is 1024.
    safety_tolerance : int, optional
        Moderation level (0–6). Default is 2.

    Returns
    -------
    dict
        The JSON response from the FLUX.2 API for the initial request
        (containing at least 'id', 'polling_url', and possibly 'cost').

    Raises
    ------
    FluxGenerationError
        If the environment variable BFL_API_KEY is missing or the HTTP request fails.
    """
    if not BFL_API_KEY:
        raise FluxGenerationError("BFL_API_KEY environment variable is not set.")

    payload: dict[str, Any] = {
        "prompt": prompt,
        "input_image": input_image_b64,
        "width": width,
        "height": height,
        "safety_tolerance": safety_tolerance,
    }

    # FLUX.2 [pro]: up to 8 images total via API (1 base + up to 7 refs here).
    if reference_images_b64:
        for idx, ref_b64 in enumerate(reference_images_b64[:7], start=2):
            payload[f"input_image_{idx}"] = ref_b64

    logger.debug("Submitting FLUX edit request with prompt length %s", len(prompt))
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
            f"FLUX.2 edit request failed with status {response.status_code}: {response.text}"
        )

    return response.json()


def poll_flux_result(
    polling_url: str,
    request_id: str | None = None,
    timeout: float = 120.0,
    interval: float = 0.5,
) -> dict[str, Any]:
    """
    Poll the FLUX.2 polling_url until the result status is 'Ready' or an error.

    Parameters
    ----------
    polling_url : str
        URL returned by the FLUX.2 API to poll for the result.
    request_id : str, optional
        Request ID returned by the initial call. Some setups expect it as a query param.
    timeout : float, optional
        Maximum number of seconds to keep polling. Default is 120.
    interval : float, optional
        Delay (in seconds) between polling attempts. Default is 0.5.

    Returns
    -------
    dict
        Final JSON result containing at least:
        - 'status': 'Ready'
        - 'result': {'sample': '<output-image-url>'}

    Raises
    ------
    FluxGenerationError
        If the API reports an error status or polling times out.
    """
    if not BFL_API_KEY:
        raise FluxGenerationError("BFL_API_KEY environment variable is not set.")

    start = time.time()
    while True:
        params = {"id": request_id} if request_id else None
        result = requests.get(
            polling_url,
            headers={
                "accept": "application/json",
                "x-key": BFL_API_KEY,
            },
            params=params,
            timeout=60,
        ).json()

        status = result.get("status")

        if status == "Ready":
            return result
        if status in ("Failed", "Error"):
            raise FluxGenerationError(f"FLUX.2 job failed: {result}")

        if (time.time() - start) > timeout:
            raise FluxGenerationError("Polling timed out before result was ready.")

        time.sleep(interval)


def load_assets_from_folder(base_dir: str) -> dict[str, list[dict[str, Any]]]:
    """
    Scan a base directory and build the asset dictionary automatically.

    Expected directory structure:
    -----------------------------
    base_dir/
        jackets/
            jacket1.png
            jacket2.jpg
        pants/
            pants1.png
        models/
            model1.png
        ...

    Each subfolder name is treated as an asset class.

    Parameters
    ----------
    base_dir : str
        Path to the base assets directory.

    Returns
    -------
    dict
        A mapping: asset_class (str) -> list of asset dicts:
        {
            "jackets": [
                {
                    "id": "jacket1",
                    "name": "jacket1",
                    "file_path": "/abs/path/.../jacket1.png",
                },
                ...
            ],
            "pants": [...],
            ...
        }

    Raises
    ------
    ValueError
        If the directory does not exist or contains no supported image files.
    """
    base_path = Path(base_dir).expanduser()
    if not base_path.is_dir():
        raise ValueError(f"Assets base directory does not exist: {base_path}")

    assets: dict[str, list[dict[str, Any]]] = {}

    for sub in base_path.iterdir():
        if not sub.is_dir():
            continue

        asset_class = sub.name
        items: list[dict[str, Any]] = []

        for f in sub.iterdir():
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
                asset_id = f.stem
                name = f.stem.replace("_", " ").replace("-", " ")
                items.append(
                    {
                        "id": asset_id,
                        "name": name,
                        "file_path": str(f.resolve()),
                    }
                )

        if items:
            assets[asset_class] = items

    if not assets:
        raise ValueError(f"No image assets found under: {base_path}")

    return assets


def select_assets_for_image(
    assets: dict[str, list[dict[str, Any]]],
    used_ids_per_class: dict[str, set],
    allowed_ids_per_class: dict[str, set[str]] | None = None,
) -> dict[str, dict[str, Any]]:
    """
    For each asset class (e.g. 'jackets', 'pants', 'models'), choose one asset.

    Attempts to avoid re-using the same asset ID in each class until all have
    been used at least once.

    Parameters
    ----------
    assets : dict
        Mapping of asset_class -> list of asset dicts (as returned by load_assets_from_folder).
    used_ids_per_class : dict
        Mutable mapping of asset_class -> set of already-used asset IDs.
    allowed_ids_per_class : dict, optional
        Optional mapping of asset_class -> set of asset IDs to prioritize. If
        provided, selection attempts to pull from this subset first while still
        falling back to the broader class list when needed.

    Returns
    -------
    dict
        Mapping of asset_class -> chosen asset dict for this image.
    """
    selection: dict[str, dict[str, Any]] = {}

    for asset_class, items in assets.items():
        if not items:
            continue

        used_ids = used_ids_per_class.setdefault(asset_class, set())
        allowed_ids = None
        if allowed_ids_per_class:
            allowed_ids = allowed_ids_per_class.get(asset_class)

        available = [a for a in items if a.get("id") not in used_ids]
        if allowed_ids:
            filtered = [a for a in available if a.get("id") in allowed_ids]
            if filtered:
                available = filtered

        if not available:
            # Reset and allow reuse once all have been used
            used_ids.clear()
            available = list(items)

        chosen = random.choice(available)
        selection[asset_class] = chosen
        used_ids.add(chosen.get("id"))
        logger.debug("Selected %s asset '%s'", asset_class, chosen.get("id"))

    return selection


def choose_base_and_references(
    selected_assets: dict[str, dict[str, Any]]
) -> tuple[tuple[str, dict[str, Any]], list[tuple[str, dict[str, Any]]]]:
    """
    Decide which asset becomes the base input image vs. reference images.

    Heuristic:
    - If there is an asset class called 'models', use that as the base.
    - Otherwise, use the first asset in the selection as the base.

    Parameters
    ----------
    selected_assets : dict
        Mapping of asset_class -> chosen asset dict.

    Returns
    -------
    ( (str, dict), list[(str, dict)] )
        - Tuple of (base_class, base_asset)
        - List of (asset_class, asset) for reference images.
    """
    if "models" in selected_assets:
        base_class = "models"
        base_asset = selected_assets["models"]
    else:
        base_class, base_asset = next(iter(selected_assets.items()))

    references = [(cls, a) for cls, a in selected_assets.items() if cls != base_class]
    return (base_class, base_asset), references


def build_prompt(
    base_prompt: str,
    selected_assets: dict[str, dict[str, Any]],
    base_asset_class: str,
) -> str:
    """
    Build the final text prompt for FLUX.2 editing.

    Notes
    -----
    - Emphasises ultra realistic, high-res fashion photography.
    - Describes the base image and how to use reference images.
    - Does NOT contain the target group; that stays as metadata only.

    Parameters
    ----------
    base_prompt : str
        Base style/content prompt (e.g. "Professional studio fashion photography ...").
    selected_assets : dict
        Mapping of asset_class -> chosen asset dict.
    base_asset_class : str
        Asset class name chosen as the base input image.

    Returns
    -------
    str
        Full prompt string to send to FLUX.2.
    """
    base = base_prompt.strip()
    if not base.endswith("."):
        base += "."

    base_asset = selected_assets[base_asset_class]
    base_label = base_asset.get("name") or base_asset.get("id")

    ref_lines = []
    for cls, asset in selected_assets.items():
        if cls == base_asset_class:
            continue
        label = asset.get("name") or asset.get("id")
        ref_lines.append(f"{cls} = {label}")

    refs_text = ""
    if ref_lines:
        refs_text = (
            " Use the reference images to apply the following items accurately: "
            + ", ".join(ref_lines)
            + "."
        )

    detail = (
        " Edit the input image into an ultra realistic, high-resolution fashion photograph. "
        "Keep the base person's identity, body shape, and pose from the input image. "
        "Respect realistic lighting, shadows, and fabric textures. "
        f"The base image shows: {base_asset_class} = {base_label}."
    )

    return f"{base}{detail}{refs_text}"


class FluxBatchSession:
    """Stateful helper that keeps asset metadata and usage tracking."""

    def __init__(self, assets_base_dir: str):
        self.assets = load_assets_from_folder(assets_base_dir)
        self.used_ids_per_class: dict[str, set[str]] = {}

    def generate_images_for_group(
        self,
        base_prompt: str,
        target_group: str,
        num_images: int = 5,
        width: int = 1024,
        height: int = 1024,
        preferred_asset_ids: dict[str, set[str]] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Generate edited images for a single target group using FLUX.2.

        IMPORTANT: The target group is NOT injected into the prompt. It is kept
        only as metadata in the returned structures so the caller can leverage it.

        Parameters
        ----------
        base_prompt : str
            Base prompt text describing overall style/look of the output.
        target_group : str
            Logical group label (e.g. "Gen Z streetwear") stored as metadata only.
        num_images : int, optional
            Number of edited images to generate for this target group. Default is 5.
        width : int, optional
            Output width in pixels. Default is 1024.
        height : int, optional
            Output height in pixels. Default is 1024.

        Returns
        -------
        list
            List of image result dicts. Each dict has the following keys:
            - 'prompt': str, the exact prompt used
            - 'target_group': str, the group label (metadata only)
            - 'assets': dict, asset_class -> asset dict used for this image
            - 'base_class': str, which asset class was used as base input image
            - 'image_url': str or None, URL of the generated image
            - 'request_id': str, FLUX.2 request ID
            - 'cost': float or None, credits charged for the request (if available)

        Raises
        ------
        FluxGenerationError
            If any FLUX.2 call fails.
        """
        group_results: list[dict[str, Any]] = []

        logger.info(
            "Generating %s images for %s", num_images, target_group
        )

        for idx in range(num_images):
            selected_assets = select_assets_for_image(
                self.assets,
                self.used_ids_per_class,
                allowed_ids_per_class=preferred_asset_ids,
            )
            (base_class, base_asset), reference_assets = choose_base_and_references(
                selected_assets
            )

            base_b64 = encode_image_to_base64(base_asset["file_path"])
            refs_b64 = [
                encode_image_to_base64(a["file_path"]) for _, a in reference_assets
            ]

            prompt = build_prompt(
                base_prompt=base_prompt,
                selected_assets=selected_assets,
                base_asset_class=base_class,
            )

            initial = call_flux_edit(
                prompt=prompt,
                input_image_b64=base_b64,
                reference_images_b64=refs_b64,
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

            final = poll_flux_result(polling_url=polling_url, request_id=request_id)
            sample_url = final.get("result", {}).get("sample")

            group_results.append(
                {
                    "prompt": prompt,
                    "target_group": target_group,
                    "assets": selected_assets,
                    "base_class": base_class,
                    "image_url": sample_url,
                    "request_id": request_id,
                    "cost": cost,
                }
            )
            logger.info(
                "[%s] Generated image %s/%s (request %s)",
                target_group,
                idx + 1,
                num_images,
                request_id,
            )

        return group_results


def print_concise_summary(results: dict[str, list[dict[str, Any]]]) -> None:
    """
    Print a short, human-readable summary of generated images.

    Parameters
    ----------
    results : dict
        Mapping target_group -> list of image result dicts,
        as returned by FluxBatchSession.generate_images_for_group.
    """
    for target_group, images in results.items():
        print(f"\n=== Target group: {target_group} ===")
        for idx, img in enumerate(images, start=1):
            asset_summaries = []
            for cls, asset in img["assets"].items():
                label = asset.get("name") or asset.get("id")
                prefix = "BASE" if cls == img.get("base_class") else cls
                asset_summaries.append(f"{prefix}={label}")

            assets_str = "; ".join(asset_summaries)
            cost = img.get("cost")
            cost_str = f" | cost={cost}" if cost is not None else ""
            print(
                f"  [{idx}] URL={img['image_url']} | assets: {assets_str}{cost_str}"
            )


if __name__ == "__main__":
    # Example standalone usage / quick test.
    default_assets_dir = Path(__file__).resolve().parents[1].parent / "assets"
    assets_path = os.environ.get("ASSETS_BASE_DIR") or default_assets_dir

    if isinstance(assets_path, str):
        assets_path = str(Path(assets_path))

    ASSETS_BASE_DIR = assets_path

    base_prompt = (
        "Professional studio fashion photography, full body, neutral background, "
        "shot on a high-end DSLR camera. Use well-fitting pose, lighting and background."
    )

    target_groups = [
        "Gen Z streetwear enthusiasts",
        "Minimalist business professionals",
        "Outdoor techwear fans",
    ]

    try:
        session = FluxBatchSession(assets_base_dir=ASSETS_BASE_DIR)
        all_results: dict[str, list[dict[str, Any]]] = {}

        for group in target_groups:
            all_results[group] = session.generate_images_for_group(
                base_prompt=base_prompt,
                target_group=group,
                num_images=5,
                width=1024,
                height=1024,
            )

        print_concise_summary(all_results)
    except Exception as e:
        print(f"Error: {e}")
