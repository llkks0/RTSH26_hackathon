"""
Prompt generation and modification utilities.

Functions for generating and refining prompts for image generation.
All functions are async for non-blocking operation where API calls are made.
"""

import json
import os
import sys

from openai import (
    APIConnectionError,
    APIError,
    AsyncOpenAI,
    RateLimitError,
)

from models import Asset, AssetType

from .types import (
    AssetSet,
    PromptGenerationInput,
    PromptGenerationOutput,
    PromptModificationInput,
    PromptModificationOutput,
)

DEFAULT_MODEL = 'gpt-4o-mini'


def generate_initial_prompt(input_data: PromptGenerationInput) -> PromptGenerationOutput:
    """
    Generate the initial prompt for FLUX.2 image editing.

    Takes the base prompt and asset set, and constructs a detailed prompt
    that describes how to edit the base image using reference assets.

    Args:
        input_data: PromptGenerationInput with base prompt and asset set

    Returns:
        PromptGenerationOutput with the constructed prompt and asset references
    """
    base_prompt = input_data.base_prompt.strip()
    if not base_prompt.endswith('.'):
        base_prompt += '.'

    # Get base asset (preferably MODEL type)
    base_asset = input_data.asset_set.assets.get(input_data.base_asset_type)
    reference_assets: list[Asset] = []

    if base_asset is None:
        # Fallback to first asset type
        first_type = next(iter(input_data.asset_set.assets))
        base_asset = input_data.asset_set.assets[first_type]
        reference_assets = [
            asset for asset_type, asset in input_data.asset_set.assets.items()
            if asset_type != first_type
        ]
    else:
        reference_assets = [
            asset for asset_type, asset in input_data.asset_set.assets.items()
            if asset_type != input_data.base_asset_type
        ]

    # Build asset labels for prompt
    base_label = base_asset.name or str(base_asset.id)[:8]

    ref_lines = []
    for asset in reference_assets:
        label = asset.name or str(asset.id)[:8]
        ref_lines.append(f"{asset.asset_type.value} = {label}")

    refs_text = ""
    if ref_lines:
        refs_text = (
                " Use the reference images to apply the following items accurately: "
                + ", ".join(ref_lines)
                + "."
        )

    detail = (
        "Edit the input image into an instagram post for a fashion brand. "
        "It should be based on a ultra realistic photograph with a logo. "
        "Keep the base person's identity and body shape from the input image but play with pose and direction. "
        "Respect realistic lighting, shadows, and fabric textures. "
        f"The base image shows: {input_data.base_asset_type.value} = {base_label}."
    )

    full_prompt = f"{base_prompt}{detail}{refs_text}"

    return PromptGenerationOutput(
        prompt=full_prompt,
        base_asset=base_asset,
        reference_assets=reference_assets,
    )


async def modify_prompt_from_analysis(
        input_data: PromptModificationInput,
) -> PromptModificationOutput:
    """
    Modify a prompt based on analysis of winning images.

    Uses OpenAI to understand what made winning images successful and
    adjusts the prompt to incorporate those success factors.

    Args:
        input_data: PromptModificationInput with current prompt and analysis data

    Returns:
        PromptModificationOutput with the modified prompt and reasoning
    """
    if 'OPENAI_API_KEY' not in os.environ:
        print(
            '[warn] OPENAI_API_KEY not set, returning original prompt.',
            file=sys.stderr,
        )
        return PromptModificationOutput(
            modified_prompt=input_data.current_prompt,
            modification_notes="No modification (OpenAI unavailable)",
            model_used=input_data.model,
        )

    client = AsyncOpenAI()

    # Build target group context
    target_parts = [f"Target Group: {input_data.target_group.name}"]
    if input_data.target_group.city:
        target_parts.append(f"Location: {input_data.target_group.city}")
    if input_data.target_group.age_group:
        target_parts.append(f"Age Group: {input_data.target_group.age_group}")
    if input_data.target_group.economic_status:
        target_parts.append(f"Economic Status: {input_data.target_group.economic_status}")
    if input_data.target_group.description:
        target_parts.append(f"Description: {input_data.target_group.description}")
    target_context = "\n".join(target_parts)

    system_prompt = """You are an expert in advertising creative optimization.
Your task is to improve image generation prompts based on performance data.

Given:
1. The current prompt used for image generation
2. Descriptions of top-performing images
3. Descriptions of lower-performing images
4. Analysis of what visual elements made winners successful
5. The target audience profile

You will create an improved prompt that:
- Incorporates the successful visual elements
- Better resonates with the target audience
- Maintains the core intent of the original prompt
- Is specific and actionable for image generation

Respond with valid JSON only."""

    user_prompt = f"""Improve this image generation prompt based on performance analysis.

CURRENT PROMPT:
{input_data.current_prompt}

TARGET AUDIENCE:
{target_context}

TOP-PERFORMING IMAGE DESCRIPTIONS:
{chr(10).join(f"- {desc}" for desc in input_data.winning_image_descriptions)}

LOWER-PERFORMING IMAGE DESCRIPTIONS:
{chr(10).join(f"- {desc}" for desc in input_data.losing_image_descriptions)}

VISUAL SIMILARITIES IN WINNING IMAGES:
{input_data.visual_similarities}

Create an improved prompt that incorporates the success factors while maintaining the core intent.

Return a JSON object with this structure:
{{
    "modified_prompt": "<the improved prompt>",
    "modification_notes": "<explanation of what changes were made and why>"
}}"""

    try:
        response = await client.chat.completions.create(
            model=input_data.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            response_format={'type': 'json_object'},
            temperature=0.7,
            max_tokens=1000,
        )

        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)

        return PromptModificationOutput(
            modified_prompt=result.get('modified_prompt', input_data.current_prompt),
            modification_notes=result.get('modification_notes', ''),
            model_used=input_data.model,
        )

    except (RateLimitError, APIConnectionError, APIError) as e:
        print(
            f'[warn] OpenAI API error ({type(e).__name__}): {e}. Returning original.',
            file=sys.stderr,
        )
        return PromptModificationOutput(
            modified_prompt=input_data.current_prompt,
            modification_notes=f"No modification (API error: {type(e).__name__})",
            model_used=input_data.model,
        )

    except (json.JSONDecodeError, KeyError) as e:
        print(
            f'[warn] Failed to parse prompt modification response: {e}.',
            file=sys.stderr,
        )
        return PromptModificationOutput(
            modified_prompt=input_data.current_prompt,
            modification_notes="No modification (parse error)",
            model_used=input_data.model,
        )

    except Exception as e:
        print(
            f'[warn] Unexpected error modifying prompt: {e}.',
            file=sys.stderr,
        )
        return PromptModificationOutput(
            modified_prompt=input_data.current_prompt,
            modification_notes=f"No modification (error: {e})",
            model_used=input_data.model,
        )


def build_flux_prompt(
        base_prompt: str,
        asset_set: AssetSet,
        base_asset_type: AssetType = AssetType.MODEL,
) -> str:
    """
    Convenience function to build a FLUX.2 prompt from a base prompt and assets.

    Args:
        base_prompt: The base style/content prompt
        asset_set: Set of assets to use
        base_asset_type: Which asset type to use as base

    Returns:
        The constructed prompt string
    """
    input_data = PromptGenerationInput(
        base_prompt=base_prompt,
        asset_set=asset_set,
        base_asset_type=base_asset_type,
    )
    output = generate_initial_prompt(input_data)
    return output.prompt
