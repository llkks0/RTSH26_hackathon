"""
Image generation utilities using FLUX.2 API.

Wrapper functions for generating images via the FLUX.2 Pro API.
All functions are async for non-blocking operation.
"""

import asyncio
import base64
import os
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from models import Asset


# FLUX.2 API Configuration
BFL_API_KEY = os.environ.get("BFL_API_KEY")
FLUX_ENDPOINT = "https://api.bfl.ai/v1/flux-2-pro"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"}

# Directory for saving generated images
GENERATED_IMAGES_DIR = Path("generated-images")

# Directory where asset files are stored
ASSET_FILES_DIR = Path(__file__).parent.parent.parent / "asset-files"


async def _download_and_save_image(url: str, request_id: str | None = None) -> str | None:
    """
    Download an image from URL and save it locally.

    Args:
        url: The URL to download from
        request_id: Optional request ID to use in filename

    Returns:
        Local file path if successful, None otherwise
    """
    try:
        # Ensure directory exists
        GENERATED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

        # Download image
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=60.0)
            response.raise_for_status()

            # Determine file extension from content-type or URL
            content_type = response.headers.get("content-type", "")
            if "jpeg" in content_type or "jpg" in content_type:
                ext = ".jpg"
            elif "png" in content_type:
                ext = ".png"
            elif "webp" in content_type:
                ext = ".webp"
            else:
                # Try to get from URL
                ext = ".jpg"  # Default to jpg

            # Generate filename
            file_id = request_id or str(uuid.uuid4())
            filename = f"{file_id}{ext}"
            file_path = GENERATED_IMAGES_DIR / filename

            # Save image
            with open(file_path, "wb") as f:
                f.write(response.content)

            return str(file_path)

    except Exception as e:
        print(f"[warn] Failed to download and save image: {e}", file=sys.stderr)
        return None


class FluxGenerationError(Exception):
    """Custom exception raised when FLUX.2 image generation fails."""
    pass


@dataclass
class ImageGenerationResult:
    """Result of an image generation request."""

    success: bool
    image_url: str | None = None
    request_id: str | None = None
    cost: float | None = None
    error: str | None = None
    metadata_tags: list[str] = field(default_factory=list)
    model_version: str = "flux-2-pro"


