"""
Tests for evaluate_image_groups module.
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError, APIError, RateLimitError
from pydantic import BaseModel

# Add src to path for imports
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / 'src'
sys.path.insert(0, str(src_dir))

# Define test schemas that match the expected interface
class AnalyticsData(BaseModel):
    """Test AnalyticsData schema."""

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
    """Test ImageData schema."""

    id: str
    file_name: str
    metadata_tags: list[str] | None = None
    final_prompt: str | None = None
    analytics: AnalyticsData | None = None


# Create a mock schemas module and patch it before any imports
class MockSchemas:
    """Mock schemas module."""

    AnalyticsData = AnalyticsData
    ImageData = ImageData


# Patch the schemas module before importing anything that uses it
sys.modules['schemas'] = MockSchemas()
sys.modules['src.schemas'] = MockSchemas()


@pytest.fixture(autouse=True)
def setup_schemas():
    """Ensure schemas are patched before each test."""
    # Re-patch to ensure it's fresh
    sys.modules['schemas'] = MockSchemas()
    sys.modules['src.schemas'] = MockSchemas()
    yield
    # Cleanup if needed
    if 'schemas' in sys.modules:
        del sys.modules['schemas']
    if 'src.schemas' in sys.modules:
        del sys.modules['src.schemas']


@pytest.fixture
def sample_analytics_data():
    """Create sample AnalyticsData objects with varying performance."""
    return [
        AnalyticsData(
            id='image_1',
            impressions=20000,
            clicks=1200,
            ctr=0.06,
            interactions=1800,
            interaction_rate=0.09,
            conversions=300,
            conversion_rate=0.015,
            cost=300.0,
            avg_cpc=0.25,
            cpm=15.0,
            conversion_value=12000.0,
            value_per_conversion=40.0,
        ),
        AnalyticsData(
            id='image_2',
            impressions=18000,
            clicks=900,
            ctr=0.05,
            interactions=1300,
            interaction_rate=0.072,
            conversions=180,
            conversion_rate=0.01,
            cost=250.0,
            avg_cpc=0.28,
            cpm=13.9,
            conversion_value=7200.0,
            value_per_conversion=40.0,
        ),
        AnalyticsData(
            id='image_3',
            impressions=15000,
            clicks=600,
            ctr=0.04,
            interactions=800,
            interaction_rate=0.053,
            conversions=90,
            conversion_rate=0.006,
            cost=200.0,
            avg_cpc=0.33,
            cpm=13.3,
            conversion_value=3600.0,
            value_per_conversion=40.0,
        ),
        AnalyticsData(
            id='image_4',
            impressions=22000,
            clicks=1100,
            ctr=0.05,
            interactions=1500,
            interaction_rate=0.068,
            conversions=220,
            conversion_rate=0.01,
            cost=280.0,
            avg_cpc=0.25,
            cpm=12.7,
            conversion_value=8800.0,
            value_per_conversion=40.0,
        ),
    ]


@pytest.fixture
def sample_image_data(sample_analytics_data):
    """Create sample ImageData objects with analytics attached."""
    images = [
        ImageData(
            id='image_1',
            file_name='img1.jpg',
            metadata_tags=['warm colors', 'outdoor', 'lifestyle'],
            final_prompt='A person running in a park with modern running shoes',
            analytics=sample_analytics_data[0],
        ),
        ImageData(
            id='image_2',
            file_name='img2.jpg',
            metadata_tags=['cool colors', 'indoor', 'product focus'],
            final_prompt='Close-up of running shoes on a white background',
            analytics=sample_analytics_data[1],
        ),
        ImageData(
            id='image_3',
            file_name='img3.jpg',
            metadata_tags=['neutral colors', 'studio', 'minimalist'],
            final_prompt='Running shoes displayed in a minimalist studio setting',
            analytics=sample_analytics_data[2],
        ),
        ImageData(
            id='image_4',
            file_name='img4.jpg',
            metadata_tags=['warm colors', 'lifestyle', 'action'],
            final_prompt='Athlete in action wearing running shoes during a race',
            analytics=sample_analytics_data[3],
        ),
    ]
    return images


class TestAnalyzeImageDifferences:
    """Test suite for analyze_image_differences function."""

    def _get_function(self):
        """Helper to get the function, reloading if necessary."""
        import importlib
        # Clear any cached imports
        modules_to_clear = [
            'steps.evaluate_image_groups',
            'steps.select_top_images',
            'schemas',
            'src.schemas',
        ]
        for mod_name in modules_to_clear:
            if mod_name in sys.modules:
                del sys.modules[mod_name]
        
        # Re-patch schemas
        sys.modules['schemas'] = MockSchemas()
        sys.modules['src.schemas'] = MockSchemas()
        
        from steps.evaluate_image_groups import analyze_image_differences
        return analyze_image_differences

    def test_with_image_data_input(self, sample_image_data):
        """Test function with ImageData input."""
        # Mock OpenAI client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        'differentiation_text': 'Top images have higher CTR and conversion rates.',
                        'differentiation_tags': ['warm colors', 'lifestyle', 'high engagement'],
                    })
                )
            )
        ]

        with patch('steps.evaluate_image_groups.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            analyze_image_differences = self._get_function()
            result = analyze_image_differences(sample_image_data, top_n=2)

            assert 'differentiation_text' in result
            assert 'differentiation_tags' in result
            assert 'top_image_ids' in result
            assert 'bottom_image_ids' in result
            assert len(result['top_image_ids']) == 2
            assert len(result['bottom_image_ids']) == 2
            assert isinstance(result['differentiation_tags'], list)

    def test_with_analytics_data_input(self, sample_analytics_data):
        """Test function with AnalyticsData input."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        'differentiation_text': 'Analysis of top performers.',
                        'differentiation_tags': ['high ctr', 'good conversion'],
                    })
                )
            )
        ]

        with patch('steps.evaluate_image_groups.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            analyze_image_differences = self._get_function()
            result = analyze_image_differences(sample_analytics_data, top_n=2)

            assert 'differentiation_text' in result
            assert 'differentiation_tags' in result
            assert 'top_image_ids' in result
            assert 'bottom_image_ids' in result

    def test_fallback_when_no_api_key(self, sample_image_data):
        """Test fallback behavior when OPENAI_API_KEY is not set."""
        # Remove API key if it exists
        original_key = os.environ.pop('OPENAI_API_KEY', None)

        try:
            analyze_image_differences = self._get_function()
            result = analyze_image_differences(sample_image_data, top_n=2)

            assert 'differentiation_text' in result
            assert 'differentiation_tags' in result
            assert 'top_image_ids' in result
            assert 'bottom_image_ids' in result
            assert 'analysis_unavailable' in result['differentiation_tags']
            assert 'unavailable' in result['differentiation_text'].lower()
        finally:
            # Restore API key if it existed
            if original_key:
                os.environ['OPENAI_API_KEY'] = original_key

    def test_fallback_on_rate_limit_error(self, sample_image_data):
        """Test fallback behavior on RateLimitError."""
        with patch('steps.evaluate_image_groups.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = RateLimitError(
                'Rate limit exceeded', response=None, body=None
            )
            mock_openai.return_value = mock_client

            analyze_image_differences = self._get_function()
            result = analyze_image_differences(sample_image_data, top_n=2)

            assert 'differentiation_text' in result
            assert 'differentiation_tags' in result
            assert 'analysis_unavailable' in result['differentiation_tags']

    def test_fallback_on_api_connection_error(self, sample_image_data):
        """Test fallback behavior on APIConnectionError."""
        with patch('steps.evaluate_image_groups.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = APIConnectionError(
                'Connection failed', request=None
            )
            mock_openai.return_value = mock_client

            analyze_image_differences = self._get_function()
            result = analyze_image_differences(sample_image_data, top_n=2)

            assert 'differentiation_text' in result
            assert 'differentiation_tags' in result
            assert 'analysis_unavailable' in result['differentiation_tags']

    def test_fallback_on_generic_api_error(self, sample_image_data):
        """Test fallback behavior on generic APIError."""
        with patch('steps.evaluate_image_groups.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = APIError(
                status_code=500, message='Internal server error', request=None
            )
            mock_openai.return_value = mock_client

            analyze_image_differences = self._get_function()
            result = analyze_image_differences(sample_image_data, top_n=2)

            assert 'differentiation_text' in result
            assert 'differentiation_tags' in result
            assert 'analysis_unavailable' in result['differentiation_tags']

    def test_fallback_on_json_decode_error(self, sample_image_data):
        """Test fallback behavior when OpenAI returns invalid JSON."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='Invalid JSON response'))
        ]

        with patch('steps.evaluate_image_groups.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            analyze_image_differences = self._get_function()
            result = analyze_image_differences(sample_image_data, top_n=2)

            assert 'differentiation_text' in result
            assert 'differentiation_tags' in result
            assert 'analysis_unavailable' in result['differentiation_tags']

    def test_insufficient_images_error(self, sample_image_data):
        """Test error when not enough images are provided."""
        analyze_image_differences = self._get_function()

        # Only provide 2 images but request top_n=2 (need at least 3)
        with pytest.raises(ValueError, match='Not enough images to compare'):
            analyze_image_differences(sample_image_data[:2], top_n=2)

    def test_image_data_without_analytics_error(self):
        """Test error when ImageData has no analytics."""
        analyze_image_differences = self._get_function()

        images_without_analytics = [
            ImageData(
                id='image_1',
                file_name='img1.jpg',
                metadata_tags=['tag1'],
                final_prompt='prompt1',
                analytics=None,
            ),
        ]

        with pytest.raises(ValueError, match='has no analytics data'):
            analyze_image_differences(images_without_analytics, top_n=1)

    def test_unsupported_type_error(self):
        """Test error when unsupported type is provided."""
        analyze_image_differences = self._get_function()

        with pytest.raises(TypeError, match='Unsupported type'):
            analyze_image_differences([{'id': 'test'}], top_n=1)

    def test_custom_model_parameter(self, sample_image_data):
        """Test function with custom model parameter."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        'differentiation_text': 'Custom model analysis.',
                        'differentiation_tags': ['tag1'],
                    })
                )
            )
        ]

        with patch('steps.evaluate_image_groups.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            analyze_image_differences = self._get_function()
            result = analyze_image_differences(
                sample_image_data, top_n=2, model='gpt-4'
            )

            # Verify the model was used
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]['model'] == 'gpt-4'

            assert 'differentiation_text' in result
            assert 'differentiation_tags' in result

    def test_custom_top_n_parameter(self, sample_image_data):
        """Test function with custom top_n parameter."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        'differentiation_text': 'Analysis with top 3.',
                        'differentiation_tags': ['tag1', 'tag2'],
                    })
                )
            )
        ]

        with patch('steps.evaluate_image_groups.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            analyze_image_differences = self._get_function()
            result = analyze_image_differences(sample_image_data, top_n=1)

            assert len(result['top_image_ids']) == 1
            assert len(result['bottom_image_ids']) == 3

    def test_result_structure(self, sample_image_data):
        """Test that result has all expected keys with correct types."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        'differentiation_text': 'Test analysis text.',
                        'differentiation_tags': ['tag1', 'tag2', 'tag3'],
                    })
                )
            )
        ]

        with patch('steps.evaluate_image_groups.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            analyze_image_differences = self._get_function()
            result = analyze_image_differences(sample_image_data, top_n=2)

            # Check all required keys exist
            assert 'differentiation_text' in result
            assert 'differentiation_tags' in result
            assert 'top_image_ids' in result
            assert 'bottom_image_ids' in result

            # Check types
            assert isinstance(result['differentiation_text'], str)
            assert isinstance(result['differentiation_tags'], list)
            assert isinstance(result['top_image_ids'], list)
            assert isinstance(result['bottom_image_ids'], list)

            # Check that all IDs are strings
            assert all(isinstance(id, str) for id in result['top_image_ids'])
            assert all(isinstance(id, str) for id in result['bottom_image_ids'])

            # Check that top and bottom IDs don't overlap
            assert not set(result['top_image_ids']).intersection(
                set(result['bottom_image_ids'])
            )
