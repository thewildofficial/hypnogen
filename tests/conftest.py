"""Shared fixtures for all tests."""
import pytest

from hypnogen.core import tts


@pytest.fixture(autouse=True)
def _clear_pipeline_cache():
    """Clear the KPipeline cache before each test to ensure isolation."""
    tts._pipeline_cache.clear()