def _encode_image_to_base64(path: str) -> str:
    """Read a local image file and return base64-encoded string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


async def _encode_asset_to_base64(asset: Asset) -> str | None:
    """
    Encode an asset's image to base64.

    Supports both local file paths and URLs.
    """
    file_name = asset.file_name

    if file_name.startswith('http://') or file_name.startswith('https://'):
        # Download image from URL
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(file_name, timeout=30.0)
                response.raise_for_status()
                return base64.b64encode(response.content).decode("utf-8")
        except Exception as e:
            print(f"[warn] Failed to download asset image: {e}", file=sys.stderr)
            return None
    else:
        # Local file - check in asset-files directory first
        path = ASSET_FILES_DIR / file_name
        if not path.exists():
            # Fallback to treating file_name as absolute/relative path
            path = Path(file_name)
        if not path.exists():
            print(f"[warn] Asset file not found: {file_name} (checked {ASSET_FILES_DIR})", file=sys.stderr)
            return None
        return _encode_image_to_base64(str(path))


async def _call_flux_edit(
    prompt: str,
    input_image_b64: str,
    reference_images_b64: list[str] | None = None,
    width: int = 1024,
    height: int = 1024,
    safety_tolerance: int = 2,
) -> dict:
    """
    Call FLUX.2 [pro] image editing endpoint.

    Args:
        prompt: Text prompt describing the edit
        input_image_b64: Base64-encoded main input image
        reference_images_b64: Optional list of base64-encoded reference images
        width: Output width in pixels
        height: Output height in pixels
        safety_tolerance: Moderation level (0-6)

    Returns:
        JSON response from the FLUX.2 API

    Raises:
        FluxGenerationError: If API call fails
    """
    api_key = os.environ.get("BFL_API_KEY")
    if not api_key:
        raise FluxGenerationError("BFL_API_KEY environment variable is not set.")

    payload = {
        "prompt": prompt,
        "input_image": input_image_b64,
        "width": width,
        "height": height,
        "safety_tolerance": safety_tolerance,
    }

    # Add reference images (up to 7)
    if reference_images_b64:
        for idx, ref_b64 in enumerate(reference_images_b64[:7], start=2):
            payload[f"input_image_{idx}"] = ref_b64

    async with httpx.AsyncClient() as client:
        response = await client.post(
            FLUX_ENDPOINT,
            headers={
                "accept": "application/json",
                "x-key": api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60.0,
        )

        if not response.is_success:
            raise FluxGenerationError(
                f"FLUX.2 edit request failed with status {response.status_code}: {response.text}"
            )

        return response.json()


async def _poll_flux_result(
    polling_url: str,
    request_id: str | None = None,
    timeout: float = 120.0,
    interval: float = 2,
) -> dict:
    """
    Poll the FLUX.2 polling_url until the result is ready.

    Args:
        polling_url: URL to poll for results
        request_id: Optional request ID
        timeout: Maximum seconds to poll
        interval: Delay between polls

    Returns:
        Final JSON result with image URL

    Raises:
        FluxGenerationError: If polling fails or times out
    """
    api_key = os.environ.get("BFL_API_KEY")
    if not api_key:
        raise FluxGenerationError("BFL_API_KEY environment variable is not set.")

    start = asyncio.get_event_loop().time()
    async with httpx.AsyncClient() as client:
        while True:
            params = {"id": request_id} if request_id else None
            response = await client.get(
                polling_url,
                headers={
                    "accept": "application/json",
                    "x-key": api_key,
                },
                params=params,
                timeout=60.0,
            )
            result = response.json()

            status = result.get("status")

            if status == "Ready":
                return result
            if status in ("Failed", "Error"):
                raise FluxGenerationError(f"FLUX.2 job failed: {result}")

            if (asyncio.get_event_loop().time() - start) > timeout:
                raise FluxGenerationError("Polling timed out before result was ready.")

            await asyncio.sleep(interval)


async def generate_image_with_flux(
    prompt: str,
    base_asset: Asset,
    reference_assets: list[Asset] | None = None,
    width: int = 1024,
    height: int = 1024,
) -> ImageGenerationResult:
    """
    Generate an image using FLUX.2 API.

    Args:
        prompt: The prompt for image generation
        base_asset: The base/input asset (typically a model)
        reference_assets: Optional list of reference assets
        width: Output image width
        height: Output image height

    Returns:
        ImageGenerationResult with success status and image URL
    """
    # Check for API key
    if not os.environ.get("BFL_API_KEY"):
        print("[warn] BFL_API_KEY not set, skipping FLUX generation.", file=sys.stderr)
        return ImageGenerationResult(
            success=False,
            error="BFL_API_KEY not set",
        )

    # Encode base asset
    base_b64 = await _encode_asset_to_base64(base_asset)
    if not base_b64:
        return ImageGenerationResult(
            success=False,
            error=f"Failed to encode base asset: {base_asset.file_name}",
        )

    # Encode reference assets concurrently
    refs_b64: list[str] = []
    if reference_assets:
        encode_tasks = [_encode_asset_to_base64(ref_asset) for ref_asset in reference_assets]
        encoded_refs = await asyncio.gather(*encode_tasks)
        refs_b64 = [ref for ref in encoded_refs if ref is not None]

    try:
        # Call FLUX.2 API
        initial = await _call_flux_edit(
            prompt=prompt,
            input_image_b64=base_b64,
            reference_images_b64=refs_b64 if refs_b64 else None,
            width=width,
            height=height,
        )

        polling_url = initial.get("polling_url")
        request_id = initial.get("id")
        cost = initial.get("cost")

        if not polling_url:
            return ImageGenerationResult(
                success=False,
                request_id=request_id,
                error="No polling_url in FLUX.2 response",
            )

        # Poll for result
        final = await _poll_flux_result(polling_url=polling_url, request_id=request_id)
        sample_url = final.get("result", {}).get("sample")

        # Download and save image locally
        local_path = await _download_and_save_image(sample_url, request_id)
        if not local_path:
            return ImageGenerationResult(
                success=False,
                request_id=request_id,
                error=f"Failed to download image from {sample_url}",
            )

        # Build metadata tags
        metadata_tags = [
            f"base_asset:{base_asset.id}",
            f"base_type:{base_asset.asset_type.value}",
            f"original_url:{sample_url}",
        ]
        if reference_assets:
            for ref in reference_assets:
                metadata_tags.append(f"ref_asset:{ref.id}")
                metadata_tags.append(f"ref_type:{ref.asset_type.value}")

        return ImageGenerationResult(
            success=True,
            image_url=local_path,  # Return local path instead of remote URL
            request_id=request_id,
            cost=cost,
            metadata_tags=metadata_tags,
            model_version="flux-2-pro",
        )

    except FluxGenerationError as e:
        return ImageGenerationResult(
            success=False,
            error=str(e),
        )
    except Exception as e:
        return ImageGenerationResult(
            success=False,
            error=f"Unexpected error: {e}",
        )


async def generate_images_batch(
    prompts_and_assets: list[tuple[str, Asset, list[Asset]]],
    width: int = 1024,
    height: int = 1024,
) -> list[ImageGenerationResult]:
    """
    Generate multiple images concurrently.

    Args:
        prompts_and_assets: List of (prompt, base_asset, reference_assets) tuples
        width: Output image width
        height: Output image height

    Returns:
        List of ImageGenerationResult for each request
    """
    tasks = [
        generate_image_with_flux(
            prompt=prompt,
            base_asset=base_asset,
            reference_assets=reference_assets,
            width=width,
            height=height,
        )
        for prompt, base_asset, reference_assets in prompts_and_assets
    ]

    return await asyncio.gather(*tasks)